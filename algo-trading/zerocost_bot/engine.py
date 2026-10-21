"""Deterministic long-only paper trader. No broker order placement here."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from collections import deque
from typing import Optional
import json


@dataclass(frozen=True)
class Bar:
    symbol: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    def validate(self):
        if self.time.tzinfo is None:
            raise ValueError("bar timestamp must have timezone")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("bar price must be positive")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("invalid OHLC")
        if self.volume < 0:
            raise ValueError("negative volume")


@dataclass
class Settings:
    start_cash: float = 1000.0
    max_position_fraction: float = 0.20
    max_daily_loss_fraction: float = 0.03
    stop_loss_fraction: float = 0.02
    take_profit_fraction: float = 0.035
    max_round_trips_per_day: int = 3
    cooldown_bars: int = 10
    lookback: int = 12
    breakout_fraction: float = 0.0005
    min_volume: int = 5000
    min_history_bars: int = 13
    slippage_bps: float = 5.0
    fee_per_order: float = 0.0
    minimum_cash_buffer: float = 1.00

    def validate(self):
        if self.start_cash <= 0 or not 0 < self.max_position_fraction <= 1:
            raise ValueError("invalid allocation")
        if not 0 < self.max_daily_loss_fraction < 1:
            raise ValueError("invalid daily loss cap")
        if not 0 < self.stop_loss_fraction < 1 or not 0 < self.take_profit_fraction < 1:
            raise ValueError("invalid exits")
        if self.max_round_trips_per_day < 1 or self.cooldown_bars < 0:
            raise ValueError("invalid rate controls")
        if self.lookback < 2 or self.min_history_bars < self.lookback + 1:
            raise ValueError("invalid lookback")
        if self.slippage_bps < 0 or self.fee_per_order < 0:
            raise ValueError("invalid costs")


@dataclass
class Position:
    symbol: str
    qty: int
    entry_price: float
    entry_time: datetime
    stop: float
    target: float


class PaperEngine:
    """Next-bar-open entries; stop fills at worse of stop or gap-open.
    Decisions use *prior completed bars* only, avoiding same-bar lookahead.
    """
    def __init__(self, settings: Settings):
        settings.validate()
        self.s = settings
        self.cash = round(settings.start_cash, 2)
        self.bars = {}
        self.positions = {}
        self.pending = set()
        self.cooldowns = {}
        self.closed_today = 0
        self.entries_today = 0
        self.day = None
        self.daily_start_equity = settings.start_cash
        self.halted = False
        self.events = []

    @property
    def equity(self):
        return self.cash + sum(p.qty * self.bars[p.symbol][-1].close for p in self.positions.values())

    def _event(self, action, bar, **extra):
        row = {"action": action, "symbol": bar.symbol, "time": bar.time.isoformat(), **extra}
        self.events.append(row)
        return row

    def _reset_day(self, day, bar):
        if self.day != day:
            # Never carry positions across day boundary in simulation.
            for symbol in list(self.positions):
                last_bar = self.bars[symbol][-1]
                self._sell(self.positions[symbol], last_bar.close, last_bar, "session_boundary")
            self.day = day
            self.closed_today = 0
            self.entries_today = 0
            self.halted = False
            self.daily_start_equity = self.equity
            self.pending.clear()
            self.cooldowns.clear()

    def _buy(self, bar):
        alloc = min(self.cash - self.s.minimum_cash_buffer,
                    self.equity * self.s.max_position_fraction)
        price = bar.open * (1 + self.s.slippage_bps / 10000)
        qty = int((alloc - self.s.fee_per_order) // price)
        if qty < 1:
            return
        cost = round(qty * price + self.s.fee_per_order, 2)
        if cost > self.cash:
            return
        self.cash = round(self.cash - cost, 2)
        self.entries_today += 1
        self.positions[bar.symbol] = Position(bar.symbol, qty, price, bar.time,
                                              price * (1 - self.s.stop_loss_fraction),
                                              price * (1 + self.s.take_profit_fraction))
        self._event("buy", bar, qty=qty, price=round(price, 4), cost=cost)

    def _sell(self, p, reference_price, bar, reason):
        price = reference_price * (1 - self.s.slippage_bps / 10000)
        proceeds = round(p.qty * price - self.s.fee_per_order, 2)
        self.cash = round(self.cash + proceeds, 2)
        gain = round(proceeds - p.qty * p.entry_price - self.s.fee_per_order, 2)
        del self.positions[p.symbol]
        self.closed_today += 1
        self.cooldowns[p.symbol] = self.s.cooldown_bars
        self._event("sell", bar, qty=p.qty, price=round(price, 4), reason=reason, pnl=gain)

    def _signal(self, symbol, bar):
        past = self.bars[symbol]
        if len(past) < self.s.min_history_bars or bar.volume < self.s.min_volume:
            return False
        previous = list(past)[-self.s.lookback:]
        max_high = max(x.high for x in previous)
        avg_vol = sum(x.volume for x in previous) / len(previous)
        # previous completed-bar maximum; today's incoming bar is NOT part of prior window
        return (bar.close > max_high * (1 + self.s.breakout_fraction)
                and bar.volume > avg_vol * 1.2)

    def on_bar(self, bar: Bar):
        bar.validate()
        s = bar.symbol.upper()
        if not s or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ." for c in s):
            raise ValueError("invalid symbol")
        bar = Bar(s, bar.time, bar.open, bar.high, bar.low, bar.close, bar.volume)
        past = self.bars.setdefault(s, deque(maxlen=256))
        if past and bar.time <= past[-1].time:
            # Never double-execute if a feed reconnects and replays a bar.
            return []
        self._reset_day(bar.time.astimezone(timezone.utc).date(), bar)
        events_start = len(self.events)

        if self.cooldowns.get(s, 0):
            self.cooldowns[s] -= 1

        if s in self.positions:
            p = self.positions[s]
            # Conservative if both stop and target touched: assume stop first.
            if bar.open <= p.stop:
                self._sell(p, bar.open, bar, "gap_stop")
            elif bar.low <= p.stop:
                self._sell(p, p.stop, bar, "stop")
            elif bar.open >= p.target:
                self._sell(p, p.target, bar, "gap_target")
            elif bar.high >= p.target:
                self._sell(p, p.target, bar, "target")

        if (s in self.pending and not self.halted
                and s not in self.positions and self.entries_today < self.s.max_round_trips_per_day
                and not self.cooldowns.get(s, 0)):
            self._buy(bar)
        self.pending.discard(s)

        # Evaluate the current completed bar against history EXCLUDING itself.
        # Then append it for future decisions and mark-to-market.
        breakout = self._signal(s, bar)
        past.append(bar)
        if self.equity <= self.daily_start_equity * (1 - self.s.max_daily_loss_fraction):
            self.halted = True
            self.pending.clear()
            # Liquidate risk; no fresh entries after daily loss is reached.
            for p in list(self.positions.values()):
                if p.symbol == s:
                    self._sell(p, bar.close, bar, "daily_loss_halt")
            self._event("halt", bar, reason="daily_loss_limit")

        if (not self.halted and s not in self.positions
                and not self.cooldowns.get(s, 0)
                and self.entries_today < self.s.max_round_trips_per_day
                and breakout):
            self.pending.add(s)
            self._event("signal", bar, reason="volume_breakout")
        return self.events[events_start:]

    def finalize(self):
        """Exit open positions at last close; for deterministic replay only."""
        for s in list(self.positions):
            bar = self.bars[s][-1]
            self._sell(self.positions[s], bar.close, bar, "replay_end")
        return self.events

    def summary(self):
        sales = [x for x in self.events if x["action"] == "sell"]
        wins = sum(x["pnl"] > 0 for x in sales)
        return {"start_cash": self.s.start_cash, "end_cash": self.cash,
                "return_pct": round(100 * (self.cash / self.s.start_cash - 1), 2),
                "round_trips": len(sales), "win_rate_pct": round(100 * wins / len(sales), 2) if sales else None,
                "net_pnl": round(self.cash - self.s.start_cash, 2),
                "halted": self.halted}
