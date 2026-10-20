"""Provider-neutral, read-only quote coverage and integrity gate.

No broker order endpoints. A DATA_READY verdict only validates a quote for
downstream independent strategy/risk review; it never authorizes a trade.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Dict, Optional, Tuple
import re


class AssetClass(str, Enum):
    STOCK = "stock"
    OPTION = "option"
    CRYPTO = "crypto"


class Coverage(str, Enum):
    CONSOLIDATED = "consolidated"
    SINGLE_VENUE = "single_venue"
    INDICATIVE = "indicative"
    DELAYED = "delayed"


# Whitelist is intentional. A wire payload cannot award itself better coverage.
PROVIDER_CAPABILITIES = {
    ("alpaca_iex", AssetClass.STOCK): Coverage.SINGLE_VENUE,
    ("alpaca_options_indicative", AssetClass.OPTION): Coverage.INDICATIVE,
    ("tradier_live", AssetClass.STOCK): Coverage.CONSOLIDATED,
    ("tradier_live", AssetClass.OPTION): Coverage.CONSOLIDATED,
    ("tradier_sandbox", AssetClass.STOCK): Coverage.DELAYED,
    ("tradier_sandbox", AssetClass.OPTION): Coverage.DELAYED,
    ("kraken_public", AssetClass.CRYPTO): Coverage.SINGLE_VENUE,
}

_STOCK = re.compile(r"^[A-Z][A-Z0-9.]{0,7}$")
_OCC_OPTION = re.compile(r"^[A-Z]{1,6}[0-9]{6}[CP][0-9]{8}$")
_CRYPTO = re.compile(r"^[A-Z0-9]{2,12}/USD$")


def _aware(dt):
    return isinstance(dt, datetime) and dt.tzinfo is not None and dt.utcoffset() is not None


@dataclass(frozen=True)
class MarketQuote:
    provider: str
    asset: AssetClass
    symbol: str
    bid: float
    ask: float
    bid_at: datetime
    ask_at: datetime
    received_at: datetime
    # Must be set by an authenticated provider adapter, never by market payload.
    entitlement_verified: bool = False

    @property
    def coverage(self):
        return PROVIDER_CAPABILITIES.get((self.provider, self.asset))

    @property
    def mid(self):
        return (self.bid + self.ask) / 2

    @property
    def observed_at(self):
        # A REST order-book snapshot is current when fetched even if a resting
        # best-price order was last updated many seconds earlier. We retain the
        # exchange publication timestamps separately for audit/research.
        if self.provider == "kraken_public":
            return self.received_at
        return min(self.bid_at, self.ask_at)

    def validate(self, max_bid_ask_skew=3.0):
        if self.coverage is None:
            raise ValueError("unknown provider or unauthorized asset/provider pairing")
        if not isinstance(self.symbol, str):
            raise ValueError("symbol must be a string")
        if self.asset == AssetClass.STOCK and not _STOCK.fullmatch(self.symbol):
            raise ValueError("invalid stock symbol")
        if self.asset == AssetClass.OPTION and not _OCC_OPTION.fullmatch(self.symbol):
            raise ValueError("invalid OCC option contract")
        if self.asset == AssetClass.CRYPTO and not _CRYPTO.fullmatch(self.symbol):
            raise ValueError("unsupported USD crypto trading pair")
        if not all(_aware(x) for x in (self.bid_at, self.ask_at, self.received_at)):
            raise ValueError("all timestamps must be timezone-aware")
        if not all(isfinite(x) for x in (self.bid, self.ask)):
            raise ValueError("non-finite quote")
        if self.bid <= 0 or self.ask < self.bid:
            raise ValueError("zero, negative or crossed quote")
        skew = abs((self.bid_at - self.ask_at).total_seconds())
        if self.provider != "kraken_public" and skew > max_bid_ask_skew:
            raise ValueError("bid and ask timestamps too far apart")
        if (self.observed_at - self.received_at).total_seconds() > 1.0:
            raise ValueError("market timestamp newer than receiving clock")


@dataclass(frozen=True)
class CoverageAssessment:
    symbol: str
    asset: AssetClass
    status: str
    reason: str
    source: str = ""
    coverage: str = ""
    bid: Optional[float] = None
    ask: Optional[float] = None
    feed_count: int = 0
    # Data quality alone can NEVER authorize a live order.
    live_order_authorized: bool = False

    def as_report(self):
        return {
            "symbol": self.symbol, "asset": self.asset.value,
            "status": self.status, "reason": self.reason,
            "source": self.source, "coverage": self.coverage,
            "bid": self.bid, "ask": self.ask,
            "feeds_checked": self.feed_count,
            "live_order_authorized": False,
        }


class CoverageGate:
    """Choose fresh entitled data, prefer consolidated, veto major disagreement.

    Single-exchange and indicative quotes may be shown for RESEARCH_ONLY;
    neither qualifies as consolidated data for live-execution readiness.
    """

    def __init__(self, max_age_seconds=4.0, max_source_disagreement=0.015,
                 max_relative_spread=0.02):
        if not 0 < max_age_seconds <= 60:
            raise ValueError("invalid max age")
        if not 0 < max_source_disagreement <= 0.25:
            raise ValueError("invalid source divergence")
        if not 0 < max_relative_spread <= 0.5:
            raise ValueError("invalid maximum spread")
        self.max_age = max_age_seconds
        self.max_divergence = max_source_disagreement
        self.max_spread = max_relative_spread
        self._latest: Dict[Tuple[str, AssetClass, str], MarketQuote] = {}

    def ingest(self, quote: MarketQuote):
        quote.validate()
        key = (quote.symbol, quote.asset, quote.provider)
        existing = self._latest.get(key)
        if existing and quote.observed_at <= existing.observed_at:
            return False
        self._latest[key] = quote
        return True

    def assess(self, symbol: str, asset: AssetClass, now: datetime):
        if not _aware(now):
            raise ValueError("now must have timezone")
        sources = [q for (s, a, _), q in self._latest.items()
                   if s == symbol and a == asset]
        def denied(reason):
            return CoverageAssessment(symbol, asset, "BLOCKED", reason,
                                      feed_count=len(sources))
        eligible = []
        for q in sources:
            if not q.entitlement_verified:
                continue
            age = (now - q.observed_at).total_seconds()
            receive_age = (now - q.received_at).total_seconds()
            if not (0 <= age <= self.max_age and
                    0 <= receive_age <= self.max_age):
                continue
            if (q.ask - q.bid) / q.mid > self.max_spread:
                continue
            eligible.append(q)
        if not eligible:
            return denied("no fresh, authorized, appropriately priced quotes")
        priority = {Coverage.CONSOLIDATED: 0,
                    Coverage.SINGLE_VENUE: 1,
                    Coverage.INDICATIVE: 2,
                    Coverage.DELAYED: 3}
        eligible.sort(key=lambda x: (priority[x.coverage],
                                    -x.observed_at.timestamp()))
        chosen = eligible[0]
        # When separate fresh eligible sources strongly contradict one another,
        # stop rather than silently replacing a quote with the preferred feed.
        for other in eligible[1:]:
            if abs(other.mid / chosen.mid - 1) > self.max_divergence:
                return denied("material disagreement between live quote sources")
        if chosen.coverage == Coverage.CONSOLIDATED:
            status = "DATA_READY"
            reason = "consolidated data usable for separate strategy/risk review"
        else:
            status = "RESEARCH_ONLY"
            reason = "partial/indicative/delayed feed cannot qualify for live execution"
        return CoverageAssessment(symbol, asset, status, reason,
                                  source=chosen.provider,
                                  coverage=chosen.coverage.value,
                                  bid=chosen.bid, ask=chosen.ask,
                                  feed_count=len(sources))
