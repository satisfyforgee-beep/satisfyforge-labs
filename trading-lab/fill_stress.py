"""Deterministic adverse-fill stress fixtures for the offline paper lab.

The function in this module is deliberately pure: it does not connect to a
provider, mutate a journal, or claim that a simulated fill occurred at a
broker.  It applies caller-declared latency, slippage, fee, and displayed-size
assumptions to one synthetic cash-only buy attempt.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN

from paper_engine import PaperOrder, Quote


def _decimal(value, label: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{label} must use an exact decimal")
    try:
        parsed = Decimal(value)
    except (TypeError, ValueError, ArithmeticError):
        raise ValueError(f"Invalid {label}") from None
    if not parsed.is_finite() or parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValueError(f"Invalid {label}")
    return parsed


def _utc(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class AdverseFillAssumptions:
    """Explicit synthetic assumptions; none are inferred from paper fills."""

    latency_ms: int
    slippage_bps: Decimal
    displayed_size_fraction: Decimal
    fixed_fee: Decimal = Decimal("0")
    fee_per_unit: Decimal = Decimal("0")
    max_quote_age_seconds: int = 15

    def __post_init__(self) -> None:
        if type(self.latency_ms) is not int or self.latency_ms < 0:
            raise ValueError("latency_ms must be a nonnegative integer")
        if type(self.max_quote_age_seconds) is not int or self.max_quote_age_seconds <= 0:
            raise ValueError("max_quote_age_seconds must be positive")
        for name in ("slippage_bps", "fixed_fee", "fee_per_unit"):
            object.__setattr__(self, name, _decimal(getattr(self, name), name, allow_zero=True))
        fraction = _decimal(self.displayed_size_fraction, "displayed_size_fraction")
        if fraction > 1:
            raise ValueError("displayed_size_fraction cannot exceed one")
        object.__setattr__(self, "displayed_size_fraction", fraction)


def stress_cash_buy(*, order: PaperOrder, quote: Quote,
                    displayed_ask_size: Decimal, cash_before: Decimal,
                    decision_at: datetime,
                    assumptions: AdverseFillAssumptions) -> dict:
    """Return a conservative synthetic no/partial/full-fill observation.

    This helper never resizes to spend remaining cash and never writes to the
    paper journal.  Whole-share equities/options are rounded down after the
    displayed-size haircut; fractional crypto keeps exact decimal quantity.
    """
    if order.side != "buy":
        raise ValueError("Adverse-fill fixture supports cash-only buys only")
    if order.instrument != quote.instrument:
        raise ValueError("Quote instrument does not match order")
    if quote.delayed:
        return _result(order, quote, decision_at, cash_before,
                       status="NO_FILL", reason="Delayed quote is not executable")

    decision = _utc(decision_at, "decision_at")
    quote_time = _utc(quote.asof, "quote.asof")
    simulated_execution = decision + timedelta(milliseconds=assumptions.latency_ms)
    if quote_time > decision:
        return _result(order, quote, simulated_execution, cash_before,
                       status="NO_FILL", reason="Future quote cannot support a fill")
    if (simulated_execution - quote_time).total_seconds() > assumptions.max_quote_age_seconds:
        return _result(order, quote, simulated_execution, cash_before,
                       status="NO_FILL", reason="Quote expired during modeled latency")

    displayed = _decimal(displayed_ask_size, "displayed_ask_size", allow_zero=True)
    cash = _decimal(cash_before, "cash_before", allow_zero=True)
    executable_size = min(order.quantity, displayed * assumptions.displayed_size_fraction)
    if order.instrument.asset != "crypto":
        executable_size = executable_size.to_integral_value(rounding=ROUND_DOWN)
    if executable_size <= 0:
        return _result(order, quote, simulated_execution, cash,
                       status="NO_FILL", reason="No conservative displayed liquidity")

    adverse_price = quote.ask * (
        Decimal("1") + assumptions.slippage_bps / Decimal("10000"))
    if adverse_price > order.limit_price:
        return _result(order, quote, simulated_execution, cash,
                       status="NO_FILL", reason="Modeled adverse price exceeds limit")

    fee = assumptions.fixed_fee + assumptions.fee_per_unit * executable_size
    debit = executable_size * order.instrument.multiplier * adverse_price + fee
    if debit > cash:
        return _result(order, quote, simulated_execution, cash,
                       status="NO_FILL", reason="Cash-only debit exceeds available cash")

    status = "FULL_FILL" if executable_size == order.quantity else "PARTIAL_FILL"
    return _result(
        order, quote, simulated_execution, cash, status=status,
        reason="Synthetic adverse fill within displayed-liquidity and cash caps",
        filled_quantity=executable_size, fill_price=adverse_price,
        fee=fee, debit=debit, cash_after=cash - debit)


def _result(order: PaperOrder, quote: Quote, observed_at: datetime,
            cash_before: Decimal, *, status: str, reason: str,
            filled_quantity: Decimal = Decimal("0"),
            fill_price: Decimal | None = None,
            fee: Decimal = Decimal("0"), debit: Decimal = Decimal("0"),
            cash_after: Decimal | None = None) -> dict:
    cash = Decimal(cash_before)
    after = cash if cash_after is None else cash_after
    return {
        "mode": "OFFLINE_SYNTHETIC_ADVERSE_FILL_STRESS",
        "paper_only": True,
        "execution_evidence": False,
        "status": status,
        "reason": reason,
        "client_id": order.client_id,
        "symbol": order.instrument.symbol,
        "requested_quantity": str(order.quantity),
        "filled_quantity": str(filled_quantity),
        "fill_price": str(fill_price) if fill_price is not None else None,
        "fee": str(fee),
        "all_in_debit": str(debit),
        "cash_before": str(cash),
        "cash_after": str(after),
        "quote_source": quote.source,
        "quote_asof_utc": _utc(quote.asof, "quote.asof").isoformat(),
        "observed_at_utc": _utc(observed_at, "observed_at").isoformat(),
        "warning": "Synthetic stress observation only; not a broker or exchange fill.",
    }
