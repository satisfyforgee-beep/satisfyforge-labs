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
from .engine import Bar

BASE = "https://data.alpaca.markets"


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
        dt = datetime.fromisoformat(row["t"].replace("Z", "+00:00"))
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
            dt=datetime.fromisoformat(row["t"].replace("Z","+00:00"))
            bars.append(Bar(symbol,dt,float(row["o"]),float(row["h"]),
                            float(row["l"]),float(row["c"]),int(row["v"])))
        page=result.get("next_page_token")
        if not page:
            break
    return bars
