#!/usr/bin/env python3
"""One owner-authorized SOFI one-share Tradier SANDBOX order test.

Only October 21, 2026, 09:35-14:44 New York time. Exactly one share at a
limit price <= $20, AND total preview debit <= $20 including fees, native
OTOCO target at limit*1.035 and stop at limit*.98. Protected environment
and mock-tested invariant checks. No options, shorting, live broker, or
repeat submissions. Not a trading strategy or buy recommendation.

GitHub Actions keeps the SANDBOX token in its secrets store and prints
only sanitized results; a local terminal without the key will not trade.
"""
from __future__ import annotations

from datetime import datetime, date, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

from zerocost_bot.journal import OrderJournal
from zerocost_bot.tradier_paper import (
    TradierSandbox, PaperBlocked, BrokerUncertain, SUBMIT_GATE, SUBMIT_VALUE,
)
from zerocost_bot.tradier_reconciliation import SandboxReconciler
from tradier_paper_cli import quote_limit

DATE = date(2026, 10, 21)
SYMBOL = "SOFI"
QTY = 1
CAP = Decimal("20.00")
_APPROVAL_VAR = "SF_ONE_SHARE_TRIAL_APPROVAL"
_APPROVAL_VALUE = "SOFI-20261021-SANDBOX-ONE-SHARE-20USD"
_ET = ZoneInfo("America/New_York")


def authorized_window(now: datetime) -> bool:
    if not isinstance(now, datetime) or now.tzinfo is None:
        return False
    et = now.astimezone(_ET)
    minute = et.hour * 60 + et.minute
    return (et.date() == DATE and et.weekday() < 5
            and 9 * 60 + 35 <= minute < 14 * 60 + 45)


def _one_share_report(kind, **allowed):
    """Fixed-schema informational logging; no token/account/order IDs."""
    clean = {
        "environment": "TRADIER_SANDBOX_ONLY",
        "symbol": SYMBOL, "quantity": QTY,
        "maximum_total_virtual_debit": str(CAP),
        "target_from_limit": "3.5%",
        "stop_from_limit": "2.0%",
        "live_money_trading_enabled": False,
        "status": kind,
    }
    safe = {
        "entry_limit", "entry_status", "verified_protective_exits",
        "bracket_readiness", "polls", "reason_code",
    }
    for key, value in allowed.items():
        if key in safe and isinstance(value, (int, float, str, bool)):
            clean[key] = value
    print(json.dumps(clean, sort_keys=True), flush=True)


def execute_one_owner_approved_sandbox_trial(*, now=None, broker=None,
                                              journal_path=None, sleep=time.sleep,
                                              max_polls=9, poll_seconds=10):
    """One attempt; no retries of POST, even after ambiguous outcomes."""
    now = now or datetime.now(timezone.utc)
    if not authorized_window(now):
        _one_share_report("PREMARKET_OR_OUTSIDE_APPROVED_WINDOW")
        return 0
    if (os.environ.get(_APPROVAL_VAR) != _APPROVAL_VALUE or
            os.environ.get(SUBMIT_GATE) != SUBMIT_VALUE):
        _one_share_report("BLOCKED", reason_code="paper_authorization_not_armed")
        return 2
    if type(max_polls) is not int or not 1 <= max_polls <= 12:
        raise ValueError("paper test poll cap invalid")
    if type(poll_seconds) is not int or not 5 <= poll_seconds <= 30:
        raise ValueError("paper test polling interval invalid")
    if broker is None:
        broker = TradierSandbox()
    if not isinstance(broker, TradierSandbox):
        raise TypeError("this one-time trial requires SANDBOX adapter")
    # Fetch *delayed* sandbox ask for a smoke-test limit. This is NOT
    # alpha, nor a real-time or future-price prediction.
    try:
        price = quote_limit(broker, SYMBOL)
    except (PaperBlocked, BrokerUncertain):
        _one_share_report("BLOCKED", reason_code="quote_unavailable_or_outside_cap")
        return 2
    if not Decimal("1.00") <= price <= CAP:
        _one_share_report("BLOCKED", reason_code="quote_outside_virtual_20_dollar_cap")
        return 2
    # Safeguards inside submit_paper: NY broker clock open, no existing
    # paper orders/positions, unleveraged cash, preview and total debit cap,
    # fresh broker readback, account/day journal, and ONE sandbox POST.
    temp = None
    if journal_path is None:
        temp = tempfile.TemporaryDirectory(prefix="sf-one-paper-")
        journal_path = str(Path(temp.name) / "paper-journal.sqlite3")
    try:
        journal = OrderJournal(journal_path)
        result = broker.submit_paper(
            SYMBOL, price, journal, explicitly_armed=True, now=now,
        )
        if result.get("status") != "SUBMITTED_TO_SANDBOX_NOT_A_FILL":
            raise BrokerUncertain("unknown sandbox receipt")
        key = result.get("journal_key")
        row = journal.status(key)
        if not isinstance(row, dict) or row.get("state") != "submitted":
            raise BrokerUncertain("missing confirmed local attempt")
        order_id = row.get("broker_order_id")
        if not isinstance(order_id, str) or not order_id.isdigit():
            raise BrokerUncertain("missing broker receipt ID")
        _one_share_report("SUBMITTED_NOT_CONFIRMED_FILLED", entry_limit=str(price))
        reader = SandboxReconciler(broker)
        last = "UNAVAILABLE"
        last_status = "UNKNOWN"
        verified_exits = 0
        for poll in range(1, max_polls + 1):
            try:
                order = broker.order_readback(order_id)
                last_status = order["status"]
                bracket = reader.inspect(order_id, symbol=SYMBOL)
                last = bracket["readiness"]
                verified_exits = bracket["verified_protective_exits"]
            except (PaperBlocked, BrokerUncertain, OSError, ValueError, KeyError):
                _one_share_report("STOP_AND_RECONCILE",
                                  entry_limit=str(price),
                                  reason_code="broker_order_readback_uncertain",
                                  polls=poll)
                return 1
            if last == "HALT_AND_RECONCILE":
                _one_share_report("STOP_AND_RECONCILE",
                                  entry_limit=str(price), entry_status=last_status,
                                  bracket_readiness=last,
                                  verified_protective_exits=verified_exits,
                                  reason_code="protective_exits_unverified",
                                  polls=poll)
                return 1
            if last in ("PROTECTED_PAPER_POSITION", "CLOSED_PAPER_POSITION",
                        "ENTRY_NOT_FILLED"):
                _one_share_report("BROKER_READBACK_VERIFIED",
                                  entry_limit=str(price), entry_status=last_status,
                                  bracket_readiness=last,
                                  verified_protective_exits=verified_exits,
                                  polls=poll)
                return 0
            if poll < max_polls:
                sleep(poll_seconds)
        _one_share_report("PENDING_BROKER_FOLLOWUP",
                          entry_limit=str(price), entry_status=last_status,
                          bracket_readiness=last,
                          verified_protective_exits=verified_exits,
                          polls=max_polls)
        return 0
    finally:
        if temp is not None:
            temp.cleanup()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv != ["--execute-approved-sandbox-test"]:
        print("No paper or live order authorized by these CLI arguments.",
              file=sys.stderr)
        return 2
    try:
        return execute_one_owner_approved_sandbox_trial()
    except (PaperBlocked, BrokerUncertain):
        _one_share_report("BLOCKED_OR_UNKNOWN",
                          reason_code="broker_refused_or_uncertain_no_retry")
        return 1
    except Exception:
        # Especially avoid printing raw brokerage responses or credentials.
        _one_share_report("BLOCKED_OR_UNKNOWN",
                          reason_code="unexpected_runtime_error_no_retry")
        return 1


if __name__ == "__main__":
    sys.exit(main())
