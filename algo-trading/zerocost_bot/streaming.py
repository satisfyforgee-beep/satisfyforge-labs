"""Alpaca free IEX streaming parser and deterministic research-only dispatcher.

No broker-order methods or live-money API URLs. Real-time data is NOT the SIP
consolidated tape. Optional 'websockets' Python package required for network.
"""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Optional
from math import isfinite
import asyncio
import json
import os
from .engine import Bar
from .agents import Snapshot, ConsensusEngine

IEX_STREAM = "wss://stream.data.alpaca.markets/v2/iex"
DEFAULT_SYMBOLS = ("SOFI", "AAL", "F", "SPY")


def timestamp(raw):
    if not isinstance(raw, str):
        raise ValueError("missing feed timestamp")
    result = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("feed timestamp missing timezone")
    return result.astimezone(timezone.utc)


def parse_market_message(item: dict):
    """Map wire format to an OHLCV bar / quote; ignore control messages."""
    kind = item.get("T")
    symbol = item.get("S", "")
    if kind not in ("b", "q"):
        return None
    if (not isinstance(symbol, str) or
            not symbol.isascii() or not symbol.isalpha() or len(symbol) > 6):
        raise ValueError("bad ticker")
    moment = timestamp(item.get("t"))
    if kind == "b":
        bar = Bar(symbol, moment,
                  float(item["o"]), float(item["h"]), float(item["l"]),
                  float(item["c"]), int(item["v"]))
        bar.validate()
        return ("bar", bar)
    bid, ask = float(item["bp"]), float(item["ap"])
    if not all(isfinite(v) for v in (bid, ask)) or bid <= 0 or ask < bid:
        raise ValueError("invalid quote")
    return ("quote", (symbol, bid, ask, moment))


class LiveResearch:
    """In-memory bounded stream consumer. Restart => warm-up, never replay orders."""
    def __init__(self, symbols=DEFAULT_SYMBOLS, analyzer=None):
        self.symbols = tuple(dict.fromkeys(s.upper() for s in symbols))
        if not self.symbols or len(self.symbols) > 30:
            raise ValueError("free IEX supports maximum 30 subscriptions")
        if "SPY" not in self.symbols:
            raise ValueError("include SPY as benchmark")
        self.agent = analyzer or ConsensusEngine()
        self.bars = defaultdict(lambda: deque(maxlen=64))
        self.quotes = {}
        self.last_evaluated = {}

    def ingest(self, wire: dict, now: Optional[datetime] = None):
        now = now or datetime.now(timezone.utc)
        event = parse_market_message(wire)
        if not event:
            return None
        kind, data = event
        if kind == "bar":
            bar = data
            if bar.symbol not in self.symbols:
                return None
            seq = self.bars[bar.symbol]
            if seq and bar.time <= seq[-1].time:
                return None
            seq.append(bar)
            return None
        symbol, bid, ask, quote_time = data
        if symbol not in self.symbols:
            return None
        self.quotes[symbol] = (bid, ask, quote_time)
        seq = self.bars[symbol]
        if symbol == "SPY" or len(seq) < 20:
            return None
        last = seq[-1]
        if self.last_evaluated.get(symbol) == last.time:
            return None
        if len(self.bars["SPY"]) < 6:
            return None  # fail closed if benchmark missing
        d = self.agent.assess(Snapshot(
            symbol=symbol, bars=tuple(seq), bid=bid, ask=ask,
            quote_at=quote_time, evaluated_at=now,
            benchmark=tuple(self.bars["SPY"])
        ))
        # If a quote arrives before its minute closes, retry on the next quote.
        if any(v.agent == "data_integrity" for v in d.votes):
            return None
        self.last_evaluated[symbol] = last.time
        report = d.as_report()
        report["market_data"] = {
            "source": "alpaca_iex", "coverage": "single_venue",
            "not_consolidated": True, "live_order_authorized": False,
        }
        return report


async def stream_research(symbols=DEFAULT_SYMBOLS, output=print):
    """Only print research signals. No brokerage execution or credentials saved."""
    try:
        import websockets
    except ImportError as err:
        raise RuntimeError("Install the free optional 'websockets' package to stream IEX") from err
    key = os.getenv("ALPACA_PAPER_KEY")
    secret = os.getenv("ALPACA_PAPER_SECRET")
    if not key or not secret:
        raise RuntimeError("Missing local Alpaca PAPER data credentials")
    consumer = LiveResearch(symbols)
    retry = 1
    while True:
        try:
            async with websockets.connect(IEX_STREAM, ping_interval=20,
                                          ping_timeout=20, max_size=2**18) as ws:
                await ws.send(json.dumps({"action": "auth", "key": key, "secret": secret}))
                authorized = False
                # Only proceed after explicit authorized acknowledgement.
                for _ in range(5):
                    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
                    for item in response:
                        if item.get("T") == "success" and item.get("msg") == "authenticated":
                            authorized = True
                        if item.get("T") == "error":
                            raise RuntimeError("IEX authentication failed")
                    if authorized:
                        break
                if not authorized:
                    raise RuntimeError("IEX authorization missing")
                await ws.send(json.dumps({"action": "subscribe",
                                          "bars": list(consumer.symbols),
                                          "quotes": list(consumer.symbols)}))
                retry = 1
                async for raw in ws:
                    # Never print raw authentication or credential messages.
                    for item in json.loads(raw):
                        try:
                            report = consumer.ingest(item)
                            if report and report["action"] == "candidate":
                                output(json.dumps(report, sort_keys=True))
                        except (KeyError, ValueError, TypeError, OverflowError):
                            continue  # malformed market data is discarded
        except asyncio.CancelledError:
            raise
        except (OSError, TimeoutError, RuntimeError, websockets.exceptions.WebSocketException):
            # Missing connection / provider outage: never emit or execute a trade.
            await asyncio.sleep(retry)
            retry = min(retry * 2, 30)
