#!/usr/bin/env python3
"""Bounded autonomous *virtual* forward execution-QA, never brokerage orders.

Uses Tradier SANDBOX delayed market quotes as observations. Entries/exits
are HYPOTHETICAL quotes, not broker paper fills or evidence of alpha. This
baseline intentionally ranks quote *usability*, not predicted return.
"""
import argparse
import fcntl
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
import stat
import sys
import tempfile
from zoneinfo import ZoneInfo

from tradier_paper_lab import (
    rank_research_candidates, screen_snapshot, symbols_from_file, money,
)
from tradier_sandbox_check import fetch_json

ET = ZoneInfo("America/New_York")
INITIAL_CASH = Decimal("150.00")
MAX_ENTRY_DEBIT = Decimal("30.00")
MAX_LIFETIME_ENTRIES = 5
FEE_PER_SIDE = Decimal("0.01")
SLIPPAGE_PER_SHARE = Decimal("0.01")
STOP = Decimal("0.02")
TARGET = Decimal("0.035")
MAX_FILE_BYTES = 128_000


def empty_book():
    return {"version": 1, "initial_cash": str(INITIAL_CASH),
            "cash": str(INITIAL_CASH), "entries": 0,
            "positions": {}, "events": []}


def validate_book(book):
    if not isinstance(book, dict) or set(book) != {
        "version", "initial_cash", "cash", "entries", "positions", "events"
    } or book["version"] != 1:
        raise ValueError("Invalid private paper ledger schema")
    if book["initial_cash"] != str(INITIAL_CASH):
        raise ValueError("Unexpected initial cash budget")
    cash = money(book["cash"])
    if cash < 0 or cash > INITIAL_CASH * 2:
        raise ValueError("Corrupt virtual cash")
    if type(book["entries"]) is not int or not 0 <= book["entries"] <= MAX_LIFETIME_ENTRIES:
        raise ValueError("Corrupt lifetime entry count")
    if not isinstance(book["positions"], dict) or len(book["positions"]) > MAX_LIFETIME_ENTRIES:
        raise ValueError("Corrupt position inventory")
    if not isinstance(book["events"], list) or len(book["events"]) > MAX_LIFETIME_ENTRIES * 2:
        raise ValueError("Corrupt event inventory")
    buys = sum(x.get("action") == "BUY" for x in book["events"] if isinstance(x, dict))
    if buys != book["entries"]:
        raise ValueError("Paper entry journal inconsistent")
    for symbol, position in book["positions"].items():
        if not isinstance(symbol, str) or not symbol.isalpha() or len(symbol) > 6:
            raise ValueError("Invalid simulated symbol")
        if not isinstance(position, dict) or set(position) != {
            "quantity", "basis", "entry_quote_at", "stop_bid", "target_bid"
        } or position["quantity"] != 1:
            raise ValueError("Invalid simulated position")
        if money(position["basis"]) <= 0 or money(position["basis"]) > MAX_ENTRY_DEBIT:
            raise ValueError("Simulated position exceeds per-entry debit")
        for field in ("stop_bid", "target_bid"):
            if money(position[field]) <= 0:
                raise ValueError("Invalid simulated exit threshold")
        _iso(position["entry_quote_at"])
    reconstructed_cash = INITIAL_CASH
    active = {}
    seen = set()
    for event in book["events"]:
        if not isinstance(event, dict) or event.get("action") not in ("BUY", "SELL"):
            raise ValueError("Invalid simulated ledger event")
        symbol = event.get("symbol")
        if (not isinstance(symbol, str) or not symbol.isalpha() or len(symbol) > 6
                or event.get("quantity") != 1
                or event.get("simulated_not_broker_fill") is not True
                or money(event.get("fee")) != FEE_PER_SIDE):
            raise ValueError("Invalid virtual event details")
        price = money(event.get("virtual_price"))
        if price <= 0:
            raise ValueError("Invalid virtual event price")
        if event["action"] == "BUY":
            debit = money(event.get("virtual_debit"))
            if symbol in seen or debit != price + FEE_PER_SIDE or debit > MAX_ENTRY_DEBIT:
                raise ValueError("Invalid virtual buy debit or duplicate")
            seen.add(symbol)
            active[symbol] = debit
            reconstructed_cash -= debit
        else:
            if symbol not in active:
                raise ValueError("Virtual sell without position")
            proceeds = price - FEE_PER_SIDE
            if proceeds <= 0 or money(event.get("realized_pnl")) != proceeds - active[symbol]:
                raise ValueError("Invalid virtual sell proceeds or P/L")
            reconstructed_cash += proceeds
            del active[symbol]
    if reconstructed_cash != cash or cash < 0 or set(active) != set(book["positions"]):
        raise ValueError("Simulated cash or position inventory does not reconcile")
    if any(active[sym] != money(pos["basis"]) for sym, pos in book["positions"].items()):
        raise ValueError("Virtual position basis does not reconcile")
    return book


def _iso(text):
    if not isinstance(text, str):
        raise ValueError("Missing quote timestamp")
    t = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("Quote timestamp must be timezone aware")
    return t.astimezone(timezone.utc)


def _eligible_quote(row, now):
    if not row.get("eligible") or row.get("flags"):
        return False
    try:
        quoted = _iso(row["asof_utc"])
        age = (now - quoted).total_seconds()
        return (0 <= age <= 1800 and quoted.astimezone(ET).date() == now.astimezone(ET).date()
                and money(row["bid"]) > 0 and money(row["ask"]) >= money(row["bid"])
                and row["symbol"].isalpha() and len(row["symbol"]) <= 6)
    except (ValueError, TypeError, KeyError):
        return False


def virtual_step(book, rows, now, *, market_open, excluded=("SOFI",)):
    """One deterministic step. Never routes to any trading API."""
    validate_book(book)
    if now.tzinfo is None:
        raise ValueError("Timezone aware clock required")
    now = now.astimezone(timezone.utc)
    local = now.astimezone(ET)
    minute = local.hour * 60 + local.minute
    # Broker clock is required to close on holidays/early-close days.
    if not market_open or local.weekday() >= 5 or not (9 * 60 + 35 <= minute < 16 * 60):
        return {"state": "MARKET_CLOSED_OR_UNVERIFIED", "opened": 0, "closed": 0}
    if not isinstance(rows, list) or len(rows) > 500 or len({
        row.get("symbol") for row in rows if isinstance(row, dict)
    }) != len(rows):
        raise ValueError("Missing, duplicate or malformed quote rows")
    eligible = {row["symbol"]: row for row in rows if _eligible_quote(row, now)}
    opened = closed = 0
    for symbol, position in list(book["positions"].items()):
        row = eligible.get(symbol)
        if row is None or _iso(row["asof_utc"]) <= _iso(position["entry_quote_at"]):
            continue
        bid = money(row["bid"])
        # Force a virtual session liquidation when the *delayed* data remains
        # usable near the close. Missing late snapshot remains an open risk.
        reason = ("STOP" if bid <= money(position["stop_bid"]) else
                  "TARGET" if bid >= money(position["target_bid"]) else
                  "SESSION_END" if minute >= 15 * 60 + 40 else None)
        if reason is None:
            continue
        sold = max(Decimal("0.01"), bid - SLIPPAGE_PER_SHARE)
        proceeds = sold - FEE_PER_SIDE
        if proceeds <= 0:
            continue
        book["cash"] = str(money(book["cash"]) + proceeds)
        book["events"].append({
            "action": "SELL", "symbol": symbol, "quantity": 1,
            "quote_at": row["asof_utc"], "checked_at": now.isoformat(),
            "virtual_price": str(sold), "fee": str(FEE_PER_SIDE),
            "realized_pnl": str(proceeds - money(position["basis"])),
            "reason": reason, "simulated_not_broker_fill": True,
        })
        del book["positions"][symbol]
        closed += 1
    # Conservative one-shot trial: only FIVE total virtual entries ever.
    # No new entries after 14:45 ET or while any input is stale.
    if minute < 14 * 60 + 45 and book["entries"] < MAX_LIFETIME_ENTRIES:
        for row in rank_research_candidates(rows):
            symbol = row["symbol"]
            if (book["entries"] >= MAX_LIFETIME_ENTRIES or
                    len(book["positions"]) >= MAX_LIFETIME_ENTRIES):
                break
            if (symbol in excluded or symbol in book["positions"]
                    or not _eligible_quote(row, now)
                    or any(e["action"] == "BUY" and e["symbol"] == symbol
                           for e in book["events"])):
                continue
            # Simple 1-share control-group execution test, not an alpha signal.
            ask = money(row["ask"])
            paid = ask + SLIPPAGE_PER_SHARE
            debit = paid + FEE_PER_SIDE
            if debit > MAX_ENTRY_DEBIT or debit > money(book["cash"]):
                continue
            book["cash"] = str(money(book["cash"]) - debit)
            book["positions"][symbol] = {
                "quantity": 1, "basis": str(debit),
                "entry_quote_at": row["asof_utc"],
                "stop_bid": str((paid * (Decimal("1") - STOP)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)),
                "target_bid": str((paid * (Decimal("1") + TARGET)).quantize(Decimal("0.01"))),
            }
            book["entries"] += 1
            book["events"].append({
                "action": "BUY", "symbol": symbol, "quantity": 1,
                "quote_at": row["asof_utc"], "checked_at": now.isoformat(),
                "virtual_price": str(paid), "fee": str(FEE_PER_SIDE),
                "virtual_debit": str(debit), "simulated_not_broker_fill": True,
                "policy": "spread_liquidity_execution_QA_not_directional_signal",
            })
            opened += 1
    validate_book(book)
    realized = sum((money(e["realized_pnl"]) for e in book["events"]
                    if e["action"] == "SELL"), Decimal("0"))
    complete_marks = all(symbol in eligible for symbol in book["positions"])
    equity = None
    if complete_marks:
        liquidation_value = sum((max(Decimal("0"), money(eligible[s]["bid"]) -
                                     SLIPPAGE_PER_SHARE - FEE_PER_SIDE)
                                 for s in book["positions"]), Decimal("0"))
        equity = money(book["cash"]) + liquidation_value
    return {"state": "VIRTUAL_FORWARD_STEP", "opened": opened, "closed": closed,
            "entries_total": book["entries"], "positions_open": len(book["positions"]),
            "cash_virtual": book["cash"], "broker_orders_sent": 0,
            "realized_pnl_virtual": str(realized),
            "liquidation_equity_virtual_est": str(equity) if equity is not None else None,
            "net_pnl_virtual_est": str(equity - INITIAL_CASH) if equity is not None else None,
            "note": "Delayed-quote synthetic fills; not broker paper orders"}


def run_once(path, token, symbols, now=None, *, getter=fetch_json):
    """Lock and atomic-write private ledger; fail without overwriting on errors."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Aware timestamp required")
    root = path.parent
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or (root.stat().st_mode & 0o077):
        raise ValueError("Paper ledger directory must be private")
    if path.is_symlink():
        raise ValueError("Symlink paper ledger not allowed")
    lockpath = path.with_name(path.name + ".lock")
    if lockpath.is_symlink():
        raise ValueError("Symlink lock not allowed")
    fd = os.open(str(lockpath), os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if stat.S_IMODE(os.fstat(fd).st_mode) & 0o077:
            raise ValueError("Paper ledger lock permissions too open")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if path.exists():
            if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES or (path.stat().st_mode & 0o077):
                raise ValueError("Paper ledger invalid or not private")
            book = validate_book(json.loads(path.read_text()))
        else:
            book = empty_book()
        # Bounded test stops itself after five completed paper round trips.
        if book["entries"] >= MAX_LIFETIME_ENTRIES and not book["positions"]:
            return {"state": "TRIAL_COMPLETE", "broker_orders_sent": 0,
                    "entries_total": book["entries"]}
        local = now.astimezone(ET)
        minute = local.hour * 60 + local.minute
        if local.weekday() >= 5 or not (9 * 60 + 35 <= minute < 16 * 60):
            return {"state": "OUTSIDE_PAPER_SESSION", "broker_orders_sent": 0,
                    "entries_total": book["entries"]}
        raw_clock = getter("/markets/clock", token)
        clock = raw_clock.get("clock") if isinstance(raw_clock, dict) else None
        market_open = (isinstance(clock, dict) and clock.get("state") == "open"
                       and clock.get("date") == now.astimezone(ET).date().isoformat())
        if not market_open:
            return {"state": "MARKET_CLOSED_OR_UNVERIFIED", "broker_orders_sent": 0,
                    "entries_total": book["entries"]}
        watch = list(book["positions"]) if book["entries"] >= MAX_LIFETIME_ENTRIES else symbols
        rows = screen_snapshot(token, watch, DEFAULT_BUDGET,
                               now=now, getter=getter)
        outcome = virtual_step(book, rows, now, market_open=market_open)
        payload = json.dumps(book, sort_keys=True, separators=(",", ":")) + "\n"
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError("Forward book reached maximum size")
        temp_fd, temp_name = tempfile.mkstemp(prefix=".forward-", dir=str(root))
        try:
            os.fchmod(temp_fd, 0o600)
            with os.fdopen(temp_fd, "w") as out:
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return outcome
    finally:
        os.close(fd)


DEFAULT_BUDGET = MAX_ENTRY_DEBIT


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-shot autonomous virtual forward-paper research; NO broker orders")
    parser.add_argument("--symbols-file", default=str(Path(__file__).resolve().parents[1] /
                                                         "config/trading_universe_us_liquid.txt"))
    parser.add_argument("--state-file", default=str(Path.home() /
                                                    ".satisfyforge/trading/forward_execution_qa.json"))
    args = parser.parse_args(argv)
    try:
        token = os.getenv("TRADIER_SANDBOX_TOKEN", "")
        if not token:
            raise ValueError("Missing sandbox token")
        outcome = run_once(Path(args.state_file), token, symbols_from_file(args.symbols_file))
        print(json.dumps(outcome, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # No tokens, account IDs, request paths or raw responses in stdout.
        print("BLOCKED: private forward QA preflight failed; zero broker orders", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
