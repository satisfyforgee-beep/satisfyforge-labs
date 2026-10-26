"""Strictly historical stock/option CASH-ONLY virtual practice from Tradier Sandbox.

GET-only delayed market history. NO broker paper orders and NO real trades.
For equities, one-share long control buys near 10:00 ET and sells with
conservative modeled stops/targets or at the historical close. For options,
a deliberately non-predictive, long-one-contract open-to-close control
replays selected historical daily bars; it does not assume daily OHLC is
executable bid/ask. Entry/exit costs include estimated friction.
"""
from __future__ import annotations

from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import json
import os
import re

from .tradier_paper import SANDBOX_HOST

_ET = ZoneInfo("America/New_York")
D = Decimal
PENNY = D("0.01")
STOCK_NAMES = ("F", "AAL", "CLF")
OCC_NAMES = ("AAL261106P00011500", "F261106C00013000")
_ABC = re.compile(r"^[A-Z]{1,6}$")
_OCC = re.compile(r"^[A-Z]{1,6}[0-9]{6}[CP][0-9]{8}$")
_DAY = date(2026, 10, 26)


def _round(n):
    return n.quantize(PENNY, rounding=ROUND_HALF_UP)


def _number(raw, *, allow_zero=False):
    try:
        d = Decimal(str(raw))
    except (TypeError, ValueError, ArithmeticError):
        raise ValueError("invalid OHLC number") from None
    if not d.is_finite() or (d < 0 if allow_zero else d <= 0):
        raise ValueError("invalid OHLC number")
    return d


def sandbox_readonly(path, query, *, token, opener=urlopen):
    if path not in ("/markets/timesales", "/markets/history"):
        raise ValueError("unapproved read-only market-data endpoint")
    if not isinstance(token, str) or not token:
        raise ValueError("missing SANDBOX credential")
    req = Request(
        SANDBOX_HOST + path + "?" + urlencode(query),
        method="GET",
        headers={"Accept": "application/json",
                 "Authorization": "Bearer " + token,
                 "User-Agent": "SatisfyForge-virtual-replay/1.0"},
    )
    with opener(req, timeout=9) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("invalid market response")
    return obj


def _prices(obj, *, zero=False):
    if not isinstance(obj, dict):
        raise ValueError("malformed price bar")
    op = _number(obj.get("open"), allow_zero=zero)
    hi = _number(obj.get("high"), allow_zero=zero)
    lo = _number(obj.get("low"), allow_zero=zero)
    cl = _number(obj.get("close"), allow_zero=zero)
    if hi < max(op, cl, lo) or lo > min(op, cl):
        raise ValueError("bad high/low bar geometry")
    return op, hi, lo, cl


def stock_bars(symbol, *, token, opener=urlopen):
    if symbol not in STOCK_NAMES:
        raise ValueError("unsupported trial stock")
    payload = sandbox_readonly("/markets/timesales", {
        "symbol": symbol, "interval": "5min",
        "start": "2026-10-26 09:30", "end": "2026-10-26 16:00",
        "session_filter": "open",
    }, token=token, opener=opener)
    section = payload.get("series")
    if not isinstance(section, dict):
        raise ValueError("missing timesales")
    rows = section.get("data")
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or len(rows) < 60:
        raise ValueError("incomplete historical stock market session")
    results = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid timesales item")
        raw = row.get("time")
        if not isinstance(raw, str):
            raise ValueError("unparseable local session time")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_ET)
        dt = dt.astimezone(_ET)
        if (dt.date() != _DAY or
                not (9 * 60 + 30 <= dt.hour * 60 + dt.minute < 16 * 60) or
                dt.minute % 5 != 0):
            raise ValueError("outside confirmed regular stock session")
        op, hi, lo, cl = _prices(row)
        volume = row.get("volume")
        if type(volume) is not int or not 0 <= volume <= 1_000_000_000_000:
            raise ValueError("invalid historical stock volume")
        results.append((dt, op, hi, lo, cl, volume))
    if len({r[0] for r in results}) != len(results):
        raise ValueError("duplicate timesales bars")
    results.sort()
    if results[-1][0].hour != 15 or results[-1][0].minute != 55:
        raise ValueError("last 5-minute market interval missing")
    return results


def option_days(contract, *, token, opener=urlopen):
    if contract not in OCC_NAMES or not _OCC.fullmatch(contract):
        raise ValueError("unsupported trial option")
    payload = sandbox_readonly("/markets/history", {
        "symbol": contract, "interval": "daily",
        "start": "2026-10-01", "end": "2026-10-26",
    }, token=token, opener=opener)
    section = payload.get("history")
    if not isinstance(section, dict):
        raise ValueError("missing option history")
    rows = section.get("day")
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or len(rows) < 8:
        raise ValueError("too few historical option sessions")
    results = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("bad option history item")
        dt = date.fromisoformat(str(row.get("date")))
        if not date(2026, 10, 1) <= dt <= _DAY:
            raise ValueError("option data outside precommitted history")
        op, hi, lo, cl = _prices(row, zero=True)
        results.append((dt, op, hi, lo, cl))
    if len({r[0] for r in results}) != len(results):
        raise ValueError("duplicate option historical bar")
    return sorted(results)


def stock_control(data_by_symbol):
    cash = D("150.00")
    events = []
    for symbol in STOCK_NAMES:
        rows = data_by_symbol[symbol]
        opens = [(i, row) for i, row in enumerate(rows)
                 if row[0].hour == 10 and row[0].minute == 0]
        if len(opens) != 1:
            raise ValueError("historical 10:00 ET stock entry bar missing")
        index, entry = opens[0]
        buy = entry[1] + PENNY
        fee = D("0.01")
        debit = _round(buy + fee)
        if debit > 30 or debit > cash:
            raise ValueError("control stock debit exceeds virtual budget")
        cash -= debit
        stop, target = buy * D("0.98"), buy * D("1.035")
        sold = None
        for j in range(index, len(rows)):
            t, op, hi, lo, cl, vol = rows[j]
            if op <= stop:
                reference, reason = op, "gap_stop"
            elif lo <= stop:
                reference, reason = stop, "stop"
            elif op >= target:
                reference, reason = target, "target_capped"
            elif hi >= target:
                reference, reason = target, "target"
            elif j == len(rows) - 1:
                reference, reason = cl, "closing_interval"
            else:
                continue
            proceeds = max(D("0"), reference - PENNY - fee)
            realized = proceeds - debit
            cash += proceeds
            sold = {
                "asset": "stock", "symbol": symbol, "quantity": 1,
                "entry_timestamp_et": entry[0].isoformat(),
                "exit_timestamp_et": t.isoformat(),
                "virtual_entry_ask_model": str(_round(buy)),
                "virtual_exit_bid_model": str(_round(max(D(0), reference - PENNY))),
                "virtual_debit": str(debit), "virtual_net_proceeds": str(_round(proceeds)),
                "realized_pnl_after_model_costs": str(_round(realized)),
                "exit_reason": reason, "model_not_broker_fill": True,
            }
            break
        if sold is None:
            raise ValueError("no historically observed virtual exit")
        events.append(sold)
    return {
        "mode": "STOCK_HISTORICAL_VIRTUAL_EXECUTION_CONTROL",
        "starting_cash": "150.00", "ending_cash": str(_round(cash)),
        "net_pnl_after_model_costs": str(_round(cash - 150)),
        "virtual_completed_roundtrips": len(events),
        "winners": sum(D(x["realized_pnl_after_model_costs"]) > 0 for x in events),
        "events": events, "broker_orders_sent": 0,
    }


def option_control(data_by_contract):
    # Build candidates before seeing outcomes. Then process in calendar order,
    # never recycle a same-day sale to finance another CASH-only entry.
    candidates = []
    for contract in OCC_NAMES:
        rows = data_by_contract[contract]
        expiry = date(2000 + int(contract[-15:-13]), int(contract[-13:-11]),
                      int(contract[-11:-9]))
        for i, (session, op, hi, lo, cl) in enumerate(rows):
            if i < 2 or i % 4 != 2 or (expiry - session).days < 7 or op <= 0:
                continue
            candidates.append((session, contract, expiry, op, cl))
    candidates.sort()
    cash = D("150.00")
    unsettled = []
    events = []
    for session, contract, expiry, op, cl in candidates:
        # T+1 business-day model is approximated by a *later observed session*.
        # No real clearing status is known for this historical counterfactual.
        ready = [value for sold_day, value in unsettled if sold_day < session]
        if ready:
            cash += sum(ready, D(0))
        unsettled = [(d, v) for d, v in unsettled if d >= session]
        premium_buy = op + PENNY
        debit = _round(premium_buy * 100 + D("0.65"))
        if debit > D("30.00") or debit > cash:
            continue
        cash -= debit
        premium_sell = max(D(0), cl - PENNY)
        gross = premium_sell * 100
        proceeds = max(D(0), gross - D("0.65"))
        unsettled.append((session, proceeds))
        pnl = proceeds - debit
        events.append({
            "asset": "long_option", "contract": contract,
            "expiration": expiry.isoformat(), "session": session.isoformat(),
            "virtual_contracts": 1, "multiplier": 100,
            "opening_premium_reference": str(op),
            "closing_premium_reference": str(cl),
            "modeled_debit_with_fee": str(debit),
            "modeled_proceeds_after_fee": str(_round(proceeds)),
            "realized_pnl_after_model_costs": str(_round(pnl)),
            "model_not_broker_fill": True,
            "no_overnight_assignment_exposure_in_this_replay": True,
        })
    final_cash = cash + sum((v for _, v in unsettled), D(0))
    return {
        "mode": "OPTION_DAILY_HISTORICAL_CONTROL_NO_ACTUAL_BID_ASK",
        "starting_cash": "150.00",
        "end_cash_after_hypothetical_settlement": str(_round(final_cash)),
        "end_cash_settled_at_final_observation": str(_round(cash)),
        "unsettled_sale_proceeds_at_final_observation": str(
            _round(sum((v for _, v in unsettled), D(0)))),
        "net_pnl_after_model_costs": str(_round(final_cash - 150)),
        "virtual_completed_roundtrips": len(events),
        "winners": sum(D(x["realized_pnl_after_model_costs"]) > 0 for x in events),
        "events": events, "broker_orders_sent": 0,
    }
