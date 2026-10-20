#!/usr/bin/env python3
"""Sandbox paper account smoke and optional broker order PREVIEW only.

This CLI intentionally has no submit argument. It never creates a paper trade,
makes a live order, accepts a production API key, or prints sensitive account
data. Actual PAPER submission in the separate guarded library remains OFF.
"""
import argparse
import json
import os
import sys
from decimal import Decimal, InvalidOperation, ROUND_UP

from zerocost_bot.tradier_paper import (
    TradierSandbox, PaperBlocked, BrokerUncertain, SANDBOX_ENV,
)


def quote_limit(sb, symbol):
    data = sb._request(
        "GET", "/markets/quotes", query={"symbols": symbol, "greeks": "false"})
    section = data.get("quotes") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        raise BrokerUncertain("no delayed sandbox quote returned")
    quote = section.get("quote")
    if isinstance(quote, list):
        if len(quote) != 1:
            raise BrokerUncertain("ambiguous sandbox quote response")
        quote = quote[0]
    if not isinstance(quote, dict) or quote.get("symbol") != symbol:
        raise BrokerUncertain("sandbox quote symbol mismatch")
    try:
        ask = Decimal(str(quote["ask"]))
    except (InvalidOperation, KeyError, ValueError, TypeError):
        raise BrokerUncertain("sandbox quote has no valid ask") from None
    if not ask.is_finite() or ask <= 0:
        raise BrokerUncertain("invalid sandbox ask price")
    # A one-cent-above-ask paper LIMIT is used ONLY to test the preview validator.
    # A delayed quote is never an executable real-time market signal.
    price = (ask + Decimal("0.01")).quantize(
        Decimal("0.01"), rounding=ROUND_UP)
    if not Decimal("1") <= price <= Decimal("20"):
        raise PaperBlocked("symbol quote outside the $1-$20 paper smoke range")
    return price


class SafeStageError(RuntimeError):
    """Only fixed stage labels, never account data, leave this process."""


def inspect_or_preview(symbol, do_preview=False):
    client = TradierSandbox()
    try:
        account = client.state()
    except (PaperBlocked, BrokerUncertain):
        raise SafeStageError(client.last_stage) from None
    summary = {
        "environment": "TRADIER_SANDBOX_ONLY",
        "paper_account_connected": True,
        "cash_available_for_one_share": account["cash"] >= Decimal("20"),
        "open_or_prior_session_orders": len(account["orders"]),
        "positions_count": len(account["positions"]),
        "pending_orders_count": account["pending"],
        "paper_order_created": False,
        "live_money_trade": False,
    }
    if do_preview:
        try:
            price = quote_limit(client, symbol)
        except (PaperBlocked, BrokerUncertain):
            raise SafeStageError("delayed_quote") from None
        try:
            result = client.preview(symbol, price)
        except (PaperBlocked, BrokerUncertain):
            raise SafeStageError(client.last_stage) from None
        summary["preview"] = {
            "status": result["status"],
            "entry_limit": result["entry_limit"],
            "otoco_exits": result["otoco_exits"],
            "simulated_only": True,
        }
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Tradier SANDBOX GETs and preview=true ONLY; never submits")
    parser.add_argument("--symbol", default="SOFI",
                        choices=("SOFI", "AAL", "F", "CLF"))
    parser.add_argument("--preview", action="store_true",
                        help="run POST preview=true; no paper/live order created")
    args = parser.parse_args(argv)
    if not os.environ.get(SANDBOX_ENV):
        print("Tradier SANDBOX secret unavailable; do not paste token into chat/logs.",
              file=sys.stderr)
        return 2
    try:
        summary = inspect_or_preview(args.symbol, do_preview=args.preview)
    except SafeStageError as error:
        # Fixed, code-owned stage labels. Never relay Tradier response
        # bodies, account metadata, URLs, secrets, or raw exceptions.
        safe_stages = {
            "profile", "account_selection", "balances", "positions",
            "orders", "pending_orders", "account_state_ready",
            "delayed_quote", "preview_preflight", "preview_request",
            "preview_validation", "not_started",
        }
        stage = str(error) if str(error) in safe_stages else "unspecified"
        print("Tradier sandbox verification BLOCKED at " + stage +
              "; no order was submitted.", file=sys.stderr)
        return 1
    except (PaperBlocked, BrokerUncertain):
        print("Tradier sandbox verification BLOCKED; no order was submitted.",
              file=sys.stderr)
        return 1
    except Exception:
        print("Unexpected sandbox response; no order was submitted.",
              file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
