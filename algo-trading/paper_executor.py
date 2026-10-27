#!/usr/bin/env python3
"""One-shot PAPER broker command. Never creates a recurring background task.

Default = read-only dry run; --paper-submit also requires SF_PAPER_ORDER_ENABLE.
No real-money endpoint is implemented in this file or its imports.
"""
import argparse
import json
from datetime import datetime,timedelta,timezone
from zerocost_bot.alpaca import get_historical_bars
from zerocost_bot.engine import Settings,PaperEngine
from zerocost_bot.paper_broker import PaperBroker,make_bracket
from zerocost_bot.signals import choose_signal


def proposed_order(broker,bars,now=None):
    if not bars:
        return {"action":"skip","reason":"no price data"}
    last=bars[-1]
    if last.time.tzinfo is None:
        return {"action":"skip","reason":"invalid feed timestamp"}
    signal=choose_signal(bars)
    if signal is None:
        return {"action":"skip","reason":"no volume breakout"}
    state=broker.snapshot()
    try:
        qty=broker.validate(state,last.symbol,last.time,last.close)
    except (RuntimeError,ValueError) as exc:
        return {"action":"skip","reason":str(exc)}
    key="sf-paper-v01-"+last.time.strftime("%Y%m%d%H%M")+"-"+last.symbol
    payload=make_bracket(last.symbol,qty,last.close,client_id=key)
    return {"action":"proposed_paper_bracket","bar_time":last.time.isoformat(),
            "payload":payload,"paper_account":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--symbol",default="SOFI")
    p.add_argument("--paper-submit",action="store_true",help="enable PAPER order only; requires environment kill-switch too")
    args=p.parse_args()
    symbol=args.symbol.upper()
    if not symbol.isalpha() or len(symbol)>6:
        p.error("invalid symbol")
    now=datetime.now(timezone.utc)
    begin=(now-timedelta(minutes=48)).isoformat()
    fetched=get_historical_bars(symbol,begin,now.isoformat())
    # Exclude the currently-forming minute; signals require closed bars only.
    rows=[b for b in fetched if b.time <= now-timedelta(minutes=1)]
    broker=PaperBroker()
    proposal=proposed_order(broker,rows)
    if args.paper_submit and proposal["action"]=="proposed_paper_bracket":
        # Includes an independent paper-order kill switch in broker module.
        result=broker.paper_submit(proposal["payload"],explicitly_armed=True)
        print(json.dumps({"paper_broker_result":result},indent=2))
    else:
        print(json.dumps(proposal,indent=2))
        print("READ ONLY: no brokerage orders submitted")


if __name__=="__main__":
    main()
