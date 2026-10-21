"""Evaluate timestamped research signals against subsequent market bars. No trades."""
import csv
import json
import argparse
from datetime import datetime, timedelta, timezone

def parse_time(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("UTC offset required")
    return d.astimezone(timezone.utc)

def evaluate(signals, bars, horizons=(15, 60, 390), cost_bps=20):
    if cost_bps < 0:
        raise ValueError("cost must be nonnegative")
    grouped = {}
    for bar in bars:
        price = float(bar["close"])
        if price <= 0:
            raise ValueError("bad close")
        grouped.setdefault(bar["symbol"].upper(), []).append((parse_time(bar["time"]), price))
    for series in grouped.values():
        series.sort()
    seen, output = set(), []
    for row in signals:
        symbol, start, entry = row["symbol"].upper(), parse_time(row["signal_time"]), float(row["signal_price"])
        if entry <= 0:
            raise ValueError("bad signal price")
        if (symbol, start) in seen:
            raise ValueError("duplicate signal")
        seen.add((symbol, start))
        item = {"symbol": symbol, "signal_time": start.isoformat(), "signal_price": entry}
        for minutes in horizons:
            target = start + timedelta(minutes=minutes)
            # Only future observations; ignore stale/missing intervals.
            found = next(((t, p) for t, p in grouped.get(symbol, []) if t >= target), None)
            item[str(minutes) + "m_net_return_pct"] = (
                round(100 * (found[1] / entry - 1 - cost_bps / 10000), 4)
                if found and found[0] <= target + timedelta(minutes=5) else None
            )
        output.append(item)
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--signals", required=True)
    parser.add_argument("--bars", required=True)
    parser.add_argument("--cost-bps", type=float, default=20)
    args = parser.parse_args()
    with open(args.signals, newline="", encoding="utf-8") as f:
        signals = list(csv.DictReader(f))
    with open(args.bars, newline="", encoding="utf-8") as f:
        bars = list(csv.DictReader(f))
    print(json.dumps({"cost_bps": args.cost_bps, "results": evaluate(signals, bars, cost_bps=args.cost_bps)}, indent=2))

if __name__ == "__main__":
    main()
