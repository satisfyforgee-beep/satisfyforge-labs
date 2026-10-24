#!/usr/bin/env python3
"""Tradier sandbox delayed-quote screen + local hypothetical stock ledger.

Read-only. Deliberately has no brokerage-order endpoints or production hostname.
No account identifiers, secrets or private journal rows are printed.
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tradier_sandbox_check import fetch_json

MAX_SYMBOLS = 6
DEFAULT_SYMBOLS = ("SOFI", "AAL", "F", "PLTR", "SPY")
DEFAULT_BUDGET = Decimal("30.00")
MAX_QUOTE_AGE_MINUTES = Decimal("30")


def money(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid number") from None
    if not result.is_finite():
        raise ValueError("Non-finite number")
    return result


def symbols_from_text(value):
    symbols = [item.strip().upper() for item in value.split(",")]
    if not symbols or len(symbols) > MAX_SYMBOLS:
        raise ValueError("Provide 1 to 6 symbols")
    if any(not s.isalpha() or len(s) > 6 for s in symbols):
        raise ValueError("Only alphabetic stock/ETF symbols of up to six characters")
    if len(set(symbols)) != len(symbols):
        raise ValueError("Duplicate symbol")
    return symbols


def quote_timestamp(quote):
    # Tradier documents epoch milliseconds for trade_date, bid_date, ask_date.
    times = []
    for field in ("bid_date", "ask_date", "trade_date"):
        value = quote.get(field)
        if value is not None:
            try:
                stamp = datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
                times.append(stamp)
            except (ValueError, TypeError, OverflowError, OSError):
                pass
    return min(times) if times else None  # Oldest component controls freshness.


def screen_snapshot(token, symbols, budget=DEFAULT_BUDGET, now=None, getter=fetch_json):
    if not token:
        raise ValueError("Missing sandbox token")
    if money(budget) <= 0:
        raise ValueError("Budget must be positive")
    if not symbols or len(symbols) > MAX_SYMBOLS or len(set(symbols)) != len(symbols):
        raise ValueError("Invalid symbol list")
    if any(not s.isalpha() or len(s) > 6 or s != s.upper() for s in symbols):
        raise ValueError("Only uppercase alphabetic symbols")
    response = getter("/markets/quotes", token,
                      params={"symbols": ",".join(symbols), "greeks": "false"})
    raw = (response.get("quotes") or {}).get("quote")
    items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    lookup = {x["symbol"].upper(): x for x in items if isinstance(x, dict)
              and isinstance(x.get("symbol"), str)}
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("UTC-aware clock required")
    rows = []
    for symbol in symbols:
        quote = lookup.get(symbol, {})
        try:
            bid = money(quote.get("bid"))
            ask = money(quote.get("ask"))
        except ValueError:
            bid = ask = Decimal("0")
        reasons = []
        if quote.get("type") not in ("stock", "etf"):
            reasons.append("not-confirmed-stock-or-etf")
        if bid <= 0 or ask <= 0 or ask < bid:
            reasons.append("invalid-or-missing-bid-ask")
        recorded = quote_timestamp(quote)
        age = None
        if recorded is None:
            reasons.append("timestamp-unavailable")
        else:
            age = Decimal(str((clock - recorded).total_seconds())) / Decimal("60")
            if age < -2 or age > MAX_QUOTE_AGE_MINUTES:
                reasons.append("stale-or-invalid-time")
        qty = int(money(budget) // ask) if ask > 0 else 0
        if qty == 0:
            reasons.append("over-budget-for-whole-share")
        spread_pct = ((ask - bid) / ask * 100) if ask > 0 and bid > 0 and ask >= bid else None
        if spread_pct is not None and spread_pct > Decimal("1"):
            reasons.append("wide-spread")
        rows.append({
            "symbol": symbol, "bid": bid, "ask": ask, "shares": qty,
            "spread_pct": spread_pct, "age_minutes": age,
            "flags": reasons, "asof_utc": recorded.isoformat() if recorded else None,
        })
    return rows


def print_screen(rows, budget):
    print("Tradier sandbox: delayed research screen (NOT trade signals)")
    print(f"Hypothetical cash budget: ${money(budget):.2f}; stocks/ETFs only, whole shares")
    for row in rows:
        bid = f"${row['bid']:.2f}" if row["bid"] > 0 else "n/a"
        ask = f"${row['ask']:.2f}" if row["ask"] > 0 else "n/a"
        spread = f"{row['spread_pct']:.2f}%" if row["spread_pct"] is not None else "n/a"
        flags = ",".join(row["flags"]) if row["flags"] else "delayed-valid-snapshot-only"
        print(f"{row['symbol']}: bid={bid} ask={ask} spread={spread} "
              f"max_whole_shares={row['shares']} asof_UTC={row['asof_utc'] or 'unknown'} "
              f"flags={flags}")
    print("Sandbox quotes are delayed (~15m); timestamps may be stale after close.")
    print("No real-time prices, recommendations, orders, account changes or transfers.")


def replay_hypothetical(csv_path, starting_cash=DEFAULT_BUDGET, fee=Decimal("0")):
    """Local-only replay of explicitly hypothetical BUY/SELL decisions.

    A BUY is filled at supplied ask, SELL at supplied bid, never at midpoint.
    Input rows are not written or uploaded; caller provides local CSV.
    """
    cash, charge = money(starting_cash), money(fee)
    if cash <= 0 or charge < 0:
        raise ValueError("Invalid cash or fee")
    holdings, basis, marks = {}, {}, {}
    realized = Decimal("0")
    trades = 0
    previous = None
    with open(Path(csv_path), encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "symbol", "action", "shares", "bid", "ask"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV requires timestamp,symbol,action,shares,bid,ask")
        for n, row in enumerate(reader, start=2):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                if timestamp.tzinfo is None or (previous is not None and timestamp < previous):
                    raise ValueError("Timestamp must be offset-aware and sorted")
                previous = timestamp
                symbol, action = row["symbol"].upper(), row["action"].upper()
                if not symbol.isalpha() or len(symbol) > 6 or action not in ("BUY", "SELL"):
                    raise ValueError("Unsupported symbol/action")
                qty = int(row["shares"])
                if qty <= 0 or str(qty) != row["shares"].strip():
                    raise ValueError("Whole-share positive quantity required")
                bid, ask = money(row["bid"]), money(row["ask"])
                if bid <= 0 or ask < bid:
                    raise ValueError("Invalid bid/ask")
                marks[symbol] = bid
                owned = holdings.get(symbol, 0)
                cost = basis.get(symbol, Decimal("0"))
                if action == "BUY":
                    debit = ask * qty + charge
                    if debit > cash:
                        raise ValueError("Insufficient simulated cash; no leverage")
                    cash -= debit
                    holdings[symbol] = owned + qty
                    basis[symbol] = cost + debit
                else:
                    if qty > owned:
                        raise ValueError("Cannot sell more than simulated holdings")
                    allocated = cost * Decimal(qty) / Decimal(owned)
                    proceeds = bid * qty - charge
                    cash += proceeds
                    holdings[symbol] = owned - qty
                    basis[symbol] = cost - allocated
                    realized += proceeds - allocated
                trades += 1
            except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
                raise ValueError(f"Hypothetical CSV row {n} invalid: {exc}") from None
    marked_value = sum((marks[s] * qty for s, qty in holdings.items()), Decimal("0"))
    unrl = marked_value - sum(basis.values(), Decimal("0"))
    equity = cash + marked_value
    return {"cash": cash, "market_value": marked_value, "equity": equity,
            "realized_pnl": realized, "unrealized_pnl": unrl,
            "net_pnl": equity - money(starting_cash),
            "trades": trades, "open_positions": sum(q > 0 for q in holdings.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only sandbox scanner and local hypothetical ledger")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true", help="Read delayed SANDBOX quotes only")
    group.add_argument("--replay", metavar="LOCAL_CSV", help="Replay hypothetical stock decisions offline")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                        help="Up to 6 alphabetic stock/ETF symbols")
    parser.add_argument("--budget", default="30.00", help="Hypothetical starting cash")
    parser.add_argument("--fee", default="0", help="Hypothetical per-order fee for replay; default 0")
    args = parser.parse_args(argv)
    try:
        budget = money(args.budget)
        if args.scan:
            token = os.environ.get("TRADIER_SANDBOX_TOKEN", "").strip()
            if not token:
                raise ValueError("TRADIER_SANDBOX_TOKEN not available")
            rows = screen_snapshot(token, symbols_from_text(args.symbols), budget)
            print_screen(rows, budget)
        else:
            result = replay_hypothetical(args.replay, budget, money(args.fee))
            print("HYPOTHETICAL only: local replay, not sandbox fills or realized broker gains")
            for key, value in result.items():
                print(f"{key}: {value}")
        return 0
    except (ValueError, OSError):
        print("Paper lab failed: check inputs, token permissions and sandbox availability. "
              "No orders were submitted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
