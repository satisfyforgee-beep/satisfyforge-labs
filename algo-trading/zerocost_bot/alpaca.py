"""Read-only Alpaca IEX minute bars. Absolutely no order placement.

Free IEX coverage is partial U.S. equity market data (not consolidated SIP).
An Alpaca PAPER account is enough to obtain PAPER_API_KEY/PAPER_API_SECRET.
"""
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os
import re
from typing import Optional
from zoneinfo import ZoneInfo
from .engine import Bar

BASE = "https://data.alpaca.markets"
_RFC3339_TIMESTAMP = re.compile(
    r"^(?P<whole>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d+))?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)
_NEW_YORK = ZoneInfo("America/New_York")


def classify_overnight_market_data(
    *,
    observed_at: datetime,
    data_asof: datetime,
    feed: str,
    data_kind: str,
    trade_date: Optional[date],
    market_calendar_verified: bool,
    trade_date_is_holiday: Optional[bool],
    account_overnight_enabled: Optional[bool],
    account_data_entitlement_verified: Optional[bool],
    asset_overnight_tradable: Optional[bool],
    asset_overnight_halted: Optional[bool],
    quote_is_indicative: Optional[bool] = None,
    delayed_minutes: Optional[int] = None,
    max_age_seconds: int = 15,
):
    """Classify Alpaca overnight data for offline research, never execution.

    Alpaca's free overnight feed has different provenance by endpoint: latest
    quotes are real-time *indicative* quotes, while trades and historical
    BOATS data are delayed.  Neither is executable-price or fill evidence.
    This pure function validates session/trade-date/account/asset provenance
    so downstream research cannot silently promote those observations into an
    order or a hypothetical broker fill.

    The returned execution flags are intentionally immutable safety policy:
    this helper has no network, broker, journal, or order side effects.
    """
    blockers = []
    if observed_at.tzinfo is None or data_asof.tzinfo is None:
        blockers.append("TIMEZONE_REQUIRED")
        local = None
    else:
        local = observed_at.astimezone(_NEW_YORK)

    expected_trade_date = None
    session_open = False
    if local is not None:
        local_clock = local.timetz().replace(tzinfo=None)
        if local_clock >= time(20, 0):
            expected_trade_date = local.date() + timedelta(days=1)
            session_open = local.weekday() in {6, 0, 1, 2, 3}
        elif local_clock < time(4, 0):
            expected_trade_date = local.date()
            session_open = local.weekday() in {0, 1, 2, 3, 4}
        if not session_open:
            blockers.append("OUTSIDE_OVERNIGHT_SESSION")

    if trade_date is None or trade_date != expected_trade_date:
        blockers.append("TRADE_DATE_UNVERIFIED")
    if market_calendar_verified is not True or trade_date_is_holiday is None:
        blockers.append("MARKET_CALENDAR_UNVERIFIED")
    elif trade_date_is_holiday:
        blockers.append("MARKET_HOLIDAY")
    if account_overnight_enabled is not True:
        blockers.append("ACCOUNT_OVERNIGHT_UNVERIFIED")
    if account_data_entitlement_verified is not True:
        blockers.append("DATA_ENTITLEMENT_UNVERIFIED")
    if asset_overnight_tradable is not True:
        blockers.append("ASSET_NOT_OVERNIGHT_TRADABLE")
    if asset_overnight_halted is not False:
        blockers.append("ASSET_HALT_UNVERIFIED")

    feed_name = str(feed).lower()
    kind = str(data_kind).lower()
    provenance = None
    allowed_age_seconds = max_age_seconds
    if feed_name == "overnight" and kind == "quote":
        provenance = "REALTIME_INDICATIVE_QUOTE"
        if quote_is_indicative is not True:
            blockers.append("INDICATIVE_PROVENANCE_UNVERIFIED")
    elif feed_name in {"overnight", "boats"} and kind == "trade":
        provenance = "DELAYED_TRADE"
        if delayed_minutes is None or delayed_minutes < 15:
            blockers.append("DELAY_PROVENANCE_UNVERIFIED")
        else:
            # The provider-documented delay is provenance, not unexplained
            # staleness. Still allow only a small capture-lag tolerance beyond
            # that delay, and never promote the observation to execution data.
            allowed_age_seconds += delayed_minutes * 60
    else:
        blockers.append("UNSUPPORTED_DATA_PROVENANCE")

    if observed_at.tzinfo is not None and data_asof.tzinfo is not None:
        age = (observed_at.astimezone(timezone.utc) -
               data_asof.astimezone(timezone.utc)).total_seconds()
        if age < 0:
            blockers.append("FUTURE_DATA")
        elif age > allowed_age_seconds:
            blockers.append("STALE_DATA")

    research_usable = not blockers
    return {
        "state": "RESEARCH_ONLY" if research_usable else "HALT",
        "research_usable": research_usable,
        "provenance": provenance,
        "expected_trade_date": (expected_trade_date.isoformat()
                                if expected_trade_date else None),
        "blockers": tuple(blockers),
        "broker_submission_enabled": False,
        "execution_price_usable": False,
        "fill_evidence": False,
    }


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
