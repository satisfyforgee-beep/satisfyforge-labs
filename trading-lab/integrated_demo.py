#!/usr/bin/env python3
"""Repeatable synthetic signal -> quote -> SQLite ledger demo. NO BROKER."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from paper_engine import Instrument, PaperEngine, Quote, RiskPolicy
from pipeline import Bar, evaluate_equity_breakout, safety_readiness


def main():
    parser = argparse.ArgumentParser(description="Offline synthetic breakout and idempotent journal")
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    start = datetime(2026, 10, 27, 13, 30, tzinfo=timezone.utc)
    now = start + timedelta(minutes=15, seconds=10)
    bars = [Bar("DEMO", start + timedelta(minutes=i), 10, 10, 10, 10, 100)
            for i in range(13)]
    bars += [Bar("DEMO", start + timedelta(minutes=13), 11, 11, 11, 11, 10000),
             Bar("DEMO", start + timedelta(minutes=14), 11.1, 11.1, 11.1, 11.1, 10000)]
    quote = Quote(Instrument("DEMO", "equity"), Decimal("11.09"), Decimal("11.12"),
                  now - timedelta(seconds=2), "SYNTHETIC_EXAMPLE", delayed=False)
    journal = PaperEngine(args.database, Decimal("100"),
                          RiskPolicy(Decimal("70"), Decimal("100"), Decimal("100")))
    outcome = evaluate_equity_breakout(journal, bars, quote, now)
    print(json.dumps({"mode": "FICTIONAL_OFFLINE_PAPER_ONLY", "decision": outcome,
                      "account": journal.snapshot(), "performance": journal.performance(),
                      "readiness": safety_readiness()}, indent=2))


if __name__ == "__main__":
    main()
