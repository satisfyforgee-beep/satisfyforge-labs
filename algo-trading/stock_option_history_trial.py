#!/usr/bin/env python3
"""Replay US STOCK and long OPTION virtual trades with actual Tradier history.

Exactly GET-only Sandbox market data. All fills are historical, estimated,
not broker-paper or live orders; option daily OHLC is NOT tradable NBBO.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from zerocost_bot.stock_option_virtual_replay import (
    STOCK_NAMES, OCC_NAMES, stock_bars, option_days,
    stock_control, option_control,
)
from zerocost_bot.engine import Bar, PaperEngine, Settings


def run():
    token = os.environ.get("TRADIER_SANDBOX_TOKEN")
    if not token:
        raise ValueError("sandbox credential not available in local process")
    now = datetime.now(timezone.utc)
    stock_rows = {symbol: stock_bars(symbol, token=token)
                  for symbol in STOCK_NAMES}
    option_rows = {symbol: option_days(symbol, token=token)
                   for symbol in OCC_NAMES}
    # Stock-only previously implemented volume-breakout engine.
    # This strategy is fixed before seeing today's outcomes.
    engine = PaperEngine(Settings(
        start_cash=150, max_position_fraction=.20,
        max_daily_loss_fraction=.03, stop_loss_fraction=.02,
        take_profit_fraction=.035, max_round_trips_per_day=3,
        lookback=12, min_history_bars=13, cooldown_bars=4,
        min_volume=1000, slippage_bps=5.0,
        fee_per_order=.01, minimum_cash_buffer=1.0,
    ))
    feed = []
    for symbol, records in stock_rows.items():
        for t, op, hi, lo, cl, vol in records:
            feed.append(Bar(symbol, t, float(op), float(hi),
                            float(lo), float(cl), vol))
    for bar in sorted(feed, key=lambda b:(b.time, b.symbol)):
        engine.on_bar(bar)
    engine.finalize()

    stock_report = stock_control(stock_rows)
    option_report = option_control(option_rows)
    report = {
        "mode": "HISTORICAL_STOCK_OPTION_OFFLINE_VIRTUAL_TRADES_NO_BROKER",
        "as_of_utc": now.isoformat(),
        "source": "TRADIER_SANDBOX_READ_ONLY_MARKET_HISTORY",
        "as_of_session": "2026-10-26_US_EQUITY_REGULAR_MARKET",
        "stock_symbols": list(STOCK_NAMES),
        "stock_five_minute_bar_counts": {s:len(v) for s,v in stock_rows.items()},
        "option_symbols": list(OCC_NAMES),
        "option_session_counts": {s:len(v) for s,v in option_rows.items()},
        "stock_control": stock_report,
        "stock_breakout": {
            "mode": "HISTORICAL_PAPER_ENGINE_NO_BROKER",
            **engine.summary(),
            "events": engine.events,
            "broker_orders_sent": 0,
        },
        "long_option_control": option_report,
        "notes": [
            "Independent hypothetical $150 stock and option accounts: do NOT sum their net P/L with each other or with crypto.",
            "One day of stock bars and 18 dates of options cannot establish an edge.",
            "Option daily OHLC contains no bid/ask spread, no fill certainty, no early assignment, no Greeks. Modeled 1c each way, 65c per contract per side are assumptions.",
            "Historical option fills are education only; production/sandbox trading permissions never enabled.",
        ],
        "broker_paper_orders_sent": 0,
        "live_money_orders_sent": 0,
    }
    folder = Path.home()/".satisfyforge"/"trading"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    filename = "stock_option_history_virtual_" + now.strftime("%Y%m%dT%H%M%SZ") + ".json"
    path = folder/filename
    handle = os.open(str(path), os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
    with os.fdopen(handle,"w") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    print(json.dumps({
        "mode": report["mode"],
        "session": report["as_of_session"],
        "stocks": {
            "control_closed_trades": stock_report["virtual_completed_roundtrips"],
            "control_net_pnl": stock_report["net_pnl_after_model_costs"],
            "breakout_closed_trades": engine.summary()["round_trips"],
            "breakout_net_pnl": str(engine.summary()["net_pnl"]),
        },
        "options": {
            "closed_virtual_trades": option_report["virtual_completed_roundtrips"],
            "winning_virtual_trades": option_report["winners"],
            "net_pnl_after_model_costs": option_report["net_pnl_after_model_costs"],
        },
        "independent_historical_virtual_accounts": True,
        "private_evidence_file": str(path),
        "broker_paper_orders_sent": 0,
        "live_money_orders_sent": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        run()
    except (ValueError, OSError, TypeError, KeyError, RuntimeError) as exc:
        print(json.dumps({
            "state": "HISTORICAL_STOCK_OPTION_REPLAY_HALTED",
            "failure_class": type(exc).__name__,
            "broker_paper_orders_sent": 0, "live_money_orders_sent": 0,
        }, sort_keys=True))
        sys.exit(1)
