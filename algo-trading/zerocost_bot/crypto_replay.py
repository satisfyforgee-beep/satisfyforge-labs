"""Deterministic offline multi-crypto trading replay against *completed* Kraken OHLC.

NO brokerage/orders, no synthetic candle fabrication, no credential access,
and no assumption that OHLC highs/lows reveal actual order-book fills.
The final in-progress Kraken candle is discarded. All selected strategies are
fixed before seeing the holdout results; no optimizer fits on the holdout.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
import re

CENT = Decimal("0.01")
SLOT = Decimal("0.00000001")
CAP = Decimal("30.00")
START = Decimal("150.00")
# Conservative hypothetical expense model. Not a broker fee quote.
TAKER = Decimal("0.004")
SLIPPAGE = Decimal("0.0005")
STOP = Decimal("0.02")
TARGET = Decimal("0.035")
MAX_HOLD_BARS = 16
MAX_CONCURRENT = 3
MAX_PER_DAY = 10
VALID_PAIRS = {"BTC/USD": "XBTUSD", "ETH/USD": "ETHUSD", "SOL/USD": "SOLUSD"}
STRATEGIES = ("control", "breakout", "reversal")


@dataclass(frozen=True)
class Candle:
    at: int
    op: Decimal
    hi: Decimal
    lo: Decimal
    cl: Decimal
    volume: Decimal

    def validate(self):
        if type(self.at) is not int or self.at < 1:
            raise ValueError("invalid candle time")
        if any(not isinstance(x, Decimal) or not x.is_finite() or x <= 0
               for x in (self.op, self.hi, self.lo, self.cl)):
            raise ValueError("invalid candle price")
        if self.volume < 0 or not self.volume.is_finite():
            raise ValueError("invalid candle volume")
        if self.lo > min(self.op, self.cl) or self.hi < max(self.op, self.cl):
            raise ValueError("impossible OHLC bar")


def fetch_kraken_ohlc(pair: str, *, opener=urlopen, now=None):
    """The final OHLC bar is always the forming bar: exclude it."""
    if pair not in VALID_PAIRS:
        raise ValueError("only supported spot USD pairs may be downloaded")
    url = "https://api.kraken.com/0/public/OHLC?" + urlencode({
        "pair": VALID_PAIRS[pair], "interval": 15,
    })
    req = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "SatisfyForge-readonly-ohlc-virtual/1.0",
    }, method="GET")
    with opener(req, timeout=9) as response:
        data = json.load(response)
    if not isinstance(data, dict) or data.get("error") != []:
        raise ValueError("Kraken returned error")
    result = data.get("result")
    if not isinstance(result, dict) or "last" not in result:
        raise ValueError("Kraken OHLC result incomplete")
    entries = [(k, v) for k, v in result.items() if k != "last"]
    if len(entries) != 1 or not isinstance(entries[0][1], list):
        raise ValueError("ambiguous OHLC result")
    rows = entries[0][1]
    if len(rows) < 30 or len(rows) > 721:
        raise ValueError("insufficient or excessive historical candles")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    stamps = set()
    parsed = []
    for raw in rows[:-1]:
        if not isinstance(raw, list) or len(raw) < 8:
            raise ValueError("malformed OHLC row")
        t = raw[0]
        if type(t) is not int or t in stamps or t % 900 != 0:
            raise ValueError("duplicate or misaligned candle")
        stamps.add(t)
        c = Candle(t, Decimal(str(raw[1])), Decimal(str(raw[2])),
                   Decimal(str(raw[3])), Decimal(str(raw[4])),
                   Decimal(str(raw[6])))
        c.validate()
        if t + 900 > now.timestamp():
            raise ValueError("historical bar is incomplete or future dated")
        parsed.append(c)
    if any(parsed[i].at >= parsed[i+1].at for i in range(len(parsed)-1)):
        raise ValueError("unordered candles")
    return parsed


def aligned(series):
    if not isinstance(series, dict) or set(series) != set(VALID_PAIRS):
        raise ValueError("all three supported markets required")
    maps = {}
    for symbol, bars in series.items():
        if not isinstance(bars, list) or len(bars) < 40:
            raise ValueError("insufficient OHLC source history")
        for c in bars:
            c.validate()
        if len({c.at for c in bars}) != len(bars):
            raise ValueError("duplicate candle timestamp")
        maps[symbol] = {c.at: c for c in bars}
    common = sorted(set.intersection(*(set(x.keys()) for x in maps.values())))
    if len(common) < 40:
        raise ValueError("insufficient aligned time samples")
    # Gapped candles imply missing observations and stop rather than interpolate.
    if any(y - x != 900 for x, y in zip(common, common[1:])):
        raise ValueError("missing aligned 15-minute intervals")
    return common, {s: [maps[s][t] for t in common] for s in sorted(maps)}


def _signal(method, candles, idx, offset):
    """Make decision from COMPLETED bar idx-1, never the fill bar idx."""
    if idx < 18:
        return False
    past = candles[idx-17:idx-1]
    prev = candles[idx-1]
    if method == "control":
        return (idx + offset * 4) % 12 == 0
    if method == "breakout":
        avg_vol = sum((x.volume for x in past), Decimal(0)) / len(past)
        return (prev.cl > max(x.hi for x in past) * Decimal("1.001")
                and prev.volume > avg_vol * Decimal("1.25"))
    if method == "reversal":
        mean = sum((x.cl for x in past), Decimal(0)) / len(past)
        return (prev.lo < mean * Decimal("0.994")
                and prev.cl > prev.op and prev.cl > candles[idx-2].cl)
    raise ValueError("unrecognized precommitted strategy")


def simulate(aligned_bars, *, strategy: str, start: int, end: int,
             starting_cash: Decimal = START):
    """Execute virtual ask-side entries and stop-first OHLC exits.

    Segment boundaries forcibly close inventory; the holdout is a fresh
    independent *test account*. Broker execution/settlement isn't represented.
    """
    if strategy not in STRATEGIES:
        raise ValueError("unknown strategy")
    symbols = sorted(aligned_bars)
    if set(symbols) != set(VALID_PAIRS):
        raise ValueError("expected three original crypto markets")
    n = len(aligned_bars[symbols[0]])
    if any(len(aligned_bars[s]) != n for s in symbols):
        raise ValueError("mismatched candle counts")
    if not (18 <= start < end <= n and end - start >= 15):
        raise ValueError("invalid segment range")
    if starting_cash <= 0 or starting_cash > Decimal("100000"):
        raise ValueError("invalid starting virtual cash")
    cash = starting_cash
    held = {}
    events = []
    equity_peak = starting_cash
    worst_dd = Decimal(0)
    daily_start = starting_cash
    day = None
    day_entries = 0
    total_fees = Decimal(0)
    cooldown = {}

    def close_one(symbol, ref, reason, stamp, i):
        nonlocal cash, total_fees
        position = held[symbol]
        price = ref * (Decimal(1) - SLIPPAGE)
        notional = position["qty"] * price
        fee = notional * TAKER
        proceeds = notional - fee
        if proceeds <= 0:
            raise ValueError("unrealistic fee exceeds proceeds")
        cash += proceeds
        total_fees += fee
        pnl = proceeds - position["debit"]
        events.append({
            "asset": "crypto", "symbol": symbol, "side": "sell",
            "time_utc": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
            "quantity": str(position["qty"]), "price": str(price),
            "fee_estimate": str(fee), "pnl": str(pnl),
            "reason": reason, "simulation_not_broker_fill": True,
        })
        del held[symbol]
        cooldown[symbol] = i + 4

    for i in range(start, end):
        stamp = aligned_bars[symbols[0]][i].at
        if any(aligned_bars[s][i].at != stamp for s in symbols):
            raise ValueError("cross asset candle timestamps do not align")
        utcday = datetime.fromtimestamp(stamp, timezone.utc).date()
        if day != utcday:
            day = utcday
            day_start = cash + sum(
                p["qty"] * aligned_bars[s][i].op for s, p in held.items())
            day_entries = 0

        # Exit first; if stop and target both touch the same bar, STOP wins.
        for symbol in list(held):
            p = held[symbol]
            bar = aligned_bars[symbol][i]
            if bar.op <= p["stop"]:
                ref, reason = bar.op, "gap_stop"
            elif bar.lo <= p["stop"]:
                ref, reason = p["stop"], "stop"
            elif bar.op >= p["target"]:
                ref, reason = p["target"], "target_capped"
            elif bar.hi >= p["target"]:
                ref, reason = p["target"], "target"
            elif i - p["at"] >= MAX_HOLD_BARS:
                ref, reason = bar.cl, "time_exit"
            elif i == end - 1:
                ref, reason = bar.cl, "segment_end"
            else:
                continue
            close_one(symbol, ref, reason, stamp, i)

        marked = cash + sum(p["qty"] * aligned_bars[s][i].cl
                            for s, p in held.items())
        if (marked > daily_start * Decimal("0.97")
                and day_entries < MAX_PER_DAY and i < end - 1):
            for offset, symbol in enumerate(symbols):
                if symbol in held or len(held) >= MAX_CONCURRENT:
                    continue
                if i < cooldown.get(symbol, -1):
                    continue
                if not _signal(strategy, aligned_bars[symbol], i, offset):
                    continue
                bar = aligned_bars[symbol][i]
                price = bar.op * (Decimal(1) + SLIPPAGE)
                budget = min(CAP, cash - Decimal("1.00"))
                if budget < Decimal("5.00"):
                    continue
                qty = (budget / (price * (Decimal(1) + TAKER))).quantize(
                    SLOT, rounding=ROUND_DOWN)
                cost = qty * price
                fee = cost * TAKER
                debit = cost + fee
                if qty <= 0 or debit > CAP or debit > cash or debit < 5:
                    continue
                cash -= debit
                total_fees += fee
                held[symbol] = {
                    "qty": qty, "debit": debit, "at": i,
                    "stop": price * (Decimal(1) - STOP),
                    "target": price * (Decimal(1) + TARGET),
                }
                events.append({
                    "asset": "crypto", "symbol": symbol, "side": "buy",
                    "time_utc": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                    "quantity": str(qty), "price": str(price),
                    "fee_estimate": str(fee),
                    "reason": strategy, "simulation_not_broker_fill": True,
                })
                # Entry occurs at this bar OPEN. Even on the entry bar,
                # intrabar stop/target collisions are conservatively STOP-first.
                position = held[symbol]
                if bar.lo <= position["stop"]:
                    close_one(symbol, position["stop"], "stop", stamp, i)
                elif bar.hi >= position["target"]:
                    close_one(symbol, position["target"], "target", stamp, i)
                day_entries += 1
                if day_entries >= MAX_PER_DAY:
                    break

        equity = cash + sum(p["qty"] * aligned_bars[s][i].cl
                            for s, p in held.items())
        if equity > equity_peak:
            equity_peak = equity
        dd = (equity_peak - equity) / equity_peak
        if dd > worst_dd:
            worst_dd = dd
        if cash < 0:
            raise ValueError("virtual cash negative")
    if held:
        raise ValueError("segment failed to liquidate inventory")
    closed = [e for e in events if e["side"] == "sell"]
    wins = sum(Decimal(e["pnl"]) > 0 for e in closed)
    losses = sum(Decimal(e["pnl"]) <= 0 for e in closed)
    net_pnl = cash - starting_cash
    return {
        "strategy": strategy,
        "start_at_utc": datetime.fromtimestamp(
            aligned_bars[symbols[0]][start].at, timezone.utc).isoformat(),
        "end_at_utc": datetime.fromtimestamp(
            aligned_bars[symbols[0]][end-1].at + 900, timezone.utc).isoformat(),
        "starting_virtual_cash": str(starting_cash),
        "ending_virtual_cash": str(cash.quantize(CENT)),
        "net_pnl_after_estimated_costs": str(net_pnl.quantize(CENT)),
        "return_pct": str((net_pnl / starting_cash * 100).quantize(CENT)),
        "max_drawdown_pct": str((worst_dd * 100).quantize(CENT)),
        "estimated_fees": str(total_fees.quantize(CENT)),
        "virtual_buys": sum(e["side"] == "buy" for e in events),
        "virtual_closes": len(closed),
        "wins": wins, "losses_or_flats": losses,
        "win_rate_pct": str(
            (Decimal(wins) / len(closed) * 100).quantize(CENT)) if closed else None,
        "events": events,
        "mode": "HISTORICAL_OFFLINE_SIMULATED_NOT_A_PAPER_BROKER",
    }
