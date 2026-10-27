#!/usr/bin/env python3
"""Snapshot existing virtual trades and monitor health; never places orders.

Prints one redacted JSON result. No browser, feed, broker or credential reads.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

from zerocost_bot.paper_status import build_status


def main():
    try:
        report = build_status(
            Path.home() / ".satisfyforge" / "trading",
            now=datetime.now(timezone.utc),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({
            "mode": "PRIVATE_READ_ONLY_VIRTUAL_TRADING_STATUS",
            "status": "HALT_UNVERIFIED_LOCAL_EVIDENCE",
            "failure_class": type(error).__name__,
            "broker_orders_placed_by_this_report": 0,
            "real_money_orders_placed_by_this_report": 0,
        }, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
