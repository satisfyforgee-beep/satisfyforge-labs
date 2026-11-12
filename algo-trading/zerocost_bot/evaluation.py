"""Out-of-sample *historical simulation*, without training or broker calls.

The fixed strategy is replayed independently on chronological train and test
windows.  No settings are tuned on either set.  Results are diagnostic, not a
forecast; data quality, fees and market coverage still matter greatly.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite

from .engine import Bar, PaperEngine, Settings


_ALPACA_OPTION_HISTORY_START = datetime(2024, 2, 1, tzinfo=timezone.utc)


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


def validate_historical_option_provenance(metadata: dict) -> dict:
    """Fail closed on ambiguous Alpaca historical-option feed provenance.

    This offline preflight validates capture metadata only.  Alpaca documents
    option history as beginning in February 2024; its free indicative feed is
    derived rather than OPRA, and indicative trades are delayed 15 minutes.
    No accepted dataset is promoted to executable quote, fill, or order proof.
    """
    if not isinstance(metadata, dict):
        raise ValueError("Historical-option provenance metadata required")
    if metadata.get("provider") != "alpaca":
        raise ValueError("Unsupported historical-option provider")
    if metadata.get("asset_class") != "option":
        raise ValueError("Historical-option asset class required")

    data_type = metadata.get("data_type")
    if data_type not in {"quotes", "trades"}:
        raise ValueError("Unsupported historical-option data type")
    feed = metadata.get("feed")
    if feed not in {"indicative", "opra"}:
        raise ValueError("Unknown historical-option feed")
    expected_provenance = {
        "indicative": "derived_indicative",
        "opra": "opra",
    }[feed]
    if metadata.get("source_provenance") != expected_provenance:
        raise ValueError("Historical-option feed provenance conflict")

    start = _observed_time(metadata.get("window_start"),
                           "historical-option window_start")
    end = _observed_time(metadata.get("window_end"),
                         "historical-option window_end")
    captured = _observed_time(metadata.get("captured_at"),
                              "historical-option captured_at")
    if start < _ALPACA_OPTION_HISTORY_START:
        raise ValueError("Historical-option window predates provider coverage")
    if end <= start:
        raise ValueError("Historical-option window must have positive duration")
    if end > captured:
        raise ValueError("Historical-option window extends beyond capture time")

    delay = metadata.get("delay_minutes")
    if type(delay) is not int or delay < 0:
        raise ValueError("Known historical-option feed delay required")
    entitlement = metadata.get("opra_entitlement_verified")
    if type(entitlement) is not bool:
        raise ValueError("Explicit OPRA entitlement status required")
    if metadata.get("execution_evidence") is not False:
        raise ValueError("Historical-option data is not execution evidence")

    if feed == "opra":
        if not entitlement:
            raise ValueError("Verified OPRA entitlement required")
        if delay != 0:
            raise ValueError("OPRA capture cannot claim delayed provenance")
    else:
        if entitlement:
            raise ValueError("Indicative feed cannot claim OPRA entitlement")
        if data_type == "trades" and delay < 15:
            raise ValueError("Indicative option trades must preserve delay")

    return {
        "mode": "OFFLINE_HISTORICAL_OPTION_PROVENANCE_PREFLIGHT",
        "provider": "alpaca",
        "asset_class": "option",
        "data_type": data_type,
        "feed": feed,
        "source_provenance": expected_provenance,
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "captured_at_utc": captured.isoformat(),
        "delay_minutes": delay,
        "opra_entitlement_verified": entitlement,
        "research_only": True,
        "execution_evidence": False,
        "warning": "Research metadata only; not quote, fill, or order evidence.",
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
                     corporate_action_as_of: datetime | None = None) -> dict:
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
    return {
        "mode": "OFFLINE_HISTORICAL_HOLDOUT",
        "paper_only": True,
        "strategy_settings_fixed": asdict(settings),
        "corporate_action_audit": action_audit,
        "train": _window_report(bars[:split], settings),
        "holdout": _window_report(bars[split:], settings),
        "limitations": [
            "No optimization, guaranteed edge, or future prediction",
            "Price-only buy-and-hold comparator and bar-level simulated fills",
            "Real execution, spreads, market impact and option/crypto behavior are not validated",
            "Synthetic data and a single holdout cannot demonstrate statistical significance",
            "Corporate-action audit metadata does not retrospectively adjust price bars",
        ],
    }
