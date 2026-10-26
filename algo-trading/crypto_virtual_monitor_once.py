#!/usr/bin/env python3
"""One check of the pre-existing THREE crypto *virtual-only* positions.

Invoked by macOS launchd approximately every 900 seconds while owner is
logged in and computer awake. Strictly calls crypto_virtual_runner --check;
it cannot start new positions, deposit funds, access trading credentials, or
send exchange/paper-broker orders. Persistent summary log is owner-only.
"""
from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
import io
import json
import os
import stat
import sys

from crypto_virtual_runner import main as virtual_runner_main
from zerocost_bot.crypto_virtual_forward import VirtualCryptoTrial

EXPECTED_MODE = "OFFLINE_FORWARD_VIRTUAL_CRYPTO_NOT_BROKER_FILLED"
MAX_LOG_BYTES = 300_000
DIR = Path.home() / ".satisfyforge" / "trading"
BOOK = DIR / "crypto_virtual_forward.sqlite3"
LOG = DIR / "crypto_virtual_monitor.jsonl"


def _record(event, *, path=LOG):
    """Append only sanitized, bounded private logs (no raw HTTP or secrets)."""
    DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if DIR.is_symlink():
        raise RuntimeError("symlinked private directory refused")
    os.chmod(DIR, 0o700)
    item = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "mode": EXPECTED_MODE,
        "actual_broker_orders": 0,
        "actual_money_trades": 0,
        **event,
    }
    line = (json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(line) > 1024:
        raise RuntimeError("oversized monitor log event")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND |
                 getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise RuntimeError("unsafe monitor log owner/file type")
        os.fchmod(fd, 0o600)
        if info.st_size + len(line) > MAX_LOG_BYTES:
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_report(report):
    if not isinstance(report, dict) or report.get("mode") != EXPECTED_MODE:
        raise ValueError("invalid offline monitor status")
    if report.get("broker_orders_sent") != 0 or report.get("state") != "VIRTUAL_EXIT_CHECK_COMPLETE":
        raise ValueError("unexpected broker or trial action")
    account = report.get("account")
    if (not isinstance(account, dict) or account.get("mode") != EXPECTED_MODE
            or account.get("broker_orders_sent") != 0
            or account.get("real_money_orders_sent") != 0
            or account.get("virtual_entry_event_count") != 3
            or type(account.get("virtual_exit_event_count")) is not int
            or not 0 <= account["virtual_exit_event_count"] <= 3
            or not isinstance(account.get("virtual_positions"), list)
            or len(account["virtual_positions"]) != 3-account["virtual_exit_event_count"]
            or type(report.get("virtual_exits_this_call")) is not int
            or not 0 <= report["virtual_exits_this_call"] <= 3):
        raise ValueError("incorrect or unsafe virtual account results")
    return {
        "state": "CHECK_COMPLETE",
        "open_virtual_positions": len(account["virtual_positions"]),
        "total_virtual_exits": account["virtual_exit_event_count"],
        "new_virtual_exits": report["virtual_exits_this_call"],
        "virtual_cash": account["settled_virtual_cash"],
        "virtual_realized_pnl": account["realized_virtual_pnl"],
        "estimated_virtual_liquidation": account["estimated_total_liquidation_value"],
    }


def run_once():
    # Unlike the interactive runner, scheduled checks must NEVER silently
    # construct/open a missing book, create entries or revive a completed trial.
    if not BOOK.exists() or BOOK.is_symlink():
        raise RuntimeError("pre-existing private virtual ledger unavailable")
    ledger = VirtualCryptoTrial(str(BOOK))
    snap = ledger.ledger.snapshot()
    if snap.get("mode") != "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE":
        raise ValueError("wrong book type")
    history = ledger._history()
    count = sum(row[1] == "buy" for row in history)
    if count != 3:
        raise ValueError("not the pre-approved three-entry virtual trial")
    positions = snap["positions"]
    if not positions and sum(row[1] == "sell" for row in history) == 3:
        return {
            "state": "TRIAL_COMPLETED_NO_NEW_QUOTES_OR_BUYS",
            "open_virtual_positions": 0,
            "total_virtual_exits": 3,
            "new_virtual_exits": 0,
            "virtual_cash": snap["settled_cash"],
            "virtual_realized_pnl": snap["realized_net_pnl"],
            "estimated_virtual_liquidation": snap["settled_cash"],
        }
    if len(positions) + sum(row[1] == "sell" for row in history) != 3:
        raise ValueError("virtual account inventory does not reconcile")
    capture = io.StringIO()
    # Constant literal --check only: no --start-three route in this monitor.
    with redirect_stdout(capture):
        virtual_runner_main(["--check"])
    try:
        report = json.loads(capture.getvalue())
    except (ValueError, TypeError):
        raise ValueError("invalid virtual readback") from None
    return _validate_report(report)


def main():
    os.umask(0o077)
    try:
        result = run_once()
        _record(result)
        print(result["state"])
        return 0
    except Exception as error:
        # Do not log HTTP response bodies, API endpoints, raw exception
        # messages, account details or credentials.
        _record({"state": "CHECK_HALTED", "error_class": type(error).__name__})
        print("CHECK_HALTED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
