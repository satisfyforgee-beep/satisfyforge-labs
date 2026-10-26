#!/usr/bin/env python3
"""One-shot, fail-closed public-Kraken-to-OFFLINE-VIRTUAL execution test.

--start-three records exactly three one-time modeled-ask buys ($15 each),
--check reads three public live books and applies virtual stops/targets/24h
exit rules. Both actions send ZERO orders to any real or paper broker.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import fcntl
import json
import os
from pathlib import Path
import sys

from zerocost_bot.crypto_virtual_forward import SYMBOLS, VirtualCryptoTrial
from zerocost_bot.read_only_feeds import fetch_kraken_public_book


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--start-three", action="store_true",
                      help="begin EXACTLY three bounded virtual crypto positions")
    mode.add_argument("--check", action="store_true",
                      help="GET-only quotes; update virtual exits if thresholds hit")
    args = parser.parse_args(argv)

    directory = Path.home() / ".satisfyforge" / "trading"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("private replay location cannot be symlink")
    os.chmod(directory, 0o700)
    lockfile = directory / "crypto_virtual_forward.lock"
    lock = os.open(str(lockfile), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.umask(0o077)
        path = directory / "crypto_virtual_forward.sqlite3"
        session = VirtualCryptoTrial(str(path))
        # No quote cache; validate all three live, GET-only public books.
        # If any provider fails, no new virtual fills are recorded.
        quotes = {symbol: fetch_kraken_public_book(symbol)
                  for symbol in SYMBOLS}
        now = datetime.now(timezone.utc)
        if args.start_three:
            report = session.start_three(quotes, now)
        else:
            report = session.evaluate_exits(quotes, now)
        print(json.dumps(report, sort_keys=True, indent=2))
    finally:
        os.close(lock)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(json.dumps({
            "state": "HALTED_AND_NO_RETRY",
            "mode": "OFFLINE_FORWARD_VIRTUAL_CRYPTO_NOT_BROKER_FILLED",
            "failure_class": type(exc).__name__,
            "broker_orders_sent": 0, "real_money_orders_sent": 0,
        }, sort_keys=True))
        sys.exit(1)
