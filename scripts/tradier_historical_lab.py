#!/usr/bin/env python3
"""Sandbox-only historical strategy research: NO broker order endpoints.

Chronological training/holdout, next-session-open execution, walk-forward
indicators, explicit adverse costs and no borrowing/shorting. Stdlib only.
A research screen, never a predictive AI or executable recommendation.
"""
import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import math
import os
import statistics
import sys
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from tradier_sandbox_check import fetch_json

MIN_BARS = 180
MAX_BARS = 2500
STRATEGIES = ("trend", "breakout", "reversion")
SYMBOLS = ("SOFI", "AAL", "F", "SPY")
EASTERN = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Bar:
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: int


def safe_number(value):
    try:
        f = float(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Invalid bar number") from None
    if not math.isfinite(f):
        raise ValueError("Non-finite bar number")
    return f


def parse_history(data, *, asof=None):
    """Fail closed for absent, duplicated, unordered or malformed bars."""
    raw = (data.get("history") or {}).get("day") if isinstance(data, dict) else None
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list) or not raw or len(raw) > MAX_BARS:
        raise ValueError("Missing/invalid historical data")
    cutoff = asof or datetime.now(EASTERN).date()
    bars, previous = [], None
    for x in raw:
        if not isinstance(x, dict):
            raise ValueError("Non-object history bar")
        try:
            day = date.fromisoformat(x["date"])
            o, h, l, c = [safe_number(x[k]) for k in ("open", "high", "low", "close")]
            volume = int(x["volume"])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError("Malformed historical bar") from None
        if previous is not None and day <= previous:
            raise ValueError("Bars must be strictly chronological and unique")
        if day > cutoff or min(o, h, l, c) <= 0 or h < max(o, c, l) or l > min(o, c, h) or volume < 0:
            raise ValueError("Impossible price, volume or future date")
        bars.append(Bar(day, o, h, l, c, volume))
        previous = day
    if len(bars) < MIN_BARS:
        raise ValueError("Insufficient observations for valid holdout")
    return bars


def sandbox_history(token, symbol, start, end, getter=fetch_json):
    if (not symbol.isalpha() or not symbol.isupper() or not 1 <= len(symbol) <= 6):
        raise ValueError("Invalid uppercase stock ticker")
    start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
    if start_day >= end_day or (end_day - start_day).days > 3650:
        raise ValueError("Historical range must be positive and <=10 years")
    # Requires the existing GET-only SANDBOX allowlist.
    data = getter("/markets/history", token,
                  params={"symbol": symbol, "interval": "daily", "start": start, "end": end})
    return parse_history(data, asof=end_day)


def signals_for(bars, strategy):
    """Signal at end of day i may only use bars through day i."""
    if strategy not in STRATEGIES + ("buyhold", "cash"):
        raise ValueError("Unsupported strategy")
    closes = [b.close for b in bars]
    out, active = [], False
    for i, close in enumerate(closes):
        if strategy == "cash":
            active = False
        elif strategy == "buyhold":
            active = True
        elif i >= 50:
            ma10 = statistics.fmean(closes[i-9:i+1])
            ma20 = statistics.fmean(closes[i-19:i+1])
            ma40 = statistics.fmean(closes[i-39:i+1])
            ma50 = statistics.fmean(closes[i-49:i+1])
            if strategy == "trend":
                active = ma10 > ma40 and close > ma40
            elif strategy == "breakout":
                if not active and close > max(closes[i-20:i]) and close > ma40:
                    active = True
                if active and close < ma20:
                    active = False
            else:
                sd = statistics.pstdev(closes[i-19:i+1])
                if not active and sd > 0 and close < ma20 - 1.2 * sd and close > ma50 * 0.85:
                    active = True
                elif active and close >= ma20:
                    active = False
        else:
            active = False
        out.append(active)
    return out


def simulate(bars, signals, start, stop, *, budget=30.0, cost_bps=20.0,
             fee=0.0, max_exposure=0.85, stop_loss=0.07, circuit_breaker=0.20):
    """Signal from close[i-1] fills at next open[i], costs adverse on both sides."""
    if not (60 <= start < stop <= len(bars)):
        raise ValueError("Invalid evaluation period")
    if len(signals) != len(bars) or not 0 < budget <= 1_000_000:
        raise ValueError("Invalid budget/signals")
    if not (0 <= cost_bps <= 1000 and 0 <= fee <= 50 and 0 < max_exposure <= 1):
        raise ValueError("Unreasonable simulated costs/exposure")
    if not (0 < stop_loss <= 0.5 and 0 < circuit_breaker <= 0.5):
        raise ValueError("Invalid risk parameters")
    cash, shares, entry = float(budget), 0, 0.0
    peak = float(budget)
    max_dd, entries, exits, exposure_days, stopped = 0.0, 0, 0, 0, False
    realized, total_fee = 0.0, 0.0
    equity_curve = []
    cooldown_until = -1
    for i in range(start, stop):
        today, prior = bars[i], bars[i-1]
        desired = bool(signals[i-1])
        if shares and prior.close <= entry * (1.0 - stop_loss):
            desired = False
            cooldown_until = i + 3
        if stopped or i < cooldown_until:
            desired = False
        if shares and not desired:
            proceeds = max(0.0, today.open * (1.0 - cost_bps / 10000.0) * shares - fee)
            cash += proceeds
            realized += proceeds - entry * shares
            total_fee += fee
            shares, entry = 0, 0.0
            exits += 1
        elif not shares and desired:
            fill = today.open * (1.0 + cost_bps / 10000.0)
            qty = max(0, math.floor((min(cash, float(budget) * max_exposure) - fee) / fill))
            if qty:
                debit = fill * qty + fee
                if debit > cash + 1e-8:
                    raise ValueError("Borrowing attempted")
                cash -= debit
                shares, entry = qty, (debit / qty)
                entries += 1
                total_fee += fee
        value = cash + shares * today.close
        exposure_days += int(shares > 0)
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak if peak > 0 else 0)
        if max_dd >= circuit_breaker:
            stopped = True  # circuit breaker acts at following session open
        equity_curve.append(value)
    ending = equity_curve[-1]
    returns = [equity_curve[i] / equity_curve[i-1] - 1.0
               for i in range(1, len(equity_curve)) if equity_curve[i-1] > 0]
    vol = statistics.pstdev(returns) if len(returns) >= 2 else 0.0
    sharpe = ((statistics.fmean(returns) / vol) * math.sqrt(252)
              if vol > 1e-12 else None)
    return {
        "equity": round(ending, 4),
        "return_pct": round((ending / budget - 1) * 100, 4),
        "max_dd_pct": round(max_dd * 100, 4),
        "sharpe": round(sharpe, 4) if sharpe is not None else None,
        "entries": entries, "exits": exits,
        "exposure_pct": round(exposure_days / (stop - start) * 100, 2),
        "realized_pnl": round(realized, 4),
        "open_shares": shares, "fees": round(total_fee, 4),
        "circuit_breaker": stopped,
    }


def analyze_symbol(bars, *, budget=30.0, cost_bps=20.0, fee=0.0):
    """Select on training ONLY; evaluate winning training candidate on holdout."""
    if len(bars) < MIN_BARS:
        raise ValueError("Insufficient complete bars")
    split = int(len(bars) * 0.7)
    if split < 100 or len(bars) - split < 50:
        raise ValueError("Training/holdout too small")
    # Warm-up begins at 60 and everything after split remains sealed for selection.
    trial = {}
    for strategy in STRATEGIES:
        signals = signals_for(bars, strategy)
        train = simulate(bars, signals, 60, split, budget=budget,
                         cost_bps=cost_bps, fee=fee)
        trial[strategy] = train
    viable = [(name, result) for name, result in trial.items()
              if result["entries"] >= 2 and result["exits"] >= 1]
    # Explicit abstention when training evidence is inadequate.
    selected = (max(viable, key=lambda pair: (
        pair[1]["return_pct"] - 1.5 * pair[1]["max_dd_pct"]
        - 0.15 * pair[1]["entries"], -pair[1]["max_dd_pct"], pair[0]))[0]
                if viable else None)
    baseline = simulate(bars, signals_for(bars, "buyhold"), split, len(bars),
                        budget=budget, cost_bps=cost_bps, fee=fee)
    outcome = None
    if selected:
        sig = signals_for(bars, selected)
        holdout = simulate(bars, sig, split, len(bars),
                           budget=budget, cost_bps=cost_bps, fee=fee)
        stress = simulate(bars, sig, split, len(bars),
                          budget=budget, cost_bps=cost_bps * 3, fee=fee)
        # Always report holdout result; label limited/poor sample as PASS, not victory.
        gate = ("INSUFFICIENT EVIDENCE" if holdout["entries"] < 3 or holdout["exits"] < 2
                else "FAIL" if holdout["return_pct"] <= max(0, baseline["return_pct"])
                              or stress["return_pct"] <= 0
                              or holdout["max_dd_pct"] > 15
                else "RESEARCH ONLY - NOT VERIFIED EDGE")
        outcome = {"holdout": holdout, "stress_3x": stress, "gate": gate}
    return {
        "bars": len(bars), "train_start": bars[60].day.isoformat(),
        "train_end": bars[split-1].day.isoformat(),
        "holdout_start": bars[split].day.isoformat(),
        "holdout_end": bars[-1].day.isoformat(),
        "selected": selected, "training": trial, "test": outcome,
        "buyhold_holdout": baseline,
        "note": "Daily unadjusted bars; no corporate-action/borrow/tax model; "
                "next-open fills hypothetical; selection only on training",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Tradier historical holdout research")
    parser.add_argument("--symbols", default="SOFI,AAL,F")
    parser.add_argument("--start", default="2025-01-02")
    parser.add_argument("--end", default=None)
    parser.add_argument("--budget", type=float, default=30.0)
    parser.add_argument("--cost-bps", type=float, default=20.0,
                        help="Per-side adverse execution cost in basis points")
    parser.add_argument("--fee", type=float, default=0.0,
                        help="Hypothetical fixed fee per order")
    parser.add_argument("--require-complete", action="store_true",
                        help="Fail CI when any requested symbol cannot be validated")
    args = parser.parse_args(argv)
    token = os.environ.get("TRADIER_SANDBOX_TOKEN", "").strip()
    try:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
        if not 1 <= len(symbols) <= 4 or len(set(symbols)) != len(symbols):
            raise ValueError("Invalid symbol count")
        if not token:
            raise ValueError("Sandbox key is required")
        end = args.end or (datetime.now(EASTERN).date() - timedelta(days=1)).isoformat()
        if date.fromisoformat(end) >= datetime.now(EASTERN).date():
            raise ValueError("End must be before today (completed sessions only)")
        if not 0 < args.budget <= 1_000_000 or not math.isfinite(args.budget):
            raise ValueError("Invalid budget")
        if not 0 <= args.cost_bps <= 1000 or not math.isfinite(args.cost_bps):
            raise ValueError("Invalid execution cost")
        if not 0 <= args.fee <= 50 or not math.isfinite(args.fee):
            raise ValueError("Invalid fee")
        failed = 0
        for symbol in symbols:
            try:
                bars = sandbox_history(token, symbol, args.start, end)
                report = analyze_symbol(bars, budget=args.budget,
                                        cost_bps=args.cost_bps, fee=args.fee)
                print(json.dumps({"symbol": symbol, **report}, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False))
            except (ValueError, OSError, HTTPError, URLError) as error:
                # Only fixed known diagnostic labels. Never print provider response,
                # account details, token, full exception string, URL or headers.
                failed += 1
                if isinstance(error, HTTPError):
                    code = "HTTP_" + str(error.code) if error.code in (400,401,403,404,429,500,502,503) else "HTTP_ERROR"
                elif isinstance(error, ValueError):
                    known = {"Insufficient observations for valid holdout": "TOO_FEW_BARS",
                             "Missing/invalid historical data": "MISSING_HISTORY",
                             "Bars must be strictly chronological and unique": "UNSORTED_HISTORY",
                             "Impossible price, volume or future date": "INVALID_OHLC_OR_DATE",
                             "Malformed historical bar": "MALFORMED_BAR",
                             "Non-object history bar": "MALFORMED_BAR"}
                    code = known.get(str(error), "UNEXPECTED_HISTORY_FORMAT")
                else:
                    code = "NETWORK_ERROR"
                print(json.dumps({"symbol": symbol, "status": "NO_RESULT", "reason": code}))
        print("RESEARCH ONLY: no orders or live prices. Backtests can overfit; "
              "history may be unadjusted and $30 whole shares may prevent trades.")
        return 3 if (args.require_complete and failed) or failed == len(symbols) else 0
    except (ValueError, TypeError):
        print("Invalid input or sandbox configuration; no trades placed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
