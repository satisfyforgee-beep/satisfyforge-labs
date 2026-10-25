#!/usr/bin/env python3
"""Read-only Tradier sandbox quote screen and local hypothetical ledger."""
import argparse
import csv
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tradier_sandbox_check import fetch_json

MAX_UNIVERSE_SYMBOLS = 500
QUOTE_BATCH_SIZE = 50
DEFAULT_SYMBOLS = ("SOFI", "AAL", "F", "PLTR", "SPY")
DEFAULT_BUDGET = Decimal("30.00")
MAX_QUOTE_AGE_MINUTES = Decimal("30")
DEFAULT_MAX_SPREAD_PCT = Decimal("1")
DEFAULT_MIN_AVERAGE_VOLUME = 500_000
MAX_UNIVERSE_FILE_BYTES = 64 * 1024


def money(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid number") from None
    if not result.is_finite():
        raise ValueError("Non-finite number")
    return result


def _validate_symbols(symbols):
    if not symbols or len(symbols) > MAX_UNIVERSE_SYMBOLS:
        raise ValueError("Provide 1 to 500 symbols")
    if any(not s.isalpha() or len(s) > 6 or s != s.upper() for s in symbols):
        raise ValueError("Only uppercase alphabetic stock/ETF symbols of up to six characters")
    if len(set(symbols)) != len(symbols):
        raise ValueError("Duplicate symbol")
    return symbols


def symbols_from_text(value):
    if not isinstance(value, str):
        raise ValueError("Symbol text required")
    return _validate_symbols([item.strip().upper() for item in value.split(",") if item.strip()])


def symbols_from_file(path):
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("Universe must be one regular, non-symlinked file")
    if source.stat().st_size > MAX_UNIVERSE_FILE_BYTES:
        raise ValueError("Universe file is too large")
    values = []
    for line in source.read_text(encoding="utf-8").splitlines():
        clean = line.split("#", 1)[0].strip()
        if clean:
            values.extend(x.strip().upper() for x in clean.split(",") if x.strip())
    return _validate_symbols(values)


def quote_timestamp(quote):
    times = []
    for field in ("bid_date", "ask_date", "trade_date"):
        value = quote.get(field)
        if value is not None:
            try:
                times.append(datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc))
            except (ValueError, TypeError, OverflowError, OSError):
                pass
    return min(times) if times else None


def _nonnegative_int(value):
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 and str(result) == str(value).strip() else None


def _batches(values, size=QUOTE_BATCH_SIZE):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def screen_snapshot(token, symbols, budget=DEFAULT_BUDGET, now=None, getter=fetch_json,
                    max_spread_pct=DEFAULT_MAX_SPREAD_PCT,
                    min_average_volume=DEFAULT_MIN_AVERAGE_VOLUME):
    if not token:
        raise ValueError("Missing sandbox token")
    symbols = _validate_symbols(list(symbols))
    budget, max_spread_pct = money(budget), money(max_spread_pct)
    if budget <= 0 or max_spread_pct <= 0:
        raise ValueError("Budget and maximum spread must be positive")
    if type(min_average_volume) is not int or min_average_volume < 0:
        raise ValueError("Minimum average volume must be a nonnegative integer")
    lookup = {}
    for batch in _batches(symbols):
        response = getter("/markets/quotes", token,
                          params={"symbols": ",".join(batch), "greeks": "false"})
        raw = (response.get("quotes") or {}).get("quote")
        items = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
        requested = set(batch)
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("symbol"), str):
                continue
            symbol = item["symbol"].upper()
            if symbol in requested:
                if symbol in lookup:
                    raise ValueError("Provider returned a duplicate quote")
                lookup[symbol] = item
    clock = now or datetime.now(timezone.utc)
    if clock.tzinfo is None:
        raise ValueError("UTC-aware clock required")
    rows = []
    for symbol in symbols:
        quote = lookup.get(symbol, {})
        try:
            bid, ask = money(quote.get("bid")), money(quote.get("ask"))
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
        qty = int(budget // ask) if ask > 0 else 0
        if qty == 0:
            reasons.append("over-budget-for-whole-share")
        spread_pct = ((ask - bid) / ask * 100) if ask > 0 and bid > 0 and ask >= bid else None
        if spread_pct is not None and spread_pct > max_spread_pct:
            reasons.append("wide-spread")
        average_volume = _nonnegative_int(quote.get("average_volume"))
        volume = _nonnegative_int(quote.get("volume"))
        bid_size = _nonnegative_int(quote.get("bidsize"))
        ask_size = _nonnegative_int(quote.get("asksize"))
        if average_volume is None or volume is None:
            reasons.append("liquidity-unavailable")
        elif average_volume < min_average_volume:
            reasons.append("low-average-volume")
        if bid_size is None or ask_size is None or bid_size < 1 or ask_size < 1:
            reasons.append("top-of-book-size-unavailable")
        spread_cost = (ask - bid) * qty if spread_pct is not None else None
        rows.append({
            "symbol": symbol, "bid": bid, "ask": ask, "shares": qty,
            "spread_pct": spread_pct, "spread_cost": spread_cost,
            "average_volume": average_volume, "volume": volume,
            "bid_size": bid_size, "ask_size": ask_size,
            "age_minutes": age, "flags": reasons,
            "eligible": not reasons,
            "asof_utc": recorded.isoformat() if recorded else None,
        })
    return rows


def rank_research_candidates(rows):
    """Deterministic data-quality ranking, never a recommendation or signal."""
    return sorted((row for row in rows if row["eligible"]), key=lambda row: (
        row["spread_pct"], row["spread_cost"], -row["average_volume"], row["symbol"]))


def print_screen(rows, budget, top=25):
    top = int(top)
    if top < 1 or top > 100:
        raise ValueError("Top count must be 1 to 100")
    ranked = rank_research_candidates(rows)
    print("Tradier sandbox: delayed broad-universe research screen (NOT trade signals)")
    print(f"scanned={len(rows)} eligible={len(ranked)} rejected={len(rows)-len(ranked)} budget=${money(budget):.2f}")
    for row in ranked[:top]:
        print(f"{row['symbol']}: ask=${row['ask']:.2f} spread={row['spread_pct']:.3f}% "
              f"spread_cost=${row['spread_cost']:.2f} avg_volume={row['average_volume']} "
              f"max_whole_shares={row['shares']} asof_UTC={row['asof_utc']}")
    reasons = Counter(flag for row in rows for flag in row["flags"])
    if reasons:
        print("rejection_counts=" + ",".join(f"{key}:{reasons[key]}" for key in sorted(reasons)))
    print("Ranking measures quote usability/liquidity only; it predicts neither direction nor profit.")
    print("No recommendations, orders, account changes or transfers.")


def replay_hypothetical(csv_path, starting_cash=DEFAULT_BUDGET, fee=Decimal("0")):
    cash, charge = money(starting_cash), money(fee)
    if cash <= 0 or charge < 0:
        raise ValueError("Invalid cash or fee")
    holdings, basis, marks = {}, {}, {}
    realized, trades, previous = Decimal("0"), 0, None
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
                owned, cost = holdings.get(symbol, 0), basis.get(symbol, Decimal("0"))
                if action == "BUY":
                    debit = ask * qty + charge
                    if debit > cash:
                        raise ValueError("Insufficient simulated cash; no leverage")
                    cash -= debit
                    holdings[symbol], basis[symbol] = owned + qty, cost + debit
                else:
                    if qty > owned:
                        raise ValueError("Cannot sell more than simulated holdings")
                    allocated = cost * Decimal(qty) / Decimal(owned)
                    proceeds = bid * qty - charge
                    cash += proceeds
                    holdings[symbol], basis[symbol] = owned - qty, cost - allocated
                    realized += proceeds - allocated
                trades += 1
            except (KeyError, ValueError, TypeError, InvalidOperation) as exc:
                raise ValueError(f"Hypothetical CSV row {n} invalid: {exc}") from None
    marked_value = sum((marks[s] * qty for s, qty in holdings.items()), Decimal("0"))
    unrl = marked_value - sum(basis.values(), Decimal("0"))
    equity = cash + marked_value
    return {"cash": cash, "market_value": marked_value, "equity": equity,
            "realized_pnl": realized, "unrealized_pnl": unrl,
            "net_pnl": equity - money(starting_cash), "trades": trades,
            "open_positions": sum(q > 0 for q in holdings.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only broad scanner and local hypothetical ledger")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", action="store_true")
    group.add_argument("--replay", metavar="LOCAL_CSV")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--symbols")
    source.add_argument("--symbols-file")
    parser.add_argument("--budget", default="30.00")
    parser.add_argument("--fee", default="0")
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--max-spread-pct", default="1")
    parser.add_argument("--min-average-volume", type=int, default=DEFAULT_MIN_AVERAGE_VOLUME)
    args = parser.parse_args(argv)
    try:
        budget = money(args.budget)
        if args.scan:
            token = os.environ.get("TRADIER_SANDBOX_TOKEN", "").strip()
            if not token:
                raise ValueError("TRADIER_SANDBOX_TOKEN not available")
            symbols = symbols_from_file(args.symbols_file) if args.symbols_file else symbols_from_text(args.symbols or ",".join(DEFAULT_SYMBOLS))
            rows = screen_snapshot(token, symbols, budget,
                                   max_spread_pct=args.max_spread_pct,
                                   min_average_volume=args.min_average_volume)
            print_screen(rows, budget, args.top)
        else:
            result = replay_hypothetical(args.replay, budget, money(args.fee))
            print("HYPOTHETICAL only: local replay, not sandbox fills or realized broker gains")
            for key, value in result.items():
                print(f"{key}: {value}")
        return 0
    except (ValueError, OSError):
        print("Paper lab failed: check inputs, token permissions and sandbox availability. No orders were submitted.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
