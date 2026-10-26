#!/usr/bin/env python3
"""Zero-credential current Kraken crypto affordability radar — NEVER places orders.

Output is hypothetical cash-only RESEARCH, NOT a profitable signal, real paper
fill, or spendable brokerage balance. Crypto does not have a US stock session.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from zerocost_bot.opportunity_radar import review_paper_idea
from zerocost_bot.paper_capital import PaperCapital
from zerocost_bot.read_only_feeds import fetch_kraken_public_book


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", nargs="+", default=[
        "BTC/USD", "ETH/USD", "SOL/USD"])
    args = parser.parse_args()
    with TemporaryDirectory(prefix="sf-offline-radar-") as tmp:
        capital = PaperCapital(Path(tmp) / "replay.sqlite").snapshot()
    results = []
    for symbol in dict.fromkeys(args.pairs):
        try:
            quote = fetch_kraken_public_book(symbol)
            result = review_paper_idea(
                quote, capital, now=datetime.now(timezone.utc))
            results.append(result.as_report())
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            results.append({
                "asset": "crypto", "symbol": symbol,
                "status": "BLOCKED", "reason": str(exc),
                "paper_order_authorized": False,
                "live_order_authorized": False,
            })
    print(json.dumps({
        "mode": "READ_ONLY_PAPER_RESEARCH_NOT_A_TRADE",
        "as_of_utc": datetime.now(timezone.utc).isoformat(),
        "hypothetical_opening_cash_usd": capital["opening_cash"],
        "max_hypothetical_entry_debit_usd": "30.00",
        "hypothetical_fee_per_buy_usd": "0.25",
        "is_strategic_buy_signal": False,
        "is_broker_fill": False,
        "can_send_orders": False,
        "notes": [
            "Reference quotes come from one public Kraken venue, not executable cross-venue quotes.",
            "Research-only sizing does not verify asset-specific order minimums, slippage or fees.",
            "No position exists in a brokerage because of this report.",
        ],
        "results": results,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
