"""Strict read-only, provenance-aware SatisfyForge trading research health.

Reconciles the local *virtual* crypto ledger with the scheduled check log.
Distinguishes simulated liquidation from realized and settled cash.
Checks the stock QA log separately. No market access, HTTP or broker orders.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote
from zoneinfo import ZoneInfo
import json
import sqlite3

from .paper_capital import PaperCapital, CapitalBlocked

ET = ZoneInfo("America/New_York")
MAX_LOG_SIZE = 320000
VALID_STATES = frozenset({
    "CHECK_COMPLETE", "CHECK_HALTED", "TRIAL_COMPLETED_NO_NEW_QUOTES_OR_BUYS"
})


def _private_file(path, *, max_size=None):
    p = Path(path)
    if not p.is_file() or p.is_symlink():
        raise ValueError("required private evidence is missing or unsafe")
    if max_size and p.stat().st_size > max_size:
        raise ValueError("private monitoring log exceeds expected size")
    return p


def get_virtual_snapshot(path):
    """RO SQLite only: never initialize an empty live or virtual database."""
    p = _private_file(path)
    uri = "file:" + quote(str(p.absolute()), safe="/") + "?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=3) as con:
            con.execute("PRAGMA query_only=ON")
            config = dict(con.execute("SELECT key,value FROM capital_config"))
            if (config.get("opening_cash") != "150.00" or
                    config.get("max_order") != "30.00" or
                    config.get("max_reservations") != "5"):
                raise ValueError("unexpected virtual trial bankroll policy")
            rows = con.execute(
                "SELECT event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at "
                "FROM capital_events ORDER BY sequence"
            ).fetchall()
    except (sqlite3.Error, CapitalBlocked) as exc:
        raise ValueError("unreadable or contradictory virtual capital journal") from exc
    policy = SimpleNamespace(
        opening_cash=Decimal("150.00"), max_order=Decimal("30.00"),
        max_reservations=5,
    )
    try:
        snapshot = PaperCapital._reduce(policy, rows)
    except (CapitalBlocked, ValueError, TypeError) as exc:
        raise ValueError("invalid virtual capital journal events") from exc
    buys = sum(r[1] == "buy" for r in rows)
    sells = sum(r[1] == "sell" for r in rows)
    if not (buys == 3 and 0 <= sells <= 3 and
            len(snapshot["positions"]) + sells == 3 and
            all(p["asset"] == "crypto" and p["symbol"] in
                ("BTC/USD", "ETH/USD", "SOL/USD")
                for p in snapshot["positions"])):
        raise ValueError("virtual position count does not reconcile")
    return {"snapshot": snapshot, "virtual_buys": buys, "virtual_sells": sells}


def parse_monitor_log(path, now):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    p = _private_file(path, max_size=MAX_LOG_SIZE)
    try:
        records = [json.loads(line) for line in p.read_text().splitlines()]
    except (UnicodeError, ValueError) as exc:
        raise ValueError("corrupt virtual status log") from exc
    if not records:
        raise ValueError("no virtual monitor records")
    observed = []
    for x in records:
        if (not isinstance(x, dict) or
                x.get("mode") != "OFFLINE_FORWARD_VIRTUAL_CRYPTO_NOT_BROKER_FILLED" or
                x.get("actual_broker_orders") != 0 or
                x.get("actual_money_trades") != 0 or
                x.get("state") not in VALID_STATES):
            raise ValueError("unexpected or conflicting monitoring record")
        try:
            dt = datetime.fromisoformat(x["utc"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("monitor timestamp unavailable") from exc
        if dt.tzinfo is None or dt > now + timedelta(seconds=30):
            raise ValueError("monitor clock mismatch")
        observed.append((dt.astimezone(timezone.utc), x))
    if any(observed[i][0] > observed[i + 1][0] for i in range(len(observed)-1)):
        raise ValueError("monitor timestamps not chronological")
    last, current = observed[-1]
    age = (now.astimezone(timezone.utc) - last).total_seconds()
    healthy = age <= 2700 and current["state"] in (
        "CHECK_COMPLETE", "TRIAL_COMPLETED_NO_NEW_QUOTES_OR_BUYS"
    )
    # A snapshot is not guaranteed to have been refreshed 15m before
    # display. Stale health is explicit, never a substitute for current quote.
    today_et = now.astimezone(ET).date()
    recent = [x for dt, x in observed if dt.astimezone(ET).date() == today_et]
    good_recent = [x for x in recent if x.get("state") == "CHECK_COMPLETE"]
    estimates = []
    for x in good_recent:
        try:
            v = Decimal(str(x["estimated_virtual_liquidation"]))
            if v.is_finite() and v >= 0:
                estimates.append(v)
        except (KeyError, TypeError, ValueError):
            continue
    return {
        "monitor_health": "HEALTHY_RECENT_CHECK" if healthy else "HALTED_OR_STALE",
        "latest_state": current["state"],
        "latest_check_utc": last.isoformat(),
        "minutes_since_latest_check": round(max(0, age) / 60, 1),
        "record_count_total": len(records),
        "checks_today_ny": len(recent),
        "estimated_value_range_today_ny": (
            {"min": str(min(estimates)), "max": str(max(estimates))}
            if estimates else None),
        "latest_estimated_liquidation_value": (
            current.get("estimated_virtual_liquidation")
            if current.get("state") != "CHECK_HALTED" else None),
        "latest_realized_virtual_pnl_from_log": (
            current.get("virtual_realized_pnl")
            if current.get("state") != "CHECK_HALTED" else None),
        "latest_open_virtual_positions": (
            current.get("open_virtual_positions")
            if current.get("state") != "CHECK_HALTED" else None),
    }


def parse_stock_qa_log(path):
    """Separate control experiment, not fungible with the crypto bankroll."""
    p = Path(path)
    if not p.is_file() or p.is_symlink():
        return {"status": "LOG_UNAVAILABLE", "merged_crypto_profits": False}
    lines = p.read_text()[-20000:].splitlines()
    if not lines:
        return {"status": "NO_STOCK_QA_EVENTS", "merged_crypto_profits": False}
    try:
        latest = json.loads(lines[-1])
    except ValueError:
        return {"status": "MALFORMED_STOCK_QA_LOG", "merged_crypto_profits": False}
    state = latest.get("state")
    if not isinstance(state, str) or len(state) > 80:
        state = "UNKNOWN"
    return {
        "status": state,
        "broker_orders_sent_reported": latest.get("broker_orders_sent")
        if latest.get("broker_orders_sent") == 0 else "UNKNOWN",
        "merged_crypto_profits": False,
        "note": "Separate stock-only virtual experiment, not paper broker performance",
    }


def build_status(private_dir, *, now):
    root = Path(private_dir)
    if root.is_symlink():
        raise ValueError("trading directory symlink denied")
    book = get_virtual_snapshot(root / "crypto_virtual_forward.sqlite3")
    clock = parse_monitor_log(root / "crypto_virtual_monitor.jsonl", now)
    stock = parse_stock_qa_log(root / "forward_qa_stdout.log")
    snapshot = book["snapshot"]
    if clock["latest_state"] != "CHECK_HALTED":
        log_positions = clock["latest_open_virtual_positions"]
        log_pnl = clock["latest_realized_virtual_pnl_from_log"]
        # A manual exit can update SQLite before the next scheduled log.
        # Never report an old log as current authoritative profit.
        try:
            realized_matches = (Decimal(str(log_pnl)) ==
                                Decimal(snapshot["realized_net_pnl"]))
        except (ValueError, TypeError):
            realized_matches = False
        if (type(log_positions) is not int or
                log_positions != len(snapshot["positions"]) or
                not realized_matches):
            clock["monitor_health"] = "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE"
    return {
        "mode": "PRIVATE_READ_ONLY_VIRTUAL_TRADING_STATUS",
        "checked_at_utc": now.astimezone(timezone.utc).isoformat(),
        "crypto_monitor": clock,
        "crypto_virtual_account": {
            "opening_cash": snapshot["opening_cash"],
            "current_settled_virtual_cash": snapshot["settled_cash"],
            "realized_virtual_pnl": snapshot["realized_net_pnl"],
            "unsettled_virtual_sale_proceeds": snapshot["unsettled_sale_proceeds"],
            "open_positions": [
                {"asset": x["asset"], "symbol": x["symbol"],
                 "quantity": x["quantity"],
                 "remaining_book_cost": x["remaining_book_cost"]}
                for x in snapshot["positions"]],
            "virtual_buys": book["virtual_buys"],
            "virtual_sells": book["virtual_sells"],
        },
        "stock_virtual_qa": stock,
        "known_blockers": [
            "Historical Tradier SOFI protective exits not independently reconciled",
            "No verified broker-paper fills for crypto/options",
            "No tested profitable multi-asset strategy",
        ],
        "broker_orders_placed_by_this_report": 0,
        "real_money_orders_placed_by_this_report": 0,
    }
