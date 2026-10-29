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


def _stock_amount(value, label):
    try:
        amount = Decimal(str(value))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid stock virtual " + label) from exc
    if not amount.is_finite() or amount != amount.quantize(Decimal("0.01")):
        raise ValueError("invalid stock virtual " + label)
    return amount


def _aware_iso(value, label):
    if not isinstance(value, str):
        raise ValueError("missing stock virtual " + label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid stock virtual " + label) from exc
    if parsed.tzinfo is None:
        raise ValueError("naive stock virtual " + label)
    return parsed.astimezone(timezone.utc)


def get_stock_virtual_snapshot(path):
    """Reconcile the bounded stock JSON journal without importing an order route."""
    p = _private_file(path, max_size=128000)
    try:
        book = json.loads(p.read_text())
    except (UnicodeError, ValueError) as exc:
        raise ValueError("corrupt stock virtual journal") from exc
    if (not isinstance(book, dict) or set(book) != {
            "version", "initial_cash", "cash", "entries", "positions", "events"
        } or book["version"] != 1 or book["initial_cash"] != "150.00"):
        raise ValueError("unexpected stock virtual journal schema")
    cash = _stock_amount(book["cash"], "cash")
    if cash < 0 or cash > Decimal("300.00"):
        raise ValueError("stock virtual cash outside policy")
    if (type(book["entries"]) is not int or not 0 <= book["entries"] <= 5 or
            not isinstance(book["positions"], dict) or len(book["positions"]) > 5 or
            not isinstance(book["events"], list) or len(book["events"]) > 10):
        raise ValueError("stock virtual inventory outside bounded pilot")

    active, seen = {}, set()
    reconstructed_cash = Decimal("150.00")
    realized = Decimal("0.00")
    buys = sells = 0
    latest_event = None
    for event in book["events"]:
        if not isinstance(event, dict) or event.get("action") not in ("BUY", "SELL"):
            raise ValueError("invalid stock virtual event")
        symbol = event.get("symbol")
        if (not isinstance(symbol, str) or not symbol.isalpha() or
                not symbol.isupper() or len(symbol) > 6 or
                event.get("quantity") != 1 or
                event.get("simulated_not_broker_fill") is not True or
                _stock_amount(event.get("fee"), "fee") != Decimal("0.01")):
            raise ValueError("stock virtual event violates pilot policy")
        checked = _aware_iso(event.get("checked_at"), "checked_at")
        quoted = _aware_iso(event.get("quote_at"), "quote_at")
        if quoted > checked + timedelta(seconds=30):
            raise ValueError("stock virtual quote occurs after check")
        latest_event = checked if latest_event is None else max(latest_event, checked)
        price = _stock_amount(event.get("virtual_price"), "price")
        if price <= 0:
            raise ValueError("nonpositive stock virtual price")
        if event["action"] == "BUY":
            debit = _stock_amount(event.get("virtual_debit"), "debit")
            if (symbol in seen or debit != price + Decimal("0.01") or
                    debit > Decimal("30.00")):
                raise ValueError("duplicate or over-cap stock virtual buy")
            if event.get("policy") != "spread_liquidity_execution_QA_not_directional_signal":
                raise ValueError("unexpected stock virtual selection policy")
            seen.add(symbol)
            active[symbol] = debit
            reconstructed_cash -= debit
            buys += 1
        else:
            if symbol not in active:
                raise ValueError("stock virtual sell lacks matching position")
            if event.get("reason") not in ("STOP", "TARGET", "SESSION_END"):
                raise ValueError("unsupported stock virtual exit reason")
            proceeds = price - Decimal("0.01")
            pnl = _stock_amount(event.get("realized_pnl"), "realized pnl")
            if proceeds <= 0 or pnl != proceeds - active[symbol]:
                raise ValueError("stock virtual sale does not reconcile")
            reconstructed_cash += proceeds
            realized += pnl
            del active[symbol]
            sells += 1

    if (buys != book["entries"] or buys != sells + len(book["positions"]) or
            reconstructed_cash != cash or set(active) != set(book["positions"])):
        raise ValueError("stock virtual journal counts or cash do not reconcile")
    positions = []
    for symbol, position in sorted(book["positions"].items()):
        if (not isinstance(position, dict) or set(position) != {
                "quantity", "basis", "entry_quote_at", "stop_bid", "target_bid"
            } or position["quantity"] != 1 or
                _stock_amount(position["basis"], "position basis") != active[symbol] or
                _stock_amount(position["stop_bid"], "stop") <= 0 or
                _stock_amount(position["target_bid"], "target") <= 0):
            raise ValueError("stock virtual position does not reconcile")
        _aware_iso(position["entry_quote_at"], "position entry quote")
        positions.append({
            "symbol": symbol, "quantity": 1, "basis": position["basis"],
            "stop_bid": position["stop_bid"], "target_bid": position["target_bid"],
        })
    return {
        "opening_virtual_cash": "150.00",
        "current_virtual_cash": str(cash),
        "realized_virtual_pnl": str(realized),
        "entries_lifetime": buys,
        "virtual_sells": sells,
        "entry_cap_reached": buys == 5,
        "open_positions": positions,
        "latest_journal_event_utc": latest_event.isoformat() if latest_event else None,
        "journal_modified_utc": datetime.fromtimestamp(
            p.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def parse_stock_qa_log(path):
    """Latest stock control record; journal remains accounting authority."""
    p = _private_file(path, max_size=MAX_LOG_SIZE)
    try:
        lines = p.read_text()[-20000:].splitlines()
    except UnicodeError as exc:
        raise ValueError("unreadable stock QA log") from exc
    if not lines:
        raise ValueError("no stock QA events")
    try:
        latest = json.loads(lines[-1])
    except ValueError as exc:
        raise ValueError("malformed stock QA log") from exc
    allowed = {
        "VIRTUAL_FORWARD_STEP", "OUTSIDE_PAPER_SESSION",
        "MARKET_CLOSED_OR_UNVERIFIED", "TRIAL_COMPLETE",
    }
    if (not isinstance(latest, dict) or latest.get("state") not in allowed or
            latest.get("broker_orders_sent") != 0):
        raise ValueError("unexpected stock QA log record")
    return {
        "latest_state": latest["state"],
        "broker_orders_sent_reported": 0,
        "entries_total_from_log": latest.get("entries_total"),
        "positions_open_from_log": latest.get("positions_open"),
        "cash_virtual_from_log": latest.get("cash_virtual"),
        "realized_pnl_virtual_from_log": latest.get("realized_pnl_virtual"),
        "latest_liquidation_equity_virtual_est": latest.get(
            "liquidation_equity_virtual_est"),
        "latest_net_pnl_virtual_est": latest.get("net_pnl_virtual_est"),
        "log_modified_utc": datetime.fromtimestamp(
            p.stat().st_mtime, tz=timezone.utc).isoformat(),
    }


def reconcile_stock_status(book, log, now):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    modified = datetime.fromisoformat(book["journal_modified_utc"])
    age = (now.astimezone(timezone.utc) - modified).total_seconds()
    if age < -30:
        raise ValueError("stock journal clock mismatch")
    health = "HEALTHY_RECONCILED_RECENT_CHECK" if age <= 2700 else "HALTED_OR_STALE"
    if log["latest_state"] == "TRIAL_COMPLETE":
        terminal_matches = (
            log["entries_total_from_log"] == book["entries_lifetime"] == 5 and
            book["entry_cap_reached"] and
            book["virtual_sells"] == 5 and
            not book["open_positions"]
        )
        health = (
            "TRIAL_COMPLETE_RECONCILED" if terminal_matches else
            "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE"
        )
    elif log["latest_state"] == "VIRTUAL_FORWARD_STEP":
        try:
            matches = (
                log["entries_total_from_log"] == book["entries_lifetime"] and
                log["positions_open_from_log"] == len(book["open_positions"]) and
                Decimal(str(log["cash_virtual_from_log"])) ==
                Decimal(book["current_virtual_cash"]) and
                Decimal(str(log["realized_pnl_virtual_from_log"])) ==
                Decimal(book["realized_virtual_pnl"])
            )
        except (ValueError, TypeError):
            matches = False
        if not matches:
            health = "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE"
    return {
        "monitor_health": health,
        "latest_state": log["latest_state"],
        "minutes_since_journal_update": round(max(0, age) / 60, 1),
        "opening_virtual_cash": book["opening_virtual_cash"],
        "current_virtual_cash": book["current_virtual_cash"],
        "realized_virtual_pnl": book["realized_virtual_pnl"],
        "entries_lifetime": book["entries_lifetime"],
        "virtual_sells": book["virtual_sells"],
        "entry_cap_reached": book["entry_cap_reached"],
        "open_positions": book["open_positions"],
        "latest_journal_event_utc": book["latest_journal_event_utc"],
        "journal_modified_utc": book["journal_modified_utc"],
        "log_modified_utc": log["log_modified_utc"],
        "latest_liquidation_equity_virtual_est":
            log["latest_liquidation_equity_virtual_est"],
        "latest_net_pnl_virtual_est": log["latest_net_pnl_virtual_est"],
        "broker_orders_sent_reported": 0,
        "merged_crypto_profits": False,
        "note": (
            "Delayed-quote stock simulation only; journal cash and realized P/L "
            "are authoritative for this separate virtual experiment. Estimates "
            "are not Tradier broker-paper fills or executable quotes."
        ),
    }


def build_status(private_dir, *, now):
    root = Path(private_dir)
    if root.is_symlink():
        raise ValueError("trading directory symlink denied")
    book = get_virtual_snapshot(root / "crypto_virtual_forward.sqlite3")
    clock = parse_monitor_log(root / "crypto_virtual_monitor.jsonl", now)
    stock_book = get_stock_virtual_snapshot(root / "forward_execution_qa.json")
    stock_log = parse_stock_qa_log(root / "forward_qa_stdout.log")
    stock = reconcile_stock_status(stock_book, stock_log, now)
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
