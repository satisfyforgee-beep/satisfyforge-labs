#!/usr/bin/env python3
"""No-network demonstration of equity, options, and crypto cash-only paper fills."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from paper_engine import Instrument, PaperEngine, PaperOrder, Quote, RiskPolicy


def main() -> None:
    parser = argparse.ArgumentParser(description="SatisfyForge paper-only synthetic trade smoke test")
    parser.add_argument("--database", required=True, type=Path,
                        help="SQLite journal path; existing orders are never duplicated")
    args = parser.parse_args()
    policy = RiskPolicy(
        max_order_cost=Decimal("100"),
        max_total_exposure=Decimal("300"),
        max_daily_loss=Decimal("300"),
    )
    engine = PaperEngine(args.database, Decimal("500"), policy)
    now = datetime.now(timezone.utc)
    inputs = [
        ("synthetic-equity-001", Instrument("DEMO", "equity"), "1", "10.03", "10.01", "10.03"),
        ("synthetic-option-001", Instrument("DEMO261030C00010000", "option", Decimal("100")),
         "1", "0.50", "0.48", "0.50"),
        ("synthetic-crypto-001", Instrument("TESTCOIN/USD", "crypto"),
         "0.01", "1000", "999", "1000"),
    ]
    results = []
    for client_id, instrument, qty, limit, bid, ask in inputs:
        results.append(engine.submit(
            PaperOrder(client_id, instrument, "buy", Decimal(qty), Decimal(limit)),
            Quote(instrument, Decimal(bid), Decimal(ask), now, "SYNTHETIC_DEMO"), now,
        ))
    print(json.dumps({
        "WARNING": "SYNTHETIC QUOTES. NO LIVE MARKET DATA, NO BROKER CONNECTION, NO REAL TRADES.",
        "orders": results, "account": engine.snapshot(),
    }, indent=2))


if __name__ == "__main__":
    main()
