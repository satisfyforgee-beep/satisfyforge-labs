"""Read-only Alpaca IEX minute bars. Absolutely no order placement.

Free IEX coverage is partial U.S. equity market data (not consolidated SIP).
An Alpaca PAPER account is enough to obtain PAPER_API_KEY/PAPER_API_SECRET.
"""
from __future__ import annotations
from datetime import datetime, timezone
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
        # Decimal validation and spread checks occur in trading-lab. Do not
        # round away a tight spread or silently replace missing market data.
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
