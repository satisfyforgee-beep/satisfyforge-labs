#!/usr/bin/env python3
"""Offline historical split evaluation; does not contact brokers."""
import argparse
import csv
import json

from cli import demo_data, to_bar
from zerocost_bot.engine import Settings
from zerocost_bot.evaluation import evaluate_holdout


def main():
    parser = argparse.ArgumentParser(description="Evaluate fixed breakout logic on a chronological holdout")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="Synthetic plumbing demonstration only")
    source.add_argument("--csv", help="Local CSV: symbol,time,open,high,low,close,volume")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    args = parser.parse_args()
    if args.demo:
        rows = demo_data()
    else:
        with open(args.csv, newline="", encoding="utf-8") as stream:
            rows = [to_bar(record) for record in csv.DictReader(stream)]
    report = evaluate_holdout(rows, Settings(), train_fraction=args.train_fraction)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
