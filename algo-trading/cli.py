#!/usr/bin/env python3
"""Offline replay, example simulation, and read-only IEX feed checks.

No endpoint capable of submitting live or paper brokerage orders is imported.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zerocost_bot.engine import Bar, Settings, PaperEngine
from zerocost_bot.alpaca import latest_bars, get_historical_bars


def to_bar(row):
    return Bar(str(row["symbol"]).upper(),
               datetime.fromisoformat(row["time"].replace("Z","+00:00")),
               float(row["open"]), float(row["high"]), float(row["low"]),
               float(row["close"]), int(float(row["volume"])))


def demo_data():
    """Synthetic price path for plumbing tests, NOT representative returns."""
    start=datetime(2026,10,20,13,30,tzinfo=timezone.utc)
    rows=[]
    close=9.00
    for n in range(80):
        if n < 20:
            close += .002
        elif n < 45:
            close += .04
        elif n < 60:
            close -= .07
        else:
            close += .01
        rows.append(Bar("DEMO",start+timedelta(minutes=n),close-.006,
                        close+.015,close-.02,close,
                        23000 if n>20 else 6000))
    return rows


def replay(rows, settings, output_path=None, finalize=True):
    engine=PaperEngine(settings)
    for b in sorted(rows, key=lambda x:x.time):
        engine.on_bar(b)
    if finalize:
        engine.finalize()
    report={"summary":engine.summary(),"events":engine.events,
            "disclaimer":"SIMULATION: not live orders; no guarantee of profitability"}
    if output_path:
        Path(output_path).parent.mkdir(parents=True,exist_ok=True)
        Path(output_path).write_text(json.dumps(report,indent=2,default=str)+"\n")
    return report


def run():
    p=argparse.ArgumentParser(description="Zero-cost PAPER-ONLY momentum scanner")
    p.add_argument("--demo", action="store_true",help="Generate synthetic bars and run test")
    p.add_argument("--replay",help="Read CSV: symbol,time,open,high,low,close,volume")
    p.add_argument("--iex-latest",nargs="+",metavar="SYMBOL",
                   help="Read one current completed minute from free Alpaca IEX; NO TRADES")
    p.add_argument("--alpaca-history",metavar="SYMBOL",help="Download IEX minute bars for simulation")
    p.add_argument("--from-utc",help="Historical start UTC ISO")
    p.add_argument("--to-utc",help="Historical end UTC ISO")
    p.add_argument("--starting-cash",type=float,default=1000.0)
    p.add_argument("--output",default="")
    args=p.parse_args()
    if sum(bool(z) for z in [args.demo,args.replay,args.iex_latest,args.alpaca_history])!=1:
        p.error("choose exactly one of --demo/--replay/--iex-latest/--alpaca-history")
    if args.iex_latest:
        bars=latest_bars(args.iex_latest)
        print(json.dumps([{"symbol":b.symbol,"time":b.time.isoformat(),
                           "close":b.close,"volume":b.volume} for b in bars],indent=2))
        print("READ ONLY: no trades were placed")
        return
    if args.alpaca_history:
        if not args.from_utc or not args.to_utc:
            p.error("--alpaca-history needs --from-utc and --to-utc")
        rows=get_historical_bars(args.alpaca_history,args.from_utc,args.to_utc)
        if not rows:
            print("No IEX bars returned",file=sys.stderr)
            sys.exit(2)
    elif args.demo:
        rows=demo_data()
    else:
        with open(args.replay,newline="") as f:
            rows=[to_bar(x) for x in csv.DictReader(f)]
    result=replay(rows,Settings(start_cash=args.starting_cash),args.output or None)
    print(json.dumps(result["summary"],indent=2))
    print("SIMULATION ONLY - NO BROKERAGE ORDERS")


if __name__=="__main__":
    run()
