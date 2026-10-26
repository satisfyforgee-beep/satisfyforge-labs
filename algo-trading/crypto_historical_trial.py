#!/usr/bin/env python3
"""Run three predeclared strategies on recent real Kraken 15-minute candles.

No API token, broker imports, POSTs or real/connected paper orders.
This is *historical simulation*, which can overfit and cannot prove future P/L.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from zerocost_bot.crypto_replay import (
    STRATEGIES, VALID_PAIRS, aligned, fetch_kraken_ohlc, simulate,
)
from zerocost_bot.replay_lessons import review_crypto_trial


def run():
    received = datetime.now(timezone.utc)
    candles = {symbol: fetch_kraken_ohlc(symbol, now=received)
               for symbol in VALID_PAIRS}
    timeline, matrix = aligned(candles)
    split = max(30, len(timeline) * 7 // 10)
    if len(timeline) - split < 40:
        raise ValueError("insufficient untouched holdout data")
    results = {}
    total_trades = 0
    for method in STRATEGIES:
        # All three predeclared strategies are evaluated on the same fixed
        # 70% development / 30% holdout partition. No optimizing on holdout.
        train = simulate(matrix, strategy=method, start=18, end=split)
        holdout = simulate(matrix, strategy=method, start=split, end=len(timeline))
        results[method] = {"development": train, "holdout": holdout}
        total_trades += train["virtual_closes"] + holdout["virtual_closes"]
    control_hold = results["control"]["holdout"]
    candidates = []
    for method in ("breakout", "reversal"):
        test = results[method]["holdout"]
        if (test["virtual_closes"] >= 10
                and float(test["return_pct"]) > 0
                and float(test["return_pct"]) > float(control_hold["return_pct"])
                and float(test["max_drawdown_pct"]) <= 3):
            candidates.append(method)
    # Even if candidates pass a short holdout, never authorize brokerage orders.
    report = {
        "as_of_utc": received.isoformat(),
        "mode": "HISTORICAL_OFFLINE_REPLAY_NO_BROKER_ORDERS",
        "source": "KRAKEN_PUBLIC_OHLC_15MIN_LAST_CANDLE_EXCLUDED",
        "asset_class": "spot_crypto",
        "symbols": sorted(candles),
        "first_completed_candle_utc": datetime.fromtimestamp(
            timeline[0], timezone.utc).isoformat(),
        "last_completed_candle_utc": datetime.fromtimestamp(
            timeline[-1] + 900, timezone.utc).isoformat(),
        "aligned_completed_candles": len(timeline),
        "development_bars": split - 18,
        "held_out_bars": len(timeline) - split,
        "total_closed_historical_virtual_trades": total_trades,
        "estimated_round_trip_taker_fee_percent": "0.8",
        "estimated_round_trip_slippage_percent": "0.1",
        "warning": (
            "OHLC intrabar ordering unknown; stop-first for collisions. "
            "Costs are estimates, not executable order book quotes. "
            "Short rolling history, not a proven statistical edge."
        ),
        "potential_followup_research_only": candidates,
        "paper_broker_orders_sent": 0,
        "live_money_orders_sent": 0,
        "results": results,
    }
    report["postmortem"] = review_crypto_trial(report)
    home = Path.home() / ".satisfyforge" / "trading"
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    name = "crypto_real_history_replay_" + received.strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = home / name
    handle = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(handle, "w") as file:
        json.dump(report, file, sort_keys=True, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    brief = {
        "mode": report["mode"],
        "as_of_utc": report["as_of_utc"],
        "symbols": report["symbols"],
        "closed_historical_virtual_trades": total_trades,
        "bars_train": report["development_bars"],
        "bars_holdout": report["held_out_bars"],
        "trial_report": str(path),
        "strategies": {
            k: {
                stage: {name: report["results"][k][stage][name] for name in (
                    "virtual_closes", "wins", "losses_or_flats",
                    "net_pnl_after_estimated_costs", "max_drawdown_pct",
                    "return_pct", "estimated_fees")}
                for stage in ("development", "holdout")}
            for k in STRATEGIES
        },
        "paper_broker_orders_sent": 0,
        "live_money_orders_sent": 0,
        "postmortem_outcome": report["postmortem"]["outcome"],
        "per_strategy_gate": {
            name: report["postmortem"]["strategies"][name]
            for name in STRATEGIES
        },
    }
    print(json.dumps(brief, sort_keys=True, indent=2))


if __name__ == "__main__":
    try:
        run()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({
            "status": "HISTORICAL_REPLAY_UNAVAILABLE",
            "reason_type": type(error).__name__,
            "paper_broker_orders_sent": 0, "live_money_orders_sent": 0,
        }))
        sys.exit(1)
