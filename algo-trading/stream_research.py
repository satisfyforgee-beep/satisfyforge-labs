#!/usr/bin/env python3
"""READ-ONLY IEX feed research runner. This program has NO trade execution."""
import argparse
import asyncio
from zerocost_bot.streaming import stream_research


def main():
    p=argparse.ArgumentParser(description="Zero-cost IEX streaming RESEARCH ONLY")
    p.add_argument("--symbols", nargs="+", default=["SOFI", "AAL", "F", "SPY"],
                   help="Up to 30 IEX stock tickers; SPY required")
    args=p.parse_args()
    asyncio.run(stream_research(args.symbols))


if __name__=="__main__":
    main()
