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


def _positive_decimal(value, label: str) -> Decimal:
    """Parse exact provider metadata without accepting floats or non-finite values."""
    if isinstance(value, float):
        raise ValueError(f"Invalid {label}")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid {label}") from None
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"Invalid {label}")
    return parsed


def replay_option_contracts_as_of(pages: list[dict], *, as_of: datetime) -> dict:
    """Rebuild one complete option-contract capture as it was observed.

    The caller supplies offline pages captured from an explicitly bounded
    contract query.  This function performs no provider request and produces
    audit metadata only; it never values a contract or authorizes an order.
    """
    cutoff = _observed_time(as_of, "option-contract cutoff")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Option-contract capture pages required")

    snapshots: dict[str, list[tuple[dict, datetime, dict]]] = {}
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Malformed option-contract capture page")
        snapshot_id = page.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("Missing option-contract snapshot provenance")
        observed = _observed_time(page.get("observed_at"),
                                  "option-contract observed_at")
        filters = page.get("request_filters")
        if not isinstance(filters, dict):
            raise ValueError("Explicit option-contract request filters required")
        symbols = filters.get("underlying_symbols")
        if (not isinstance(symbols, list) or not symbols
                or any(not isinstance(symbol, str) or not symbol
                       or symbol != symbol.upper() for symbol in symbols)
                or len(set(symbols)) != len(symbols)):
            raise ValueError("Explicit underlying_symbols filter required")
        try:
            expiration_start = date.fromisoformat(filters["expiration_date_gte"])
            expiration_end = date.fromisoformat(filters["expiration_date_lte"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Explicit option expiration bounds required") from None
        if expiration_start > expiration_end:
            raise ValueError("Invalid option expiration bounds")
        if filters.get("show_deliverables") is not True:
            raise ValueError("Option deliverables must be explicitly requested")
        status = filters.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("Explicit option status filter required")
        token = page.get("page_token")
        next_token = page.get("next_page_token")
        for value in (token, next_token):
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError("Invalid option-contract page token")
        if not isinstance(page.get("contracts"), list):
            raise ValueError("Option-contract page records missing")
        snapshots.setdefault(snapshot_id, []).append((page, observed, filters))

    eligible: list[tuple[datetime, str]] = []
    for snapshot_id, rows in snapshots.items():
        observed = {stamp for _, stamp, _ in rows}
        filters = [query for _, _, query in rows]
        if len(observed) != 1 or any(query != filters[0] for query in filters[1:]):
            raise ValueError("Option-contract snapshot metadata conflict")
        stamp = next(iter(observed))
        if stamp <= cutoff:
            eligible.append((stamp, snapshot_id))
    if not eligible:
        raise ValueError("No option-contract snapshot existed by cutoff")
    newest = max(stamp for stamp, _ in eligible)
    candidate_ids = [snapshot_id for stamp, snapshot_id in eligible
                     if stamp == newest]
    if len(candidate_ids) != 1:
        raise ValueError("Ambiguous option-contract snapshot at cutoff")

    snapshot_id = candidate_ids[0]
    rows = snapshots[snapshot_id]
    query = rows[0][2]
    by_token: dict[str | None, dict] = {}
    for page, _, _ in rows:
        token = page.get("page_token")
        if token in by_token:
            raise ValueError("Duplicate option-contract page token")
        by_token[token] = page
    if None not in by_token:
        raise ValueError("Option-contract pagination has no first page")
    ordered = []
    seen = set()
    token = None
    while True:
        if token in seen:
            raise ValueError("Option-contract pagination cycle")
        page = by_token.get(token)
        if page is None:
            raise ValueError("Option-contract pagination is truncated")
        seen.add(token)
        ordered.append(page)
        token = page.get("next_page_token")
        if token is None:
            break
    if len(seen) != len(by_token):
        raise ValueError("Option-contract pagination has orphan pages")

    start = date.fromisoformat(query["expiration_date_gte"])
    end = date.fromisoformat(query["expiration_date_lte"])
    requested_underlyings = set(query["underlying_symbols"])
    contracts = []
    identities = set()
    for page in ordered:
        for contract in page["contracts"]:
            if not isinstance(contract, dict):
                raise ValueError("Malformed option-contract record")
            symbol = contract.get("symbol")
            underlying = contract.get("underlying_symbol")
            contract_type = contract.get("type")
            status = contract.get("status")
            if (not isinstance(symbol, str) or not symbol
                    or not isinstance(underlying, str)
                    or underlying not in requested_underlyings
                    or contract_type not in ("call", "put")
                    or status != query["status"]):
                raise ValueError("Option-contract identity conflicts with request")
            if symbol in identities:
                raise ValueError("Duplicate option-contract identity")
            identities.add(symbol)
            try:
                expiration = date.fromisoformat(contract["expiration_date"])
            except (KeyError, TypeError, ValueError):
                raise ValueError("Invalid option-contract expiration") from None
            if not start <= expiration <= end:
                raise ValueError("Option contract outside requested expiration bounds")
            strike = _positive_decimal(contract.get("strike_price"),
                                       "option strike")
            size = _positive_decimal(contract.get("size"), "option size")
            multiplier = _positive_decimal(contract.get("multiplier"),
                                            "option multiplier")
            deliverables = contract.get("deliverables")
            if not isinstance(deliverables, list) or not deliverables:
                raise ValueError("Option contract deliverables missing")
            normalized_deliverables = []
            for deliverable in deliverables:
                if not isinstance(deliverable, dict):
                    raise ValueError("Malformed option deliverable")
                kind = deliverable.get("type")
                asset = deliverable.get("symbol")
                if (not isinstance(kind, str) or not kind
                        or asset is not None
                        and (not isinstance(asset, str) or not asset)):
                    raise ValueError("Option deliverable identity missing")
                amount = _positive_decimal(deliverable.get("amount"),
                                           "option deliverable amount")
                normalized_deliverables.append({
                    "type": kind,
                    "symbol": asset,
                    "amount": str(amount),
                })
            normalized = dict(contract)
            normalized.update({
                "strike_price": str(strike),
                "size": str(size),
                "multiplier": str(multiplier),
                "deliverables": normalized_deliverables,
                "known_at_utc": newest.isoformat(),
            })
            contracts.append(normalized)
    if not contracts:
        raise ValueError("Option-contract snapshot contains no contracts")
    contracts.sort(key=lambda item: item["symbol"])
    return {
        "mode": "OFFLINE_POINT_IN_TIME_OPTION_CONTRACT_REPLAY",
        "snapshot_id": snapshot_id,
        "as_of_utc": cutoff.isoformat(),
        "observed_at_utc": newest.isoformat(),
        "request_filters": dict(query),
        "pages_exhausted": len(ordered),
        "contracts": contracts,
        "warning": "Audit metadata only; does not value options or authorize trading.",
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
