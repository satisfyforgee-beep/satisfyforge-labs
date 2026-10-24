#!/usr/bin/env python3
"""One-shot or foreground watcher; sandbox-only and disarmed by default."""
import argparse
import json
import os
import time
from pathlib import Path
from .runner import Plan, Runner, Journal, TradierSandbox, Halt


def main(argv=None):
    parser=argparse.ArgumentParser(description="Tradier sandbox-only options trigger watcher")
    parser.add_argument("--rules",required=True,help="local strategy JSON, never credentials")
    parser.add_argument("--journal",default="./.tradier-paper-state/orders.sqlite3")
    parser.add_argument("--watch",action="store_true",help="foreground polling until Ctrl+C")
    parser.add_argument("--interval",type=int,default=20,help="poll cadence >=15 seconds")
    parser.add_argument("--sandbox-submit",action="store_true",help="only sandbox orders; requires two other gates")
    a=parser.parse_args(argv)
    if a.interval < 15:
        parser.error("at least 15 seconds between sandbox polls")
    try:
        rules=json.loads(Path(a.rules).read_text())
        plan=Plan.from_dict(rules)
        if a.sandbox_submit and not plan.enabled:
            raise Halt("strategy file still disabled; no order")
        api=TradierSandbox()
        journal=Journal(a.journal)
        runner=Runner(api,journal,plan,paper_submit=a.sandbox_submit)
        while True:
            try:
                print(json.dumps(runner.run_once(),sort_keys=True),flush=True)
            except Halt as error:
                print(json.dumps({"action":"halt","reason":str(error),"sandbox":True}),flush=True)
                # In armed mode, fail closed rather than retry an uncertain submission.
                if a.sandbox_submit:
                    return 2
            if not a.watch:
                break
            time.sleep(a.interval)
    except (Halt,ValueError,OSError) as error:
        print(json.dumps({"action":"halt","reason":str(error),"sandbox":True}),flush=True)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
