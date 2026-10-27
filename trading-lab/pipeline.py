"""Single, offline signal-to-paper-journal path; absolutely no broker orders.

Reuses the existing OHLC breakout research engine. No background process or
trade-capable broker module is imported. The only writer is the local SQLite
PaperEngine, which validates cash, spreads, quote age and duplicate IDs.
"""
from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

_STRATEGY_PATH = Path(__file__).resolve().parent.parent / "algo-trading"
if str(_STRATEGY_PATH) not in sys.path:
    sys.path.insert(0, str(_STRATEGY_PATH))

from zerocost_bot.engine import Bar  # noqa: E402
from zerocost_bot.signals import choose_signal  # noqa: E402
from paper_engine import Instrument, PaperEngine, PaperOrder, Quote  # noqa: E402


def stable_signal_id(symbol: str, bar_time: datetime) -> str:
    if bar_time.tzinfo is None:
        raise ValueError("Signal time must be timezone-aware")
    canonical = f"volume-breakout-v1|{symbol.upper()}|{bar_time.astimezone(timezone.utc).isoformat()}"
    return "sf-signal-" + hashlib.sha256(canonical.encode()).hexdigest()[:30]


def evaluate_equity_breakout(
    journal: PaperEngine,
    completed_bars: list[Bar],
    quote: Quote,
    now: datetime,
    *,
    max_quantity: int = 1,
    max_signal_age_seconds: int = 180,
) -> dict:
    """One immediate synthetic/paper quote fill, never an actual brokerage call.

    Bar timestamps denote the START of a one-minute interval. A quote must be
    no earlier than the close of the final bar and must pass journal quote QA.
    """
    def skip(reason: str) -> dict:
        return {"action": "SKIP", "reason": reason, "paper_only": True}

    if now.tzinfo is None:
        raise ValueError("Evaluation timestamp must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if os.getenv("SF_TRADING_PAUSED", "").lower() in {"1", "true", "yes", "on"}:
        return skip("Emergency pause is enabled")
    if not isinstance(max_quantity, int) or isinstance(max_quantity, bool) or max_quantity < 1:
        raise ValueError("max_quantity must be a positive whole number")
    if max_signal_age_seconds <= 0:
        raise ValueError("max_signal_age_seconds must be positive")
    if quote.instrument.asset != "equity":
        return skip("This signal adapter supports underlying equities only")
    if not completed_bars:
        return skip("No completed market bars")
    if any(bar.symbol.upper() != quote.instrument.symbol.upper() for bar in completed_bars):
        return skip("Bar/quote symbol mismatch")

    signal = choose_signal(completed_bars)
    if signal is None:
        return skip("No qualified breakout")
    close_at = signal.time.astimezone(timezone.utc) + timedelta(minutes=1)
    if close_at > now:
        return skip("Latest bar has not closed")
    if (now - close_at).total_seconds() > max_signal_age_seconds:
        return skip("Signal is stale")
    if quote.asof.astimezone(timezone.utc) < close_at:
        return skip("Quote precedes the completed signal bar")

    affordable = int((journal.policy.max_order_cost / quote.ask).to_integral_value(rounding=ROUND_FLOOR))
    quantity = min(affordable, max_quantity)
    if quantity <= 0:
        return skip("Not enough per-order budget for one whole share")
    signal_id = stable_signal_id(signal.symbol, signal.time)
    order = PaperOrder(
        client_id="sf-paper-" + signal_id.removeprefix("sf-signal-"),
        instrument=Instrument(signal.symbol.upper(), "equity"),
        side="buy",
        quantity=Decimal(quantity),
        limit_price=quote.ask,
        signal_id=signal_id,
    )
    result = journal.submit(order, quote, now)
    return {"action": "PAPER_" + result["status"], "signal_id": signal_id,
            "order": result, "paper_only": True}


def safety_readiness() -> dict:
    """Diagnostic only: report capabilities without reading or printing secrets."""
    return {
        "paper_simulation_available": True,
        "broker_order_submission_enabled": False,
        "live_money_enabled": False,
        "always_on_monitoring_enabled": False,
        "emergency_pause": os.getenv("SF_TRADING_PAUSED", "").lower() in {"1", "true", "yes", "on"},
        "alpaca_paper_data_credentials_present": bool(os.getenv("ALPACA_PAPER_KEY") and os.getenv("ALPACA_PAPER_SECRET")),
        "tradier_sandbox_credentials_present": bool(os.getenv("TRADIER_SANDBOX_TOKEN")),
        "limits": "One-shot, paper-only. No unverified execution claims.",
    }
