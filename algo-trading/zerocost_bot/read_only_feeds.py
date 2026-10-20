"""Strict, read-only adapters for two differently entitled market-data providers.

Alpaca IEX events are single-venue. Tradier LIVE quotes are consolidated for
eligible brokerage users. This code contains NO order or funding operations.
"""
from __future__ import annotations
from datetime import datetime, timezone
from math import isfinite
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .market_coverage import AssetClass, MarketQuote

TRADIER_QUOTES_URL = "https://api.tradier.com/v1/markets/quotes"
_OCC = re.compile(r"^[A-Z]{1,6}[0-9]{6}[CP][0-9]{8}$")
_STOCK = re.compile(r"^[A-Z][A-Z0-9./]{0,7}$")


def _utc_from_ms(raw):
    if isinstance(raw, bool) or raw is None:
        raise ValueError("missing exchange-side quote timestamp")
    number = float(raw)
    if not isfinite(number) or number <= 0:
        raise ValueError("invalid exchange-side quote timestamp")
    return datetime.fromtimestamp(number / 1000.0, tz=timezone.utc)


def _iex_time(raw):
    if not isinstance(raw, str):
        raise ValueError("missing Alpaca quote timestamp")
    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("naive Alpaca exchange time")
    return stamp.astimezone(timezone.utc)


def alpaca_iex_quote(event, received_at, authenticated=False):
    """Normalize Alpaca v2 IEX quote; never call it consolidated."""
    if not isinstance(event, dict) or event.get("T") != "q":
        raise ValueError("not an IEX quote")
    stamp = _iex_time(event.get("t"))
    quote = MarketQuote("alpaca_iex", AssetClass.STOCK,
                        str(event.get("S", "")),
                        float(event["bp"]), float(event["ap"]),
                        stamp, stamp, received_at,
                        entitlement_verified=authenticated)
    quote.validate()
    return quote


def _tradier_symbol(raw, expected_asset=None):
    if not isinstance(raw, str):
        raise ValueError("invalid symbol")
    symbol = raw.upper()
    if _OCC.fullmatch(symbol):
        kind = AssetClass.OPTION
    elif _STOCK.fullmatch(symbol):
        kind = AssetClass.STOCK
        symbol = symbol.replace("/", ".")
    else:
        raise ValueError("symbol not a supported stock or OCC option")
    if expected_asset and kind != expected_asset:
        raise ValueError("asset classification mismatch")
    return symbol, kind


def tradier_quote(payload, received_at, authenticated_live=False):
    """Normalize a Tradier REST quote (bid_date, ask_date in Unix ms)."""
    if not isinstance(payload, dict):
        raise ValueError("invalid Tradier quote payload")
    symbol, kind = _tradier_symbol(payload.get("symbol"))
    stated_type = str(payload.get("type", "")).lower()
    if stated_type == "option" and kind != AssetClass.OPTION:
        raise ValueError("claimed option with non-option symbol")
    if stated_type in ("stock", "etf") and kind != AssetClass.STOCK:
        raise ValueError("claimed stock with option symbol")
    provider = "tradier_live" if authenticated_live else "tradier_sandbox"
    result = MarketQuote(provider, kind, symbol,
                         float(payload["bid"]), float(payload["ask"]),
                         _utc_from_ms(payload.get("bid_date")),
                         _utc_from_ms(payload.get("ask_date")),
                         received_at, entitlement_verified=authenticated_live)
    result.validate()
    return result


def tradier_stream_quote(payload, received_at, authenticated_live=False):
    """Normalize Tradier websocket/HTTP-stream quote (biddate, askdate)."""
    if not isinstance(payload, dict) or payload.get("type") != "quote":
        raise ValueError("not a Tradier stream quote")
    formatted = {
        "symbol": payload.get("symbol"), "bid": payload.get("bid"),
        "ask": payload.get("ask"), "bid_date": payload.get("biddate"),
        "ask_date": payload.get("askdate"),
    }
    return tradier_quote(formatted, received_at, authenticated_live)


def fetch_tradier_live_quotes(symbols, opener=urlopen, now=None):
    """GET real-time read-only data using a user-owned Tradier live entitlement.

    Fail closed without both explicit read-only activation and a live API token.
    HTTP calls never point to an orders endpoint. No secret is logged or stored.
    """
    if os.environ.get("SF_TRADIER_DATA_ENABLE") != "READ_ONLY_APPROVED":
        raise RuntimeError("Tradier live market data is not enabled")
    token = os.environ.get("TRADIER_LIVE_DATA_TOKEN")
    if not token:
        raise RuntimeError("Tradier live data token is missing locally")
    symbols = list(dict.fromkeys(symbols))
    if not symbols or len(symbols) > 50:
        raise ValueError("request 1-50 distinct symbols")
    requested = []
    for raw in symbols:
        name, _ = _tradier_symbol(raw)
        requested.append(name)
    url = TRADIER_QUOTES_URL + "?" + urlencode({"symbols": ",".join(requested)})
    req = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "SatisfyForge-read-only-feed/0.3",
    }, method="GET")
    with opener(req, timeout=5) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("malformed Tradier response")
    records = payload.get("quotes", {}).get("quote") if isinstance(
        payload.get("quotes"), dict) else None
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list) or not records:
        raise ValueError("Tradier did not return valid quote records")
    received_at = now or datetime.now(timezone.utc)
    output = []
    for record in records:
        parsed = tradier_quote(record, received_at, authenticated_live=True)
        if parsed.symbol not in requested:
            raise ValueError("unexpected symbol in Tradier response")
        output.append(parsed)
    return output


KRAKEN_PUBLIC_BOOK_URL = "https://api.kraken.com/0/public/PreTrade"


def _kraken_utc(raw):
    if not isinstance(raw, str) or not raw:
        raise ValueError("missing Kraken publication timestamp")
    normalized = raw.replace("Z", "+00:00")
    # Python 3.9 rejects nanosecond strings; preserve timestamps to microseconds.
    normalized = re.sub(r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)", r"\1", normalized)
    result = datetime.fromisoformat(normalized)
    if result.tzinfo is None:
        raise ValueError("Kraken quote lacks timezone")
    return result.astimezone(timezone.utc)


def kraken_public_book(payload, received_at, expected_symbol):
    """Normalize first-level prices using each book side's publication timestamp.

    Kraken public data describes Kraken's own crypto venue, NOT a global crypto
    consolidated NBBO; the quality gate marks it RESEARCH_ONLY.
    """
    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("Kraken public book error")
    book = payload.get("result")
    if not isinstance(book, dict) or book.get("symbol") != expected_symbol:
        raise ValueError("Kraken pair mismatch or incomplete book")
    bids, asks = book.get("bids"), book.get("asks")
    if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
        raise ValueError("Kraken book has no two-sided liquidity")
    best_bid = max(bids, key=lambda x: float(x["price"]))
    best_ask = min(asks, key=lambda x: float(x["price"]))
    result = MarketQuote("kraken_public", AssetClass.CRYPTO, expected_symbol,
                         float(best_bid["price"]), float(best_ask["price"]),
                         _kraken_utc(best_bid.get("publication_ts")),
                         _kraken_utc(best_ask.get("publication_ts")),
                         received_at, entitlement_verified=True)
    result.validate()
    return result


def fetch_kraken_public_book(symbol, opener=urlopen, now=None):
    """Free, unauthenticated, read-only Kraken spot order-book snapshot.

    Limited to USD spot research. Never sends a trade or an API key.
    """
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9]{2,12}/USD", symbol):
        raise ValueError("expected USD-denominated crypto pair, e.g. BTC/USD")
    request = Request(KRAKEN_PUBLIC_BOOK_URL + "?" + urlencode({"symbol": symbol}),
                      headers={"Accept": "application/json",
                               "User-Agent": "SatisfyForge-read-only-feed/0.3"},
                      method="GET")
    with opener(request, timeout=5) as response:
        payload = json.load(response)
    return kraken_public_book(payload, now or datetime.now(timezone.utc), symbol)
