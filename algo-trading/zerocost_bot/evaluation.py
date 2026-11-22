"""Out-of-sample *historical simulation*, without training or broker calls.

The fixed strategy is replayed independently on chronological train and test
windows.  No settings are tuned on either set.  Results are diagnostic, not a
forecast; data quality, fees and market coverage still matter greatly.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from math import isfinite

from .engine import Bar, PaperEngine, Settings


def _observed_time(value, label: str) -> datetime:
    """Parse local capture provenance; this is not a provider timestamp."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid {label}") from None
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise ValueError(f"Missing timezone-aware {label}")
    return value.astimezone(timezone.utc)


def _trade_decimal(value, label: str) -> str:
    """Return a canonical positive decimal without accepting binary floats."""
    if isinstance(value, float):
        raise ValueError(f"Invalid {label}")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid {label}") from None
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"Invalid {label}")
    return format(parsed, "f")


def classify_stock_trade_bar_updates(*, tape: str, bar_type: str,
                                     conditions: list[str]) -> dict:
    """Classify a bounded set of Alpaca/SIP trade-condition bar updates.

    This is an offline negative control for captured research data, not a bar
    builder.  Unsupported condition/tape combinations fail closed rather than
    guessing.  Even an eligible price update is never promoted to executable
    quote or fill evidence.
    """
    if tape not in {"A", "B", "C", "O"}:
        raise ValueError("Unsupported stock-trade tape")
    if bar_type not in {"minute", "daily"}:
        raise ValueError("Unsupported stock-bar type")
    if (not isinstance(conditions, list) or not conditions
            or not all(isinstance(item, str) and item for item in conditions)):
        raise ValueError("Stock-trade conditions required")
    if len(set(conditions)) != len(conditions):
        raise ValueError("Duplicate stock-trade condition")

    always = "ALWAYS"
    first = "FIRST_ONLY"
    never = "NEVER"
    rank = {never: 0, first: 1, always: 2}

    def rule(code: str) -> tuple[str, str, str]:
        if code == "@":
            if tape not in {"C", "O"}:
                raise ValueError("Trade condition conflicts with tape")
            return always, always, always
        if code == "I":
            return never, never, always
        if code == "P":
            if bar_type == "minute":
                return never, never, always
            return first, always, always
        if code == "4":
            if tape == "O":
                raise ValueError("Trade condition conflicts with tape")
            if bar_type == "minute":
                return never, never, always
            return first, always, always
        raise ValueError("Unknown stock-trade condition")

    component_rules = [rule(code) for code in conditions]
    combined = tuple(min((item[index] for item in component_rules),
                         key=rank.get) for index in range(3))
    open_close, high_low, volume = combined
    volume_only = (open_close == never and high_low == never
                   and volume == always)
    can_seed_complete_bar = (open_close in {always, first}
                             and high_low == always and volume == always)
    return {
        "mode": "OFFLINE_STOCK_TRADE_BAR_CONDITION_AUDIT",
        "tape": tape,
        "bar_type": bar_type,
        "conditions": list(conditions),
        "open_close_update": open_close,
        "high_low_update": high_low,
        "volume_update": volume,
        "volume_only": volume_only,
        "can_seed_complete_bar": can_seed_complete_bar,
        "execution_evidence": False,
        "fill_inference_allowed": False,
        "warning": "Aggregation audit only; not quote, fill, order, or alpha evidence.",
    }


def replay_crypto_quotes_as_of(pages: list[dict], *, as_of: datetime,
                               location: str, symbols: list[str],
                               start: datetime, end: datetime) -> dict:
    """Audit one complete offline Alpaca crypto-quote capture.

    Alpaca's historical crypto quote limit applies across all requested
    symbols, so a first page is not proof of complete symbol coverage. This
    routine exhausts one captured token chain, binds it to explicit location,
    interval and entitlement provenance, and never treats quotes as fills.
    """
    cutoff = _observed_time(as_of, "crypto-quote cutoff")
    requested_start = _observed_time(start, "crypto-quote start")
    requested_end = _observed_time(end, "crypto-quote end")
    if requested_start >= requested_end or requested_end > cutoff:
        raise ValueError("Invalid crypto-quote interval")
    supported_locations = {"us", "us-1", "us-2", "eu-1", "bs-1"}
    if location not in supported_locations:
        raise ValueError("Unsupported crypto-quote location")
    us1_start = datetime(2025, 10, 14, tzinfo=timezone.utc)
    if location == "us-1" and requested_start < us1_start:
        raise ValueError("Crypto-quote interval predates us-1 coverage")
    if (not isinstance(symbols, list) or not symbols
            or not all(isinstance(item, str) and item and "/" in item
                       and item == item.upper()
                       and not any(ch.isspace() for ch in item)
                       for item in symbols)
            or len(set(symbols)) != len(symbols)):
        raise ValueError("Explicit unique crypto symbols required")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Crypto-quote capture pages required")

    requested_symbols = tuple(symbols)
    snapshots: dict[str, list[tuple[dict, datetime, str]]] = {}
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Malformed crypto-quote capture page")
        snapshot_id = page.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("Missing crypto-quote snapshot provenance")
        observed = _observed_time(page.get("observed_at"),
                                  "crypto-quote observed_at")
        entitlement = page.get("entitlement")
        if entitlement not in {"real_time", "delayed_15m"}:
            raise ValueError("Explicit crypto-quote entitlement required")
        if (page.get("source") != "ALPACA_CRYPTO_QUOTES"
                or page.get("location") != location
                or tuple(page.get("symbols", [])) != requested_symbols
                or _observed_time(page.get("start"), "crypto-quote page start")
                   != requested_start
                or _observed_time(page.get("end"), "crypto-quote page end")
                   != requested_end):
            raise ValueError("Crypto-quote query provenance mismatch")
        if requested_end > observed:
            raise ValueError("Crypto-quote request ends after capture")
        if (entitlement == "delayed_15m"
                and requested_end > observed - timedelta(minutes=15)):
            raise ValueError("Crypto-quote interval violates delayed entitlement")
        token = page.get("page_token")
        next_token = page.get("next_page_token")
        for value in (token, next_token):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError("Invalid crypto-quote page token")
        if not isinstance(page.get("quotes"), list):
            raise ValueError("Crypto-quote page records missing")
        snapshots.setdefault(snapshot_id, []).append((page, observed, entitlement))

    eligible: list[tuple[datetime, str]] = []
    for snapshot_id, rows in snapshots.items():
        observed = {stamp for _, stamp, _ in rows}
        metadata = {(page["source"], page["location"],
                     tuple(page["symbols"]), page["start"], page["end"],
                     entitlement)
                    for page, _, entitlement in rows}
        if len(observed) != 1 or len(metadata) != 1:
            raise ValueError("Crypto-quote snapshot metadata conflict")
        stamp = next(iter(observed))
        if stamp <= cutoff:
            eligible.append((stamp, snapshot_id))
    if not eligible:
        raise ValueError("No crypto-quote snapshot existed by cutoff")
    newest = max(stamp for stamp, _ in eligible)
    candidate_ids = [item for stamp, item in eligible if stamp == newest]
    if len(candidate_ids) != 1:
        raise ValueError("Ambiguous crypto-quote snapshot at cutoff")

    snapshot_id = candidate_ids[0]
    rows = snapshots[snapshot_id]
    by_token: dict[str | None, dict] = {}
    for page, _, _ in rows:
        token = page.get("page_token")
        if token in by_token:
            raise ValueError("Duplicate crypto-quote page token")
        by_token[token] = page
    if None not in by_token:
        raise ValueError("Crypto-quote pagination has no first page")
    ordered = []
    seen = set()
    token = None
    while True:
        if token in seen:
            raise ValueError("Crypto-quote pagination cycle")
        page = by_token.get(token)
        if page is None:
            raise ValueError("Crypto-quote pagination is truncated")
        seen.add(token)
        ordered.append(page)
        token = page.get("next_page_token")
        if token is None:
            break
    if len(seen) != len(by_token):
        raise ValueError("Crypto-quote pagination has orphan pages")

    normalized = []
    quote_keys = set()
    coverage = {symbol: 0 for symbol in requested_symbols}
    for page in ordered:
        for quote in page["quotes"]:
            if not isinstance(quote, dict) or quote.get("symbol") not in coverage:
                raise ValueError("Malformed or unrequested crypto quote")
            stamp = _observed_time(quote.get("time"), "crypto-quote time")
            if not requested_start <= stamp <= requested_end or stamp > newest:
                raise ValueError("Crypto quote outside captured interval")
            bid = _trade_decimal(quote.get("bid_price"), "crypto-quote bid")
            ask = _trade_decimal(quote.get("ask_price"), "crypto-quote ask")
            bid_size = _trade_decimal(quote.get("bid_size"),
                                      "crypto-quote bid size")
            ask_size = _trade_decimal(quote.get("ask_size"),
                                      "crypto-quote ask size")
            if Decimal(ask) < Decimal(bid):
                raise ValueError("Crossed crypto quote")
            key = (quote["symbol"], stamp.isoformat())
            if key in quote_keys:
                raise ValueError("Duplicate crypto quote")
            quote_keys.add(key)
            coverage[quote["symbol"]] += 1
            normalized.append({
                "symbol": quote["symbol"],
                "time_utc": stamp.isoformat(),
                "bid_price": bid,
                "bid_size": bid_size,
                "ask_price": ask,
                "ask_size": ask_size,
            })
    missing = sorted(symbol for symbol, count in coverage.items() if not count)
    if missing:
        raise ValueError("Crypto-quote snapshot missing requested symbols")
    normalized.sort(key=lambda item: (item["time_utc"], item["symbol"]))
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return {
        "mode": "OFFLINE_POINT_IN_TIME_CRYPTO_QUOTE_REPLAY",
        "snapshot_id": snapshot_id,
        "as_of_utc": cutoff.isoformat(),
        "observed_at_utc": newest.isoformat(),
        "source": "ALPACA_CRYPTO_QUOTES",
        "location": location,
        "entitlement": rows[0][2],
        "symbols": list(requested_symbols),
        "start_utc": requested_start.isoformat(),
        "end_utc": requested_end.isoformat(),
        "pages_exhausted": len(ordered),
        "quotes": len(normalized),
        "quotes_by_symbol": coverage,
        "first_quote_utc": normalized[0]["time_utc"],
        "last_quote_utc": normalized[-1]["time_utc"],
        "content_sha256": sha256(payload.encode("utf-8")).hexdigest(),
        "execution_evidence": False,
        "fill_inference_allowed": False,
        "warning": "Offline quote audit only; not fill, order, or alpha evidence.",
    }


def replay_stock_trades_as_of(events: list[dict], *, as_of: datetime,
                              symbol: str) -> dict:
    """Replay locally captured stock trades/corrections at one cutoff.

    ``arrived_at`` and ``capture_sequence`` are local capture provenance, not
    exchange event time.  Corrections replace the referenced trade ID and
    cancel/error events remove it.  The result is audit data only: it is not a
    quote, bar, signal or executable fill source.
    """
    cutoff = _observed_time(as_of, "stock-trade cutoff")
    if not isinstance(events, list) or not events:
        raise ValueError("Stock-trade capture events required")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Stock-trade symbol required")
    requested_symbol = symbol.strip().upper()

    unique: dict[str, dict] = {}
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Malformed stock-trade capture event")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("Missing stock-trade event provenance")
        prior = unique.get(event_id)
        if prior is not None:
            if prior != event:
                raise ValueError("Conflicting duplicate stock-trade event")
            continue
        unique[event_id] = event

    normalized = []
    sequences = set()
    for event in unique.values():
        arrived = _observed_time(event.get("arrived_at"),
                                 "stock-trade arrived_at")
        sequence = event.get("capture_sequence")
        if type(sequence) is not int or sequence < 1 or sequence in sequences:
            raise ValueError("Invalid or duplicate stock-trade capture sequence")
        sequences.add(sequence)
        event_symbol = event.get("symbol")
        if (not isinstance(event_symbol, str)
                or event_symbol.upper() != requested_symbol):
            raise ValueError("Cross-symbol stock-trade capture")
        kind = event.get("event_type")
        if kind not in {"trade", "correction", "cancel_error"}:
            raise ValueError("Unsupported stock-trade event type")
        normalized.append((arrived, sequence, event))

    eligible = [row for row in normalized if row[0] <= cutoff]
    if not eligible:
        raise ValueError("No stock-trade event existed by cutoff")
    eligible.sort(key=lambda row: (row[0], row[1]))

    active: dict[str, dict] = {}
    superseded = []
    cancelled = []
    for arrived, _, event in eligible:
        kind = event["event_type"]
        if kind == "trade":
            trade_id = event.get("trade_id")
            if not isinstance(trade_id, str) or not trade_id or trade_id in active:
                raise ValueError("Missing or duplicate original stock-trade ID")
            conditions = event.get("conditions")
            if (not isinstance(conditions, list)
                    or not all(isinstance(item, str) and item for item in conditions)):
                raise ValueError("Invalid stock-trade conditions")
            exchange_time = _observed_time(event.get("exchange_time"),
                                           "stock-trade exchange_time")
            if exchange_time > arrived:
                raise ValueError("Stock trade arrived before exchange time")
            active[trade_id] = {
                "trade_id": trade_id,
                "symbol": requested_symbol,
                "price": _trade_decimal(event.get("price"), "stock-trade price"),
                "size": _trade_decimal(event.get("size"), "stock-trade size"),
                "conditions": list(conditions),
                "exchange_time_utc": exchange_time.isoformat(),
                "known_at_utc": arrived.isoformat(),
            }
            continue

        original_id = event.get("original_id")
        if not isinstance(original_id, str) or original_id not in active:
            raise ValueError("Unknown stock-trade correction/cancel ID")
        original = active.pop(original_id)
        if kind == "cancel_error":
            cancelled.append(original_id)
            continue

        corrected_id = event.get("corrected_id")
        if (not isinstance(corrected_id, str) or not corrected_id
                or corrected_id == original_id or corrected_id in active):
            raise ValueError("Invalid corrected stock-trade ID")
        conditions = event.get("corrected_conditions")
        if (not isinstance(conditions, list)
                or not all(isinstance(item, str) and item for item in conditions)):
            raise ValueError("Invalid corrected stock-trade conditions")
        active[corrected_id] = {
            "trade_id": corrected_id,
            "symbol": requested_symbol,
            "price": _trade_decimal(event.get("corrected_price"),
                                    "corrected stock-trade price"),
            "size": _trade_decimal(event.get("corrected_size"),
                                   "corrected stock-trade size"),
            "conditions": list(conditions),
            "exchange_time_utc": original["exchange_time_utc"],
            "known_at_utc": arrived.isoformat(),
            "corrects_trade_id": original_id,
        }
        superseded.append(original_id)

    return {
        "mode": "OFFLINE_POINT_IN_TIME_STOCK_TRADE_REPLAY",
        "symbol": requested_symbol,
        "as_of_utc": cutoff.isoformat(),
        "events_applied": len(eligible),
        "trades": sorted(active.values(), key=lambda row: row["trade_id"]),
        "superseded_trade_ids": sorted(superseded),
        "cancelled_trade_ids": sorted(cancelled),
        "warning": "Audit only; not bar, signal, quote, fill, or order evidence.",
    }


def replay_corporate_actions_as_of(pages: list[dict], *, as_of: datetime) -> dict:
    """Rebuild one fully captured corporate-action snapshot as it was known.

    Each page is an offline capture with local ``snapshot_id``, ``observed_at``,
    ``page_token`` and ``next_page_token`` provenance plus normalized ``actions``.
    ``observed_at`` is deliberately required because Alpaca does not guarantee
    when a corporate action becomes available.  This function performs no HTTP
    request and never substitutes today's complete dataset for historical state.
    """
    cutoff = _observed_time(as_of, "corporate-action cutoff")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Corporate-action capture pages required")
    snapshots: dict[str, list[tuple[dict, datetime]]] = {}
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Malformed corporate-action capture page")
        snapshot_id = page.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("Missing corporate-action snapshot provenance")
        observed = _observed_time(page.get("observed_at"), "snapshot observed_at")
        quality = page.get("data_quality")
        if quality not in ("all", "complete"):
            raise ValueError("Unsupported corporate-action data quality")
        token = page.get("page_token")
        next_token = page.get("next_page_token")
        for value in (token, next_token):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError("Invalid corporate-action page token")
        if not isinstance(page.get("actions"), list):
            raise ValueError("Corporate-action page records missing")
        snapshots.setdefault(snapshot_id, []).append((page, observed))

    eligible: list[tuple[datetime, str]] = []
    for snapshot_id, rows in snapshots.items():
        observed = {stamp for _, stamp in rows}
        quality = {page["data_quality"] for page, _ in rows}
        if len(observed) != 1 or len(quality) != 1:
            raise ValueError("Corporate-action snapshot metadata conflict")
        stamp = next(iter(observed))
        if stamp <= cutoff:
            eligible.append((stamp, snapshot_id))
    if not eligible:
        raise ValueError("No corporate-action snapshot existed by cutoff")
    newest = max(stamp for stamp, _ in eligible)
    candidate_ids = [snapshot_id for stamp, snapshot_id in eligible if stamp == newest]
    if len(candidate_ids) != 1:
        raise ValueError("Ambiguous corporate-action snapshot at cutoff")

    snapshot_id = candidate_ids[0]
    rows = snapshots[snapshot_id]
    by_token: dict[str | None, dict] = {}
    for page, _ in rows:
        token = page.get("page_token")
        if token in by_token:
            raise ValueError("Duplicate corporate-action page token")
        by_token[token] = page
    if None not in by_token:
        raise ValueError("Corporate-action pagination has no first page")
    ordered = []
    seen = set()
    token = None
    while True:
        if token in seen:
            raise ValueError("Corporate-action pagination cycle")
        page = by_token.get(token)
        if page is None:
            raise ValueError("Corporate-action pagination is truncated")
        seen.add(token)
        ordered.append(page)
        token = page.get("next_page_token")
        if token is None:
            break
    if len(seen) != len(by_token):
        raise ValueError("Corporate-action pagination has orphan pages")

    actions = []
    excluded = []
    action_ids = set()
    requested_quality = ordered[0]["data_quality"]
    for page in ordered:
        for action in page["actions"]:
            if not isinstance(action, dict):
                raise ValueError("Malformed corporate-action record")
            action_id = action.get("id")
            kind = action.get("type")
            symbol = action.get("symbol")
            quality = action.get("record_quality")
            revision = action.get("revision")
            if (not isinstance(action_id, str) or not action_id
                    or not isinstance(kind, str) or not kind
                    or not isinstance(symbol, str) or not symbol
                    or quality not in ("complete", "incomplete")
                    or type(revision) is not int or revision < 1):
                raise ValueError("Corporate-action record provenance incomplete")
            try:
                date.fromisoformat(action.get("process_date"))
            except (TypeError, ValueError):
                raise ValueError("Invalid corporate-action process date") from None
            if action_id in action_ids:
                raise ValueError("Duplicate corporate-action record")
            action_ids.add(action_id)
            if quality == "incomplete":
                if requested_quality == "complete":
                    raise ValueError("Complete snapshot contains incomplete action")
                excluded.append(action_id)
                continue
            normalized = dict(action)
            normalized["known_at_utc"] = newest.isoformat()
            actions.append(normalized)
    actions.sort(key=lambda item: (item["process_date"], item["id"]))
    return {
        "mode": "OFFLINE_POINT_IN_TIME_CORPORATE_ACTION_REPLAY",
        "snapshot_id": snapshot_id,
        "as_of_utc": cutoff.isoformat(),
        "observed_at_utc": newest.isoformat(),
        "data_quality": requested_quality,
        "pages_exhausted": len(ordered),
        "actions": actions,
        "excluded_incomplete_ids": sorted(excluded),
        "warning": "Audit metadata only; does not adjust bars or authorize trading.",
    }


def _bar_decimal(value, label: str, *, allow_zero: bool = False) -> str:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid {label}") from None
    if (not parsed.is_finite() or parsed < 0
            or (not allow_zero and parsed == 0)):
        raise ValueError(f"Invalid {label}")
    return format(parsed, "f")


def _stock_bar_snapshot(pages: list[dict], *, as_of: datetime, symbol: str,
                        adjustment: str, symbol_asof: str) -> tuple[dict, list[dict]]:
    """Select and normalize one complete locally observed stock-bar snapshot."""
    cutoff = _observed_time(as_of, "stock-bar cutoff")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Stock-bar capture pages required")
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Stock-bar symbol required")
    requested_symbol = symbol.strip().upper()
    if adjustment not in {"raw", "split", "dividend", "spin-off", "all"}:
        raise ValueError("Explicit supported stock-bar adjustment required")
    try:
        date.fromisoformat(symbol_asof)
    except (TypeError, ValueError):
        raise ValueError("Explicit stock-bar symbol as-of date required") from None

    snapshots: dict[str, list[tuple[dict, datetime]]] = {}
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Malformed stock-bar capture page")
        snapshot_id = page.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("Missing stock-bar snapshot provenance")
        observed = _observed_time(page.get("observed_at"),
                                  "stock-bar snapshot observed_at")
        if (page.get("source") != "ALPACA_STOCK_BARS"
                or page.get("feed") != "iex"
                or page.get("symbol") != requested_symbol
                or page.get("adjustment") != adjustment
                or page.get("symbol_asof") != symbol_asof
                or not isinstance(page.get("timeframe"), str)
                or not page["timeframe"]):
            raise ValueError("Stock-bar query provenance mismatch")
        token = page.get("page_token")
        next_token = page.get("next_page_token")
        for value in (token, next_token):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError("Invalid stock-bar page token")
        if not isinstance(page.get("bars"), list):
            raise ValueError("Stock-bar page records missing")
        snapshots.setdefault(snapshot_id, []).append((page, observed))

    eligible: list[tuple[datetime, str]] = []
    for snapshot_id, rows in snapshots.items():
        observed = {stamp for _, stamp in rows}
        metadata = {(page["source"], page["feed"], page["symbol"],
                     page["adjustment"], page["symbol_asof"], page["timeframe"])
                    for page, _ in rows}
        if len(observed) != 1 or len(metadata) != 1:
            raise ValueError("Stock-bar snapshot metadata conflict")
        stamp = next(iter(observed))
        if stamp <= cutoff:
            eligible.append((stamp, snapshot_id))
    if not eligible:
        raise ValueError("No stock-bar snapshot existed by cutoff")
    newest = max(stamp for stamp, _ in eligible)
    candidate_ids = [item for stamp, item in eligible if stamp == newest]
    if len(candidate_ids) != 1:
        raise ValueError("Ambiguous stock-bar snapshot at cutoff")

    snapshot_id = candidate_ids[0]
    rows = snapshots[snapshot_id]
    by_token: dict[str | None, dict] = {}
    for page, _ in rows:
        token = page.get("page_token")
        if token in by_token:
            raise ValueError("Duplicate stock-bar page token")
        by_token[token] = page
    if None not in by_token:
        raise ValueError("Stock-bar pagination has no first page")
    ordered = []
    seen = set()
    token = None
    while True:
        if token in seen:
            raise ValueError("Stock-bar pagination cycle")
        page = by_token.get(token)
        if page is None:
            raise ValueError("Stock-bar pagination is truncated")
        seen.add(token)
        ordered.append(page)
        token = page.get("next_page_token")
        if token is None:
            break
    if len(seen) != len(by_token):
        raise ValueError("Stock-bar pagination has orphan pages")

    normalized = []
    bar_keys = set()
    for page in ordered:
        for bar in page["bars"]:
            if not isinstance(bar, dict) or bar.get("symbol") != requested_symbol:
                raise ValueError("Malformed or cross-symbol stock bar")
            stamp = _observed_time(bar.get("time"), "stock-bar time")
            if stamp > newest:
                raise ValueError("Stock bar occurs after snapshot observation")
            row = {
                "symbol": requested_symbol,
                "time_utc": stamp.isoformat(),
                "open": _bar_decimal(bar.get("open"), "stock-bar open"),
                "high": _bar_decimal(bar.get("high"), "stock-bar high"),
                "low": _bar_decimal(bar.get("low"), "stock-bar low"),
                "close": _bar_decimal(bar.get("close"), "stock-bar close"),
                "volume": _bar_decimal(bar.get("volume"), "stock-bar volume",
                                        allow_zero=True),
            }
            if (Decimal(row["low"]) > min(Decimal(row["open"]),
                                           Decimal(row["close"]))
                    or Decimal(row["high"]) < max(Decimal(row["open"]),
                                                  Decimal(row["close"]))
                    or Decimal(row["low"]) > Decimal(row["high"])):
                raise ValueError("Inconsistent stock-bar OHLC")
            key = (requested_symbol, row["time_utc"])
            if key in bar_keys:
                raise ValueError("Duplicate stock bar")
            bar_keys.add(key)
            normalized.append(row)
    if not normalized:
        raise ValueError("Stock-bar snapshot is empty")
    normalized.sort(key=lambda row: row["time_utc"])
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    audit = {
        "mode": "OFFLINE_POINT_IN_TIME_STOCK_BAR_REPLAY",
        "snapshot_id": snapshot_id,
        "as_of_utc": cutoff.isoformat(),
        "observed_at_utc": newest.isoformat(),
        "source": "ALPACA_STOCK_BARS",
        "feed": "iex",
        "symbol": requested_symbol,
        "adjustment": adjustment,
        "symbol_asof": symbol_asof,
        "timeframe": ordered[0]["timeframe"],
        "pages_exhausted": len(ordered),
        "bars": len(normalized),
        "first_bar_utc": normalized[0]["time_utc"],
        "last_bar_utc": normalized[-1]["time_utc"],
        "content_sha256": sha256(payload.encode("utf-8")).hexdigest(),
        "warning": "Offline audit only; not quote, fill, order, or alpha evidence.",
    }
    return audit, normalized


def replay_stock_bars_as_of(pages: list[dict], *, as_of: datetime, symbol: str,
                            adjustment: str, symbol_asof: str) -> dict:
    """Audit one complete stock-bar snapshot without making a provider request."""
    audit, _ = _stock_bar_snapshot(
        pages, as_of=as_of, symbol=symbol, adjustment=adjustment,
        symbol_asof=symbol_asof)
    return audit


def _engine_bar_rows(bars: list[Bar]) -> list[dict]:
    return [{
        "symbol": bar.symbol.upper(),
        "time_utc": bar.time.astimezone(timezone.utc).isoformat(),
        "open": _bar_decimal(bar.open, "evaluation bar open"),
        "high": _bar_decimal(bar.high, "evaluation bar high"),
        "low": _bar_decimal(bar.low, "evaluation bar low"),
        "close": _bar_decimal(bar.close, "evaluation bar close"),
        "volume": _bar_decimal(bar.volume, "evaluation bar volume",
                               allow_zero=True),
    } for bar in bars]


def _check_data(bars: list[Bar]) -> None:
    if not bars:
        raise ValueError("Historical bars required")
    symbol = bars[0].symbol.upper()
    last = None
    for bar in bars:
        bar.validate()
        if not all(isfinite(v) for v in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError("Non-finite historical price")
        if bar.symbol.upper() != symbol:
            raise ValueError("Use a single instrument per evaluation")
        utc_time = bar.time.astimezone(timezone.utc)
        if last is not None and utc_time <= last:
            raise ValueError("Bars must be chronological and nonduplicated")
        last = utc_time


def _window_report(rows: list[Bar], settings: Settings) -> dict:
    engine = PaperEngine(settings)
    peak = settings.start_cash
    worst_drawdown = 0.0
    for bar in rows:
        engine.on_bar(bar)
        mark = engine.equity
        peak = max(peak, mark)
        worst_drawdown = max(worst_drawdown, (peak - mark) / peak if peak else 0.0)
    engine.finalize()  # Forced exit for a fair window-end comparison
    summary = engine.summary()
    return {
        "start_utc": rows[0].time.astimezone(timezone.utc).isoformat(),
        "end_utc": rows[-1].time.astimezone(timezone.utc).isoformat(),
        "bars": len(rows),
        "strategy": summary,
        "max_mark_to_market_drawdown_pct": round(100 * worst_drawdown, 2),
        "buy_hold_price_change_pct": round(100 * (rows[-1].close / rows[0].open - 1), 2),
        "warning": "Buy-and-hold benchmark is price-only; it excludes spreads and commissions",
    }


def evaluate_holdout(bars: list[Bar], settings: Settings | None = None,
                     *, train_fraction: float = 0.70,
                     corporate_action_pages: list[dict] | None = None,
                     corporate_action_as_of: datetime | None = None,
                     stock_bar_pages: list[dict] | None = None,
                     stock_bar_as_of: datetime | None = None,
                     stock_bar_adjustment: str | None = None,
                     stock_bar_symbol_asof: str | None = None) -> dict:
    """Chronological split, fresh account per window, no parameter search.

    Minimum usable history is required *within each window*.  This avoids
    feeding future or training-period positions into the holdout portfolio.
    """
    settings = settings or Settings()
    settings.validate()
    if not isfinite(train_fraction) or not 0.3 <= train_fraction <= 0.85:
        raise ValueError("train_fraction must be between 0.30 and 0.85")
    _check_data(bars)
    split = int(len(bars) * train_fraction)
    minimum = settings.min_history_bars + 3
    if split < minimum or len(bars) - split < minimum:
        raise ValueError(f"Need at least {minimum} bars in each split")
    action_audit = {
        "status": "NOT_PROVIDED",
        "warning": "No point-in-time corporate-action capture was supplied.",
    }
    if corporate_action_pages is not None or corporate_action_as_of is not None:
        if corporate_action_pages is None or corporate_action_as_of is None:
            raise ValueError("Corporate-action pages and cutoff must be supplied together")
        cutoff = _observed_time(corporate_action_as_of,
                                "corporate-action cutoff")
        first_bar = bars[0].time.astimezone(timezone.utc)
        if cutoff > first_bar:
            raise ValueError("Corporate-action cutoff must not follow evaluation start")
        action_audit = replay_corporate_actions_as_of(
            corporate_action_pages, as_of=cutoff)
    bar_audit = {
        "status": "NOT_PROVIDED",
        "warning": "No point-in-time stock-bar capture was supplied.",
    }
    bar_inputs = (stock_bar_pages, stock_bar_as_of, stock_bar_adjustment,
                  stock_bar_symbol_asof)
    if any(value is not None for value in bar_inputs):
        if any(value is None for value in bar_inputs):
            raise ValueError("Stock-bar pages, cutoff, adjustment and symbol as-of "
                             "must be supplied together")
        cutoff = _observed_time(stock_bar_as_of, "stock-bar cutoff")
        last_bar = bars[-1].time.astimezone(timezone.utc)
        if cutoff < last_bar:
            raise ValueError("Stock-bar cutoff must not precede evaluation end")
        bar_audit, captured = _stock_bar_snapshot(
            stock_bar_pages, as_of=cutoff, symbol=bars[0].symbol,
            adjustment=stock_bar_adjustment,
            symbol_asof=stock_bar_symbol_asof)
        if captured != _engine_bar_rows(bars):
            raise ValueError("Evaluation bars do not match audited stock-bar snapshot")
    return {
        "mode": "OFFLINE_HISTORICAL_HOLDOUT",
        "paper_only": True,
        "strategy_settings_fixed": asdict(settings),
        "corporate_action_audit": action_audit,
        "stock_bar_audit": bar_audit,
        "train": _window_report(bars[:split], settings),
        "holdout": _window_report(bars[split:], settings),
        "limitations": [
            "No optimization, guaranteed edge, or future prediction",
            "Price-only buy-and-hold comparator and bar-level simulated fills",
            "Real execution, spreads, market impact and option/crypto behavior are not validated",
            "Synthetic data and a single holdout cannot demonstrate statistical significance",
            "Corporate-action audit metadata does not retrospectively adjust price bars",
            "Stock-bar provenance is optional; when supplied, exact content must match",
        ],
    }
