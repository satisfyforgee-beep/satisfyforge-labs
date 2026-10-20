"""Pure risk preflight; no broker credentials or order transport imports.

The BUY candidate can be vetoed. This is not authorization to place a trade.
Stops are estimates; gaps can exceed the planned risk.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo
from .agents import Decision

_ET = ZoneInfo("America/New_York")


def D(value):
    return Decimal(str(value))


@dataclass(frozen=True)
class RiskPolicy:
    maximum_notional: Decimal = Decimal("20.00")
    maximum_equity_fraction: Decimal = Decimal("0.50")
    minimum_cash_reserve: Decimal = Decimal("5.00")
    maximum_planned_trade_loss: Decimal = Decimal("1.00")
    maximum_daily_loss: Decimal = Decimal("3.00")
    stop_fraction: Decimal = Decimal("0.02")
    take_profit_fraction: Decimal = Decimal("0.035")
    max_quote_age_seconds: int = 5
    max_entries_per_day: int = 2

    def __post_init__(self):
        if (self.maximum_notional <= 0 or
            not 0 < self.maximum_equity_fraction <= 1 or
            self.minimum_cash_reserve < 0 or
            self.maximum_planned_trade_loss <= 0 or
            self.maximum_daily_loss <= 0 or
            not 0 < self.stop_fraction < .2 or
            not 0 < self.take_profit_fraction < .5 or
            self.max_quote_age_seconds <= 0 or
            self.max_entries_per_day < 1):
            raise ValueError("invalid risk policy")


@dataclass(frozen=True)
class BrokerState:
    cash: Decimal
    equity: Decimal
    day_start_equity: Decimal
    buying_power: Decimal
    positions: int
    pending_orders: int
    entries_today: int
    market_open: bool
    trading_blocked: bool


@dataclass(frozen=True)
class Quote:
    bid: Decimal
    ask: Decimal
    time: datetime


@dataclass(frozen=True)
class Preflight:
    approved: bool
    symbol: str
    reason: str
    qty: int = 0
    entry_limit: str = ""
    stop_reference: str = ""
    target_reference: str = ""
    planned_risk: str = ""
    notional: str = ""


def _cents(value):
    return D(value).quantize(Decimal(".01"), rounding=ROUND_DOWN)


class RiskGate:
    """Strict spend, exposure, freshness, daily-loss and duplicate vetoes."""

    def __init__(self, policy=RiskPolicy()):
        self.p = policy

    def check(self, decision: Decision, state: BrokerState,
              quote: Quote, now: datetime) -> Preflight:
        sym = decision.symbol
        def deny(reason):
            return Preflight(False, sym, reason)
        if (decision.action != "candidate" or decision.support_count < 4 or
                any(v.verdict == "veto" for v in decision.votes)):
            return deny("consensus did not authorize candidate")
        try:
            decision_at = datetime.fromisoformat(decision.observed_at)
        except (TypeError, ValueError):
            return deny("missing or invalid signal timestamp")
        if decision_at.tzinfo is None or now.tzinfo is None:
            return deny("timezone missing")
        signal_age = (now - decision_at).total_seconds()
        if not 0 <= signal_age <= self.p.max_quote_age_seconds:
            return deny("stale signal")
        if now.tzinfo is None or quote.time.tzinfo is None:
            return deny("timezone missing")
        now = now.astimezone(timezone.utc)
        age = (now - quote.time.astimezone(timezone.utc)).total_seconds()
        if not 0 <= age <= self.p.max_quote_age_seconds:
            return deny("stale or future quote")
        if quote.ask <= 0 or quote.bid <= 0 or quote.ask < quote.bid:
            return deny("crossed or missing quote")
        if not state.market_open or state.trading_blocked:
            return deny("market closed or broker trading blocked")
        local = now.astimezone(_ET)
        minutes = local.hour * 60 + local.minute
        if local.weekday() >= 5 or not (9*60+35 <= minutes < 14*60+45):
            return deny("outside 09:35-14:44 ET entry window")
        if state.positions or state.pending_orders:
            return deny("open position or pending order must reconcile first")
        if state.entries_today >= self.p.max_entries_per_day:
            return deny("maximum daily entries reached")
        if min(state.cash, state.equity, state.buying_power, state.day_start_equity) <= 0:
            return deny("missing or nonpositive account equity")
        if state.day_start_equity - state.equity >= self.p.maximum_daily_loss:
            return deny("hard daily loss cutoff")
        remaining = min(self.p.maximum_notional,
                        state.equity * self.p.maximum_equity_fraction,
                        state.cash - self.p.minimum_cash_reserve,
                        state.buying_power - self.p.minimum_cash_reserve)
        if remaining < quote.ask:
            return deny("not enough unleveraged buying power under capital cap")
        stop = _cents(quote.ask * (1 - self.p.stop_fraction))
        target = _cents(quote.ask * (1 + self.p.take_profit_fraction))
        if not 0 < stop < quote.ask < target:
            return deny("invalid bracket geometry")
        planned_risk_per_share = quote.ask - stop
        if planned_risk_per_share <= 0:
            return deny("nonpositive estimated risk")
        qty = min(int(remaining // quote.ask),
                  int(self.p.maximum_planned_trade_loss // planned_risk_per_share))
        if qty < 1:
            return deny("risk cap cannot fund one whole share")
        notional = qty * quote.ask
        planned = qty * planned_risk_per_share
        return Preflight(True, sym,
                         "Research preflight ONLY; broker execution not authorized",
                         qty=qty, entry_limit=str(_cents(quote.ask)),
                         stop_reference=str(stop), target_reference=str(target),
                         planned_risk=str(_cents(planned)),
                         notional=str(_cents(notional)))
