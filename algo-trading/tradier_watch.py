#!/usr/bin/env python3
"""Private SANDBOX-only order monitor. Read-only; no trading endpoints.

Run once by default. --watch polls 10-60s but only while this owner-managed
local process runs. No cloud scheduler, public server or paid subscription.
Every exception triggers a HALT status and clean process shutdown.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

from zerocost_bot.tradier_paper import TradierSandbox
from zerocost_bot.tradier_reconciliation import SandboxReconciler
from zerocost_bot.paper_supervisor import (
    PaperSupervisor, SupervisorReport, append_private_journal,
    write_private_report,
)

_STOCK = re.compile(r"[A-Z]{1,5}$")
_ID = re.compile(r"[0-9]{1,18}$")


def _private_root():
    """Can be overridden only in direct tests by passing a private Path."""
    return Path.home() / ".satisfyforge" / "trading"


def run_watch(order_id, symbol, *, watch=False, interval_seconds=15,
              max_polls=120, report_dir=None, read_function=None,
              sleep=time.sleep):
    if not isinstance(order_id, str) or not _ID.fullmatch(order_id) or int(order_id) < 1:
        raise ValueError("valid paper order ID required")
    if not isinstance(symbol, str) or not _STOCK.fullmatch(symbol):
        raise ValueError("valid equity symbol required")
    if type(interval_seconds) not in (int, float) or not 10 <= interval_seconds <= 60:
        raise ValueError("poll interval must be 10-60 seconds")
    if type(max_polls) is not int or not 1 <= max_polls <= 720:
        raise ValueError("poll limit must be 1-720")
    if read_function is None:
        # Sandbox token stays solely in process memory, never logs or reports.
        broker = TradierSandbox()
        recon = SandboxReconciler(broker)
        read_function = lambda: recon.inspect(order_id, symbol=symbol)
    root = Path(report_dir) if report_dir is not None else _private_root()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("private report directory must not be symlinked")
    lockpath = root / "paper_monitor.lock"
    if lockpath.is_symlink():
        raise ValueError("monitor lock must not be a symlink")
    # Exclusive non-blocking lock prevents duplicate monitors of same account.
    fd = os.open(str(lockpath), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError):
            raise RuntimeError("another sandbox monitor already holds the lock") from None
        supervisor = PaperSupervisor(read_function)
        limit = max_polls if watch else 1
        last = None
        for index in range(limit):
            last = supervisor.poll()
            write_private_report(last, directory=root)
            append_private_journal(last, directory=root)
            print(json.dumps(last.as_dict(), sort_keys=True), flush=True)
            if last.state != "MONITORING":
                break
            if watch and index < limit - 1:
                sleep(interval_seconds)
        if last is None:
            return 2
        if last.state == "HALTED":
            return 1
        return 0
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="SANDBOX-only read-only order watchdog, no order submission")
    parser.add_argument("--order-id", required=True,
                        help="known SANDBOX order ID (not a live order)")
    parser.add_argument("--symbol", required=True,
                        choices=("SOFI", "AAL", "F", "CLF"))
    parser.add_argument("--watch", action="store_true",
                        help="monitor while this process runs; never trades")
    parser.add_argument("--interval", type=int, default=15,
                        help="poll seconds, range 10 to 60")
    parser.add_argument("--max-polls", type=int, default=120,
                        help="upper bound on number of polls, max 720")
    args = parser.parse_args(argv)
    try:
        return run_watch(
            args.order_id, args.symbol, watch=args.watch,
            interval_seconds=args.interval, max_polls=args.max_polls)
    except KeyboardInterrupt:
        # No automatic trading capability; leave a sanitized stopped marker.
        report = SupervisorReport(
            "STOPPED", "UNKNOWN", "Owner stopped the read-only monitor",
            datetime.now(timezone.utc).isoformat())
        try:
            write_private_report(report, directory=_private_root())
            append_private_journal(report, directory=_private_root())
        except (OSError, ValueError):
            pass
        print("Read-only monitor stopped by owner.", file=sys.stderr)
        return 130
    except (RuntimeError, ValueError, OSError, TypeError):
        print("Read-only SANDBOX monitor unavailable or locked; no trades sent.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
