#!/usr/bin/env python3
"""Sanitized GET-only bridge from Alpaca capture to the offline inventory fence.

This operator tool never submits, cancels, or replaces an order.  Raw provider
responses stay in memory and are passed directly to the existing normalizer;
stdout contains only coarse status, counts, and safety flags.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError


_ALGO_PATH = Path(__file__).resolve().parents[1] / "algo-trading"
if str(_ALGO_PATH) not in sys.path:
    sys.path.insert(0, str(_ALGO_PATH))

from data_preflight import (  # noqa: E402
    capture_alpaca_inventory,
    classify_alpaca_cash_only_eligibility,
    load_credentials,
)
from paper_engine import normalize_alpaca_inventory_capture  # noqa: E402


def _base_report(*, network_attempted: bool, keychain_opted_in: bool) -> dict:
    return {
        "mode": "ALPACA_PAPER_GET_ONLY_INVENTORY_FENCE",
        "network_attempted": network_attempted,
        "keychain_opted_in": keychain_opted_in,
        "inventory_status": "NOT_ATTEMPTED",
        "cash_only_eligibility": "UNKNOWN",
        "position_count": None,
        "open_order_count": None,
        "captured_at": None,
        "broker_order_submission_enabled": False,
        "live_money_enabled": False,
        "raw_provider_data_displayed": False,
    }


def check_alpaca_inventory(*, network: bool = False,
                           allow_keychain: bool = False,
                           transport=None, clock=None) -> dict:
    """Capture, normalize, and summarize current paper inventory safely.

    Credential access and provider GETs are both opt-in through ``network``.
    The result deliberately excludes symbols, balances, account/order IDs,
    credential values, and exception details.  Any uncertain capture fails
    closed without returning the raw response.
    """
    report = _base_report(
        network_attempted=bool(network),
        keychain_opted_in=bool(network and allow_keychain),
    )
    if not network:
        return report

    credentials = load_credentials(allow_keychain=allow_keychain)
    api_key = credentials["ALPACA_PAPER_KEY"]
    api_secret = credentials["ALPACA_PAPER_SECRET"]
    if not api_key and not api_secret:
        report["inventory_status"] = "MISSING_CREDENTIAL"
        return report
    if not api_key or not api_secret:
        report["inventory_status"] = "INCOMPLETE_CREDENTIAL_PAIR"
        return report

    now = clock or (lambda: datetime.now(timezone.utc))
    try:
        capture = capture_alpaca_inventory(
            api_key=api_key,
            api_secret=api_secret,
            transport=transport,
            clock=now,
        )
        observed_at = now()
        snapshot = normalize_alpaca_inventory_capture(
            capture,
            observed_at=observed_at,
        )
        has_short_exposure = any(
            position.get("side") != "long"
            for position in snapshot["positions"]
        )
        report.update({
            "inventory_status": "FENCED",
            "cash_only_eligibility": classify_alpaca_cash_only_eligibility(
                snapshot["account"],
                has_short_exposure=has_short_exposure,
            ),
            "position_count": len(snapshot["positions"]),
            "open_order_count": len(snapshot["open_orders"]),
            "captured_at": snapshot["captured_at"],
        })
    except HTTPError as exc:
        report["inventory_status"] = (
            "AUTH_FAILED" if exc.code in {401, 403} else "HTTP_ERROR"
        )
    except (URLError, TimeoutError, OSError):
        report["inventory_status"] = "NETWORK_ERROR"
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        report["inventory_status"] = "HALT_INVENTORY_UNVERIFIED"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read and fence Alpaca paper inventory without trading",
    )
    parser.add_argument(
        "--network", action="store_true",
        help="Opt in to four fixed authenticated GET-only paper requests",
    )
    parser.add_argument(
        "--keychain", action="store_true",
        help="With --network, opt in to exact Alpaca paper Keychain items",
    )
    args = parser.parse_args()
    print(json.dumps(check_alpaca_inventory(
        network=args.network,
        allow_keychain=args.keychain,
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
