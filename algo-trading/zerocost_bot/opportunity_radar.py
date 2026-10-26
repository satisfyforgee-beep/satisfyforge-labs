"""Read-only cross-asset research/affordability review for a CASH-ONLY paper lab.

Never imports trading adapters or submits orders. A quote and a paper-ledger
snapshot are *not* a verified signal, an executable quote, or broker cash.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, InvalidOperation
import re

from .market_coverage import AssetClass, CoverageGate, MarketQuote

OCC = re.compile(r"^[A-Z]{1,6}([0-9]{6})[CP][0-9]{8}$")
PAPER_MODE = "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE"


def _money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("invalid paper amount") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("invalid paper amount")
    return amount


@dataclass(frozen=True)
class PaperIdea:
    asset: str
    symbol: str
    status: str
    reasons: tuple
    data_source: str
    reference_ask: str
    hypothetical_max_quantity: str
    hypothetical_max_debit: str
    live_order_authorized: bool = False
    paper_order_authorized: bool = False

    def as_report(self):
        return {
            "mode": "READ_ONLY_PAPER_RESEARCH_NOT_A_TRADE",
            "asset": self.asset, "symbol": self.symbol,
            "status": self.status, "reasons": list(self.reasons),
            "data_source": self.data_source,
            "reference_ask": self.reference_ask,
            "hypothetical_max_quantity": self.hypothetical_max_quantity,
            "hypothetical_max_debit": self.hypothetical_max_debit,
            "live_order_authorized": False, "paper_order_authorized": False,
        }


def review_paper_idea(quote: MarketQuote, capital: dict, *, now: datetime,
                      market_regular_session=False, estimated_fee="0.25"):
    """Size a hypothetical long-only paper candidate without changing capital.

    quote: a provider-verified read-only quote, evaluated for freshness and
    spread. capital: an OFFLINE PaperCapital.snapshot(), never broker balances.
    A candidate does not mean the instrument has a profitable entry signal.
    """
    if not isinstance(quote, MarketQuote) or not isinstance(capital, dict):
        raise ValueError("quote and capital snapshot required")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    if capital.get("mode") != PAPER_MODE:
        raise ValueError("only verified-format offline paper capital accepted")
    try:
        available = _money(capital["available_for_next_paper_trade"])
        order_cap = _money(capital["maximum_order_debit"])
        settled = _money(capital["settled_cash"])
        reserved = _money(capital["reserved_cash"])
        active = int(capital["active_reservation_count"])
        positions = capital["positions"]
        if not isinstance(positions, list) or type(capital["active_reservation_count"]) is not int:
            raise ValueError("invalid positions")
        if active < 0 or reserved > settled or available != settled - reserved:
            raise ValueError("inconsistent replay snapshot")
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError("invalid replay capital snapshot") from exc
    fee = _money(estimated_fee)
    budget = min(available, order_cap, Decimal("30.00"))
    reasons = []
    data_source = ""
    ask = Decimal("0")
    quantity = Decimal("0")
    debit = Decimal("0")

    try:
        gate = CoverageGate()
        gate.ingest(quote)
        assessment = gate.assess(quote.symbol, quote.asset, now)
        data_source = assessment.source
        if assessment.status == "BLOCKED":
            reasons.append("QUOTE_UNVERIFIED_OR_STALE")
        if assessment.coverage == "delayed":
            reasons.append("DELAYED_QUOTES_NOT_ENTRY_DATA")
        if quote.asset != AssetClass.CRYPTO and assessment.status != "DATA_READY":
            reasons.append("CONSOLIDATED_CURRENT_STOCK_OPTION_DATA_REQUIRED")
        if quote.asset == AssetClass.CRYPTO and assessment.source != "kraken_public":
            reasons.append("SUPPORTED_SPOT_CRYPTO_REFERENCE_MISSING")
        ask = Decimal(str(quote.ask))
        bid = Decimal(str(quote.bid))
        max_spread = Decimal("0.01") if quote.asset == AssetClass.CRYPTO else (
            Decimal("0.10") if quote.asset == AssetClass.OPTION else Decimal("0.01"))
        if (ask - bid) / ask > max_spread:
            reasons.append("WIDE_SPREAD")
    except (ValueError, TypeError, OverflowError, InvalidOperation):
        reasons.append("MALFORMED_QUOTE")

    if quote.asset != AssetClass.CRYPTO and not market_regular_session:
        reasons.append("US_REGULAR_SESSION_CLOSED")
    if active + len(positions) >= 5:
        reasons.append("MAX_FIVE_PAPER_POSITIONS_OR_RESERVATIONS")
    if budget <= fee:
        reasons.append("INSUFFICIENT_REPLAY_BUDGET")

    if quote.asset == AssetClass.OPTION:
        match = OCC.fullmatch(quote.symbol)
        if match:
            try:
                expiry = datetime.strptime(match.group(1), "%y%m%d").date()
                if (expiry - now.astimezone(timezone.utc).date()).days < 7:
                    reasons.append("OPTION_EXPIRY_TOO_NEAR")
            except ValueError:
                reasons.append("INVALID_OPTION_EXPIRY")
        else:
            reasons.append("INVALID_OPTION_CONTRACT")

    if ask > 0 and budget > fee:
        if quote.asset == AssetClass.CRYPTO:
            quantity = ((budget - fee) / ask).quantize(
                Decimal("0.00000001"), rounding=ROUND_DOWN)
        elif quote.asset == AssetClass.STOCK:
            quantity = ((budget - fee) / ask).to_integral_value(rounding=ROUND_DOWN)
        elif quote.asset == AssetClass.OPTION:
            quantity = ((budget - fee) / (ask * Decimal(100))).to_integral_value(
                rounding=ROUND_DOWN)
        if quantity > 0:
            multiplier = Decimal(100) if quote.asset == AssetClass.OPTION else Decimal(1)
            debit = quantity * ask * multiplier + fee
        else:
            reasons.append("ONE_UNIT_OR_CONTRACT_EXCEEDS_30_DOLLAR_CAP")
    if not reasons and quantity > 0:
        reasons.append("AFFORDABLE_FRESH_QUOTE_ONLY_NO_VERIFIED_ALPHA")
    else:
        quantity, debit = Decimal(0), Decimal(0)
    return PaperIdea(
        asset=quote.asset.value, symbol=quote.symbol,
        status="RESEARCH_ONLY" if reasons == ["AFFORDABLE_FRESH_QUOTE_ONLY_NO_VERIFIED_ALPHA"] else "BLOCKED",
        reasons=tuple(reasons), data_source=data_source,
        reference_ask=str(ask), hypothetical_max_quantity=str(quantity),
        hypothetical_max_debit=str(debit.quantize(Decimal("0.01"))),
    )
