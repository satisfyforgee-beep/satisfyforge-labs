#!/usr/bin/env python3
"""Read-only, provider-neutral coverage report. NO trading or funding routes.

Run with --demo for synthetic smoke. Use --kraken-public for free real crypto
spot data, or --tradier-live with separately approved local data credentials.
"""
import argparse
import json
from datetime import datetime, timedelta, timezone

from zerocost_bot.market_coverage import AssetClass, CoverageGate, MarketQuote
from zerocost_bot.read_only_feeds import (
    fetch_kraken_public_book, fetch_tradier_live_quotes,
)


def synthetic_quotes(now):
    """Made-up, non-live values: test the data router, not a trading strategy."""
    old = now - timedelta(seconds=1)
    return [
        MarketQuote("alpaca_iex", AssetClass.STOCK, "SOFI",
                    14.60, 14.61, old, old, now, True),
        MarketQuote("tradier_live", AssetClass.STOCK, "SOFI",
                    14.59, 14.61, old, old, now, True),
        MarketQuote("tradier_live", AssetClass.OPTION,
                    "SOFI261023C00015000", 0.199, 0.20, old, old, now, True),
        MarketQuote("kraken_public", AssetClass.CRYPTO,
                    "BTC/USD", 65000, 65001, old, old, now, True),
    ]


def main():
    p = argparse.ArgumentParser(
        description="Data coverage diagnostics ONLY; never sends a trading order")
    p.add_argument("--demo", action="store_true",
                   help="use clearly labeled synthetic quotes for offline tests")
    p.add_argument("--tradier-live", action="store_true",
                   help="read live quotes with separately enabled local Tradier key")
    p.add_argument("--kraken-public", action="store_true",
                   help="fetch public Kraken spot book; no credentials required")
    p.add_argument("--symbols", nargs="+", default=["SOFI", "SPY"],
                   help="stocks and OCC contracts for the Tradier read-only call")
    p.add_argument("--crypto-pairs", nargs="+", default=["BTC/USD"],
                   help="Kraken spot USD markets (research only)")
    args = p.parse_args()
    if args.demo and (args.tradier_live or args.kraken_public):
        p.error("--demo may not be mixed with actual market feeds")
    if not (args.demo or args.tradier_live or args.kraken_public):
        print("No feeds connected. Run --demo for offline validation; "
              "--kraken-public for free crypto research; "
              "or --tradier-live after enabling authorized read-only market data.")
        return
    now = datetime.now(timezone.utc)
    gate = CoverageGate()
    notes = []
    data = []
    if args.demo:
        data += synthetic_quotes(now)
        notes.append("DEMONSTRATION: every demo quote is fabricated, NOT a market price")
    if args.tradier_live:
        try:
            data += fetch_tradier_live_quotes(args.symbols, now=now)
        except (OSError, ValueError, RuntimeError, KeyError) as err:
            notes.append("Tradier unavailable: " + str(err))
    if args.kraken_public:
        for pair in args.crypto_pairs:
            try:
                data.append(fetch_kraken_public_book(pair, now=now))
            except (OSError, ValueError, RuntimeError, KeyError) as err:
                notes.append("Kraken " + pair + " unavailable: " + str(err))
    for quote in data:
        try:
            gate.ingest(quote)
        except (ValueError, TypeError, OverflowError) as err:
            notes.append("Discarded invalid " + quote.provider + " quote: " + str(err))
    targets = sorted({(q.symbol, q.asset) for q in data},
                     key=lambda entry: (entry[1].value, entry[0]))
    reports = [gate.assess(symbol, asset, now).as_report()
               for symbol, asset in targets]
    print(json.dumps({
        "mode": "SYNTHETIC_TEST_ONLY" if args.demo else "READ_ONLY_RESEARCH",
        "at_utc": now.isoformat(), "live_money_trading_enabled": False,
        "reports": reports, "notes": notes,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
