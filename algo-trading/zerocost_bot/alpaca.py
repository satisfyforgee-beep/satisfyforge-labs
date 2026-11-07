"""Read-only Alpaca IEX minute bars. Absolutely no order placement.

Free IEX coverage is partial U.S. equity market data (not consolidated SIP).
An Alpaca PAPER account is enough to obtain PAPER_API_KEY/PAPER_API_SECRET.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import re
from .engine import Bar

BASE = "https://data.alpaca.markets"
_RFC3339_TIMESTAMP = re.compile(
    r"^(?P<whole>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d+))?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)


def _parse_rfc3339_timestamp(value):
    """Parse provider RFC3339 timestamps on Python 3.9 through current Python.

    Alpaca emits nanosecond precision, while Python 3.9 fromisoformat only
    accepts up to six fractional digits. Truncating to microseconds preserves
    ordering at the runtime precision. A timezone remains mandatory.
    """
    match = _RFC3339_TIMESTAMP.fullmatch(str(value))
    if not match:
        raise ValueError("Expected a timezone-aware RFC3339 timestamp")
    fraction = match.group("fraction")
    normalized = match.group("whole")
    if fraction:
        normalized += "." + fraction[:6]
    zone = match.group("zone")
    normalized += "+00:00" if zone == "Z" else zone
    timestamp = datetime.fromisoformat(normalized)
    if timestamp.tzinfo is None:
        raise ValueError("RFC3339 timestamp must carry timezone")
    return timestamp


def _positive_decimal(value, label):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid option {label}") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError(f"Invalid option {label}")
    return result


def validate_option_snapshot_pages(requested_symbols, pages, now,
                                   *, feed, max_age_seconds=15):
    """Validate a locally captured, complete option-snapshot page chain.

    This function performs no network request. Each captured page must include
    ``request_page_token`` (null on the first request), the provider
    ``snapshots`` mapping, and ``next_page_token``. It fails closed on missing,
    duplicate, cyclic, orphaned, stale, crossed, or malformed data. Alpaca's
    free ``indicative`` feed is always labelled non-executable because its
    trades are delayed and quotes are modified.
    """
    if now.tzinfo is None:
        raise ValueError("Evaluation time must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if not isinstance(max_age_seconds, int) or max_age_seconds <= 0:
        raise ValueError("Quote age limit must be a positive integer")
    if feed not in {"opra", "indicative"}:
        raise ValueError("Unsupported option feed")
    symbols = [str(symbol).upper() for symbol in requested_symbols]
    if not 1 <= len(symbols) <= 100 or len(set(symbols)) != len(symbols):
        raise ValueError("Expected 1-100 unique option symbols")
    if any(not re.fullmatch(r"[A-Z0-9]{15,32}", symbol) for symbol in symbols):
        raise ValueError("Malformed option symbol")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Option snapshot pages are required")

    by_token = {}
    for page in pages:
        if not isinstance(page, dict) or "request_page_token" not in page:
            raise ValueError("Malformed option snapshot page")
        token = page["request_page_token"]
        if token is not None and (not isinstance(token, str) or not token):
            raise ValueError("Invalid option request page token")
        if token in by_token:
            raise ValueError("Duplicate option request page token")
        by_token[token] = page

    requested = set(symbols)
    seen = set()
    rows = []
    token = None
    visited = set()
    while True:
        if token in visited:
            raise ValueError("Option snapshot page-token cycle")
        visited.add(token)
        page = by_token.get(token)
        if page is None:
            raise ValueError("Incomplete option snapshot page chain")
        snapshots = page.get("snapshots")
        if not isinstance(snapshots, dict):
            raise ValueError("Malformed option snapshot mapping")
        for raw_symbol, snapshot in snapshots.items():
            symbol = str(raw_symbol).upper()
            if symbol not in requested:
                raise ValueError("Unexpected option symbol")
            if symbol in seen:
                raise ValueError("Duplicate option snapshot")
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("latestQuote"), dict):
                raise ValueError("Missing option latest quote")
            quote = snapshot["latestQuote"]
            bid = _positive_decimal(quote.get("bp"), "bid")
            ask = _positive_decimal(quote.get("ap"), "ask")
            if ask < bid:
                raise ValueError("Crossed option quote")
            asof = _parse_rfc3339_timestamp(quote.get("t")).astimezone(timezone.utc)
            age = (now - asof).total_seconds()
            if age < 0 or age > max_age_seconds:
                raise ValueError("Option quote is stale or from the future")
            seen.add(symbol)
            rows.append({
                "symbol": symbol, "bid": str(bid), "ask": str(ask),
                "asof": asof, "source": f"ALPACA_{feed.upper()}",
                "delayed_or_modified": feed == "indicative",
                "execution_eligible": feed == "opra",
            })
        next_token = page.get("next_page_token")
        if next_token is None:
            break
        if not isinstance(next_token, str) or not next_token:
            raise ValueError("Invalid option next page token")
        token = next_token

    if visited != set(by_token):
        raise ValueError("Orphaned option snapshot page")
    if seen != requested:
        raise ValueError("Missing requested option snapshots")
    return sorted(rows, key=lambda row: row["symbol"])


def latest_equity_quotes(symbols, api_key=None, api_secret=None, transport=None):
    """Fetch read-only IEX top-of-book equity quotes, never orders.

    This is single-exchange market data, not consolidated SIP. A caller must
    independently reject stale, crossed, delayed or wide-spread quotes.
    `transport` is an optional test-only callable accepting a urllib Request.
    """
    key = api_key or os.getenv("ALPACA_PAPER_KEY")
    secret = api_secret or os.getenv("ALPACA_PAPER_SECRET")
    if not key or not secret:
        raise RuntimeError("Missing Alpaca paper data credentials")
    names = sorted(set(str(s).upper() for s in symbols))
    if not 1 <= len(names) <= 10 or any(not re.fullmatch(r"[A-Z]{1,6}", s) for s in names):
        raise ValueError("Expected 1–10 simple U.S. equity symbols")
    url = BASE + "/v2/stocks/quotes/latest?" + urlencode({"symbols": ",".join(names), "feed": "iex"})
    request = Request(url, headers={"APCA-API-KEY-ID": key,
                                    "APCA-API-SECRET-KEY": secret,
                                    "Accept": "application/json"})
    if transport is None:
        with urlopen(request, timeout=8) as response:
            payload = json.load(response)
    else:
        payload = transport(request)
    quotes = payload.get("quotes", {})
    output = []
    for symbol in names:
        row = quotes.get(symbol)
        if not row:
            continue
        bid, ask = str(row.get("bp", "0")), str(row.get("ap", "0"))
        timestamp = _parse_rfc3339_timestamp(row["t"])
        if timestamp.tzinfo is None:
            raise ValueError("IEX quote timestamp must carry timezone")
        output.append({"symbol": symbol, "bid": bid, "ask": ask,
                       "asof": timestamp, "source": "ALPACA_IEX", "delayed": False})
    return output


def latest_bars(symbols, api_key=None, api_secret=None):
    key = api_key or os.getenv("ALPACA_PAPER_KEY")
    secret = api_secret or os.getenv("ALPACA_PAPER_SECRET")
    if not key or not secret:
        raise RuntimeError("Missing Alpaca paper API keys; use --demo or --replay offline")
    symbols = sorted(set(s.upper() for s in symbols))
    if not symbols or len(symbols) > 10:
        raise ValueError("expected 1-10 symbols")
    url = BASE + "/v2/stocks/bars/latest?" + urlencode({"symbols": ",".join(symbols), "feed": "iex"})
    request = Request(url, headers={"APCA-API-KEY-ID": key,
                                    "APCA-API-SECRET-KEY": secret,
                                    "Accept": "application/json"})
    with urlopen(request, timeout=8) as response:
        data = json.load(response)
    out = []
    for symbol, row in data.get("bars", {}).items():
        dt = _parse_rfc3339_timestamp(row["t"])
        out.append(Bar(symbol, dt, float(row["o"]), float(row["h"]),
                       float(row["l"]), float(row["c"]), int(row["v"])))
    return out


def get_historical_bars(symbol, start, end, api_key=None, api_secret=None):
    key = api_key or os.getenv("ALPACA_PAPER_KEY")
    secret = api_secret or os.getenv("ALPACA_PAPER_SECRET")
    if not key or not secret:
        raise RuntimeError("Missing Alpaca paper API keys")
    symbol = symbol.upper()
    if not symbol.isalpha() or len(symbol) > 6:
        raise ValueError("invalid ticker")
    bars = []
    page = None
    while True:
        params = {"timeframe":"1Min", "start":start, "end":end,
                  "feed":"iex", "limit":"1000", "adjustment":"split"}
        if page:
            params["page_token"] = page
        url = BASE + "/v2/stocks/" + symbol + "/bars?" + urlencode(params)
        request = Request(url, headers={"APCA-API-KEY-ID":key,
                                        "APCA-API-SECRET-KEY":secret,
                                        "Accept":"application/json"})
        with urlopen(request, timeout=10) as response:
            result=json.load(response)
        for row in result.get("bars", []):
            dt=_parse_rfc3339_timestamp(row["t"])
            bars.append(Bar(symbol,dt,float(row["o"]),float(row["h"]),
                            float(row["l"]),float(row["c"]),int(row["v"])))
        page=result.get("next_page_token")
        if not page:
            break
    return bars
