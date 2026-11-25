"""Offline, deterministic, cash-only paper execution for SatisfyForge.

No network access, broker keys, market-data downloads, or live-order paths exist
in this module. Quotes must be supplied by an explicitly identified data source.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterator


def amount(value: str | int | Decimal) -> Decimal:
    """Reject floats, negative, zero, and non-finite financial inputs."""
    if isinstance(value, float):
        raise ValueError("Floating-point money is not supported; use decimal strings")
    try:
        result = Decimal(value)
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise ValueError("Expected a decimal number") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError("Value must be finite and greater than zero")
    return result


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset: str  # equity, option, crypto
    multiplier: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if self.asset not in {"equity", "option", "crypto"}:
            raise ValueError("Unsupported asset class")
        if not self.symbol or len(self.symbol) > 64 or any(c.isspace() for c in self.symbol):
            raise ValueError("Instrument requires a nonempty, whitespace-free symbol")
        multiplier = amount(self.multiplier)
        object.__setattr__(self, "multiplier", multiplier)
        if self.asset != "option" and multiplier != 1:
            raise ValueError("Equity and crypto must use a multiplier of 1")
        if self.asset == "option" and multiplier != 100:
            raise ValueError("Only explicitly confirmed standard 100-share options supported")


@dataclass(frozen=True)
class Quote:
    instrument: Instrument
    bid: Decimal
    ask: Decimal
    asof: datetime
    source: str
    delayed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "bid", amount(self.bid))
        object.__setattr__(self, "ask", amount(self.ask))
        _utc(self.asof)
        if not self.source.strip():
            raise ValueError("Quote source must be identified")
        if self.ask < self.bid:
            raise ValueError("Crossed quote: ask below bid")


@dataclass(frozen=True)
class PaperOrder:
    client_id: str
    instrument: Instrument
    side: str  # buy or sell, no shorting
    quantity: Decimal
    limit_price: Decimal
    signal_id: str = ""  # stable strategy decision identifier; optional for manual demos

    def __post_init__(self) -> None:
        if not self.client_id or len(self.client_id) > 128 or self.client_id.isspace():
            raise ValueError("A stable client_id is required for duplicate protection")
        if len(self.signal_id) > 128 or any(c.isspace() for c in self.signal_id):
            raise ValueError("Signal ID must be whitespace-free and at most 128 characters")
        if self.side not in {"buy", "sell"}:
            raise ValueError("Only buy and sell-to-close are supported")
        qty = amount(self.quantity)
        object.__setattr__(self, "quantity", qty)
        object.__setattr__(self, "limit_price", amount(self.limit_price))
        if self.instrument.asset != "crypto" and qty != qty.to_integral_value():
            raise ValueError("Stock and options quantities must be whole numbers")


@dataclass(frozen=True)
class CryptoOrderRules:
    """Explicit provider metadata required before shaping a crypto order.

    These values must come from a captured asset/fee snapshot.  Defaults are
    intentionally omitted so missing precision, minimum, or fee evidence fails
    closed instead of silently borrowing assumptions from another pair.
    """

    min_quantity: Decimal
    quantity_increment: Decimal
    min_notional: Decimal
    price_increment: Decimal
    taker_fee_fraction: Decimal

    def __post_init__(self) -> None:
        for name in ("min_quantity", "quantity_increment", "min_notional",
                     "price_increment", "taker_fee_fraction"):
            object.__setattr__(self, name, amount(getattr(self, name)))


def validate_crypto_buy_contract(payload: dict, *, rules: CryptoOrderRules,
                                 available_cash: Decimal,
                                 reference_price: Decimal) -> dict:
    """Validate one offline crypto buy request without submitting or filling it.

    Alpaca documents crypto ``market``, ``limit`` and ``stop_limit`` orders,
    ``gtc``/``ioc`` time in force, and fractional sizing by exactly one of
    ``qty`` or ``notional``.  This guard additionally requires captured
    pair-specific increments/minimums plus an explicit conservative fee and
    cash estimate.  It is a contract audit only, not a broker adapter.
    """
    if not isinstance(payload, dict):
        raise ValueError("Crypto order payload must be an object")
    forbidden = {"order_class", "take_profit", "stop_loss", "bracket", "oco", "oto"}
    if forbidden.intersection(payload):
        raise ValueError("Bracket/OCO/OTO fields are unsupported for crypto")
    allowed = {
        "symbol", "side", "type", "time_in_force", "qty", "notional",
        "limit_price", "stop_price", "client_order_id",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError("Unknown crypto order fields")

    symbol = payload.get("symbol")
    if (not isinstance(symbol, str) or "/" not in symbol
            or symbol != symbol.upper() or any(char.isspace() for char in symbol)):
        raise ValueError("Explicit uppercase crypto pair required")
    if payload.get("side") != "buy":
        raise ValueError("This contract guard supports buys only")
    order_type = payload.get("type")
    if order_type not in {"market", "limit", "stop_limit"}:
        raise ValueError("Unsupported crypto order type")
    time_in_force = payload.get("time_in_force")
    if time_in_force not in {"gtc", "ioc"}:
        raise ValueError("Unsupported crypto time in force")

    has_qty = "qty" in payload
    has_notional = "notional" in payload
    if has_qty == has_notional:
        raise ValueError("Provide exactly one of crypto qty or notional")
    sizing_name = "qty" if has_qty else "notional"
    sizing = amount(payload[sizing_name])
    cash = amount(available_cash)
    reference = amount(reference_price)

    limit_price = None
    stop_price = None
    if order_type == "market":
        if "limit_price" in payload or "stop_price" in payload:
            raise ValueError("Market crypto order cannot contain limit/stop prices")
    elif order_type == "limit":
        if "limit_price" not in payload or "stop_price" in payload:
            raise ValueError("Limit crypto order requires only limit_price")
        limit_price = amount(payload["limit_price"])
    else:
        if "limit_price" not in payload or "stop_price" not in payload:
            raise ValueError("Stop-limit crypto order requires limit_price and stop_price")
        limit_price = amount(payload["limit_price"])
        stop_price = amount(payload["stop_price"])

    for label, price in (("limit", limit_price), ("stop", stop_price)):
        if price is not None and price % rules.price_increment != 0:
            raise ValueError(f"Crypto {label} price violates asset increment")

    if has_qty:
        if sizing < rules.min_quantity:
            raise ValueError("Crypto quantity is below asset minimum")
        if sizing % rules.quantity_increment != 0:
            raise ValueError("Crypto quantity violates asset increment")
        gross = sizing * (limit_price if limit_price is not None else reference)
    else:
        if sizing < rules.min_notional:
            raise ValueError("Crypto notional is below asset minimum")
        gross = sizing

    fee = gross * rules.taker_fee_fraction
    total_debit = gross + fee
    if total_debit > cash:
        raise ValueError("Crypto order exceeds cash after conservative fee")

    canonical = {
        "symbol": symbol,
        "side": "buy",
        "type": order_type,
        "time_in_force": time_in_force,
        sizing_name: str(sizing),
        "estimated_gross": str(gross),
        "estimated_taker_fee": str(fee),
        "estimated_total_debit": str(total_debit),
        "available_cash": str(cash),
        "reference_price": str(reference),
        "execution_evidence": False,
        "broker_submit_allowed": False,
        "warning": "Offline contract validation only; not an order, fill, or profit claim.",
    }
    if limit_price is not None:
        canonical["limit_price"] = str(limit_price)
    if stop_price is not None:
        canonical["stop_price"] = str(stop_price)
    client_order_id = payload.get("client_order_id")
    if client_order_id is not None:
        if (not isinstance(client_order_id, str) or not client_order_id
                or len(client_order_id) > 128 or any(c.isspace() for c in client_order_id)):
            raise ValueError("Stable crypto client_order_id is invalid")
        canonical["client_order_id"] = client_order_id
    return canonical


@dataclass(frozen=True)
class AccountInventoryPolicy:
    """Account-wide caps for an offline, paper-only inventory preflight."""

    max_total_exposure: Decimal
    max_daily_loss: Decimal
    max_open_positions: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_total_exposure",
                           amount(self.max_total_exposure))
        object.__setattr__(self, "max_daily_loss", amount(self.max_daily_loss))
        if (not isinstance(self.max_open_positions, int)
                or isinstance(self.max_open_positions, bool)
                or self.max_open_positions < 1):
            raise ValueError("max_open_positions must be a positive integer")


def _snapshot_amount(value: object, label: str, *, allow_zero: bool = False) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{label} must use an exact decimal string")
    try:
        number = Decimal(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise ValueError(f"{label} must be a decimal") from exc
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        raise ValueError(f"{label} is invalid")
    return number


def _snapshot_time(value: object, label: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{label} must be an RFC3339 timestamp") from exc
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def normalize_alpaca_inventory_capture(capture: dict, *, observed_at: datetime,
                                       max_capture_span_seconds: int = 10,
                                       max_snapshot_age_seconds: int = 30) -> dict:
    """Normalize three read-only Alpaca paper GET responses for preflight.

    The caller must capture the account, complete positions list, and a single
    maximum-size ``status=open`` orders page from the documented paper host.
    This function performs no network request and never enables submission.
    A full 500-order page is rejected because completeness cannot be proved.
    """
    if (not isinstance(capture, dict) or set(capture) != {
            "provider", "base_url", "account", "positions", "open_orders"}):
        raise ValueError("Exact Alpaca capture fields are required")
    if capture["provider"] != "alpaca" \
            or capture["base_url"] != "https://paper-api.alpaca.markets":
        raise ValueError("Exact Alpaca paper provider and host are required")
    if (not isinstance(max_capture_span_seconds, int)
            or isinstance(max_capture_span_seconds, bool)
            or not isinstance(max_snapshot_age_seconds, int)
            or isinstance(max_snapshot_age_seconds, bool)
            or min(max_capture_span_seconds, max_snapshot_age_seconds) <= 0):
        raise ValueError("Snapshot timing limits must be positive integers")
    now = _snapshot_time(observed_at, "observed_at")

    specifications = {
        "account": ("/v2/account", {}, dict),
        "positions": ("/v2/positions", {}, list),
        "open_orders": (
            "/v2/orders",
            {"status": "open", "limit": 500, "nested": False,
             "direction": "asc"},
            list,
        ),
    }
    bodies: dict[str, object] = {}
    started: list[datetime] = []
    finished: list[datetime] = []
    envelope_fields = {
        "method", "path", "query", "status_code", "requested_at",
        "received_at", "body",
    }
    for name, (path, query, body_type) in specifications.items():
        envelope = capture[name]
        if not isinstance(envelope, dict) or set(envelope) != envelope_fields:
            raise ValueError(f"Exact {name} response envelope is required")
        if (envelope["method"] != "GET" or envelope["path"] != path
                or envelope["query"] != query or envelope["status_code"] != 200
                or not isinstance(envelope["body"], body_type)):
            raise ValueError(f"Unverified or malformed {name} response")
        requested = _snapshot_time(envelope["requested_at"],
                                   f"{name} requested_at")
        received = _snapshot_time(envelope["received_at"],
                                  f"{name} received_at")
        if received < requested or received > now:
            raise ValueError(f"Invalid {name} response timing")
        started.append(requested)
        finished.append(received)
        bodies[name] = envelope["body"]

    captured_at = max(finished)
    if (captured_at - min(started)).total_seconds() > max_capture_span_seconds:
        raise ValueError("Account inventory capture span is too wide")
    if (now - captured_at).total_seconds() > max_snapshot_age_seconds:
        raise ValueError("Account inventory capture is stale")

    account_body = bodies["account"]
    positions_body = bodies["positions"]
    orders_body = bodies["open_orders"]
    assert isinstance(account_body, dict)
    assert isinstance(positions_body, list)
    assert isinstance(orders_body, list)
    if len(orders_body) >= 500:
        raise ValueError("Open-order inventory may be truncated at page limit")

    account_fields = {
        "status", "crypto_status", "trading_blocked", "account_blocked",
        "trade_suspended_by_user", "multiplier", "cash", "buying_power",
        "equity", "last_equity",
    }
    if not account_fields.issubset(account_body):
        raise ValueError("Alpaca account response is missing required fields")
    position_fields = {"symbol", "asset_class", "side", "qty", "cost_basis"}
    order_fields = {
        "id", "client_order_id", "symbol", "asset_class", "side", "status",
        "type", "qty", "notional", "limit_price",
    }
    if any(not isinstance(row, dict) or not position_fields.issubset(row)
           for row in positions_body):
        raise ValueError("Alpaca position response is missing required fields")
    if any(not isinstance(row, dict) or not order_fields.issubset(row)
           for row in orders_body):
        raise ValueError("Alpaca order response is missing required fields")

    return {
        "provider": "alpaca",
        "paper_base_url": capture["base_url"],
        "captured_at": captured_at.isoformat(),
        "paper_endpoint_verified": True,
        "positions_complete": True,
        "open_orders_complete": True,
        "account": {name: account_body[name] for name in account_fields},
        "positions": [
            {name: row[name] for name in position_fields}
            for row in positions_body
        ],
        "open_orders": [
            {name: row[name] for name in order_fields}
            for row in orders_body
        ],
    }


def validate_crypto_account_preflight(snapshot: dict, *, contract: dict,
                                      policy: AccountInventoryPolicy,
                                      observed_at: datetime,
                                      max_snapshot_age_seconds: int = 30) -> dict:
    """Audit a complete paper-account snapshot before one crypto buy.

    This pure function accepts caller-captured account, position, and open-order
    GET results.  It reserves existing open buys, counts long positions across
    equities/options/crypto, and rejects margin-like buying power or ambiguous
    inventory.  It never fetches provider state or permits broker submission.
    """
    if not isinstance(snapshot, dict) or not isinstance(contract, dict):
        raise ValueError("Snapshot and validated contract must be objects")
    required_snapshot = {
        "provider", "paper_base_url", "captured_at",
        "paper_endpoint_verified", "positions_complete", "open_orders_complete",
        "account", "positions", "open_orders",
    }
    if set(snapshot) != required_snapshot:
        raise ValueError("Exact account snapshot fields are required")
    if not all(snapshot[name] is True for name in (
            "paper_endpoint_verified", "positions_complete", "open_orders_complete")):
        raise ValueError("Paper account inventory is incomplete or unverified")
    if (snapshot["provider"] != "alpaca"
            or snapshot["paper_base_url"] != "https://paper-api.alpaca.markets"):
        raise ValueError("Alpaca paper snapshot provenance is unverified")
    if (not isinstance(max_snapshot_age_seconds, int)
            or isinstance(max_snapshot_age_seconds, bool)
            or max_snapshot_age_seconds <= 0):
        raise ValueError("Snapshot freshness limit must be a positive integer")
    captured_at = _snapshot_time(snapshot["captured_at"], "captured_at")
    now = _snapshot_time(observed_at, "observed_at")
    age = (now - captured_at).total_seconds()
    if age < 0 or age > max_snapshot_age_seconds:
        raise ValueError("Account inventory snapshot is stale or future-dated")
    if (contract.get("broker_submit_allowed") is not False
            or contract.get("execution_evidence") is not False):
        raise ValueError("Only an offline validated contract is accepted")
    symbol = contract.get("symbol")
    client_id = contract.get("client_order_id")
    if not isinstance(symbol, str) or not symbol or not isinstance(client_id, str):
        raise ValueError("Contract symbol and stable client_order_id are required")
    new_debit = _snapshot_amount(contract.get("estimated_total_debit"),
                                 "contract total debit")

    account = snapshot["account"]
    positions = snapshot["positions"]
    open_orders = snapshot["open_orders"]
    if not isinstance(account, dict) or not isinstance(positions, list) \
            or not isinstance(open_orders, list):
        raise ValueError("Malformed account inventory snapshot")
    if (account.get("status") != "ACTIVE"
            or account.get("crypto_status") not in {
                "ACTIVE", "APPROVED", "PAPER_ONLY"}
            or any(account.get(flag) is not False for flag in (
                "trading_blocked", "account_blocked", "trade_suspended_by_user"))):
        raise ValueError("Paper account or crypto trading is not active")
    if str(account.get("multiplier")) != "1":
        raise ValueError("Cash-only account multiplier is not verified")
    cash = _snapshot_amount(account.get("cash"), "account cash", allow_zero=True)
    buying_power = _snapshot_amount(account.get("buying_power"),
                                    "account buying power", allow_zero=True)
    equity = _snapshot_amount(account.get("equity"), "account equity")
    last_equity = _snapshot_amount(account.get("last_equity"),
                                   "prior account equity")
    if buying_power > cash:
        raise ValueError("Buying power exceeds cash; margin-like capacity blocked")
    daily_loss = max(Decimal("0"), last_equity - equity)
    if daily_loss >= policy.max_daily_loss:
        raise ValueError("Account-wide daily loss limit reached")

    allowed_assets = {"us_equity", "us_option", "crypto"}
    seen_positions: set[tuple[str, str]] = set()
    position_symbols: set[str] = set()
    position_quantities: dict[tuple[str, str], Decimal] = {}
    exposure = Decimal("0")
    for position in positions:
        if not isinstance(position, dict) or set(position) != {
                "symbol", "asset_class", "side", "qty", "cost_basis"}:
            raise ValueError("Malformed position inventory")
        key = (position.get("asset_class"), position.get("symbol"))
        if (key[0] not in allowed_assets or not isinstance(key[1], str)
                or not key[1] or key in seen_positions):
            raise ValueError("Unsupported or duplicate position inventory")
        if position.get("side") != "long":
            raise ValueError("Short positions violate cash-only policy")
        position_quantity = _snapshot_amount(position.get("qty"),
                                               "position quantity")
        exposure += _snapshot_amount(position.get("cost_basis"),
                                     "position cost basis")
        seen_positions.add(key)
        position_symbols.add(key[1])
        position_quantities[key] = position_quantity

    if symbol in position_symbols:
        raise ValueError("Existing position duplicates intended crypto symbol")
    if len(positions) + 1 > policy.max_open_positions:
        raise ValueError("Maximum open-position count would be exceeded")

    open_statuses = {
        "new", "accepted", "pending_new", "partially_filled",
        "pending_cancel", "pending_replace", "accepted_for_bidding", "held",
    }
    seen_order_ids: set[str] = set()
    seen_client_ids: set[str] = set()
    pending_sell_quantities: dict[tuple[str, str], Decimal] = {}
    reserved_buys = Decimal("0")
    for order in open_orders:
        if not isinstance(order, dict) or set(order) != {
                "id", "client_order_id", "symbol", "asset_class", "side",
                "status", "type", "qty", "notional", "limit_price"}:
            raise ValueError("Malformed open-order inventory")
        order_id = order.get("id")
        order_client_id = order.get("client_order_id")
        order_symbol = order.get("symbol")
        if (not isinstance(order_id, str) or not order_id
                or not isinstance(order_client_id, str) or not order_client_id
                or order_id in seen_order_ids or order_client_id in seen_client_ids):
            raise ValueError("Duplicate or missing open-order identity")
        if (order.get("asset_class") not in allowed_assets
                or order.get("status") not in open_statuses
                or order.get("side") not in {"buy", "sell"}
                or not isinstance(order_symbol, str) or not order_symbol):
            raise ValueError("Unsupported open-order inventory")
        if order_symbol == symbol or order_client_id == client_id:
            raise ValueError("Duplicate position/order intent detected")
        if order.get("side") == "sell":
            if order.get("qty") is None or order.get("notional") is not None:
                raise ValueError("Open sell must use an exact closing quantity")
            position_key = (order.get("asset_class"), order_symbol)
            sell_quantity = _snapshot_amount(order["qty"],
                                              "open sell quantity")
            pending = pending_sell_quantities.get(position_key, Decimal("0"))
            if (position_key not in position_quantities
                    or pending + sell_quantity > position_quantities[position_key]):
                raise ValueError("Open sells could create a short position")
            pending_sell_quantities[position_key] = pending + sell_quantity
        else:
            has_qty = order.get("qty") is not None
            has_notional = order.get("notional") is not None
            if has_qty == has_notional:
                raise ValueError("Open buy requires exactly one sizing mode")
            if has_notional:
                if order.get("asset_class") == "us_option":
                    raise ValueError("Option buys cannot use notional sizing")
                reserved_buys += _snapshot_amount(order["notional"],
                                                  "open-order notional")
            else:
                if order.get("type") not in {"limit", "stop_limit"} \
                        or order.get("limit_price") is None:
                    raise ValueError("Open market buy cannot be reserved safely")
                reserved_buys += (
                    _snapshot_amount(order["qty"], "open-order quantity")
                    * _snapshot_amount(order["limit_price"],
                                       "open-order limit price")
                    * (Decimal("100") if order.get("asset_class") == "us_option"
                       else Decimal("1"))
                )
        seen_order_ids.add(order_id)
        seen_client_ids.add(order_client_id)

    if reserved_buys + new_debit > buying_power:
        raise ValueError("Open buys plus intended order exceed cash buying power")
    projected_exposure = exposure + reserved_buys + new_debit
    if projected_exposure > policy.max_total_exposure:
        raise ValueError("Projected account-wide exposure exceeds policy")
    return {
        "paper_endpoint_verified": True,
        "existing_positions": len(positions),
        "existing_exposure": str(exposure),
        "reserved_open_buys": str(reserved_buys),
        "intended_total_debit": str(new_debit),
        "projected_exposure": str(projected_exposure),
        "account_daily_loss": str(daily_loss),
        "broker_submit_allowed": False,
        "execution_evidence": False,
        "warning": "Offline inventory preflight only; independent broker readback still required.",
    }


@dataclass(frozen=True)
class RiskPolicy:
    max_order_cost: Decimal
    max_total_exposure: Decimal
    max_daily_loss: Decimal
    max_spread_fraction: Decimal = Decimal("0.15")
    max_quote_age_seconds: int = 15
    option_fee_per_contract: Decimal = Decimal("0.65")

    def __post_init__(self) -> None:
        for name in ("max_order_cost", "max_total_exposure", "max_daily_loss",
                     "max_spread_fraction"):
            object.__setattr__(self, name, amount(getattr(self, name)))
        if isinstance(self.option_fee_per_contract, float):
            raise ValueError("Use a decimal string for option fees")
        fee = Decimal(self.option_fee_per_contract)
        if not fee.is_finite():
            raise ValueError("Option fee must be finite")
        object.__setattr__(self, "option_fee_per_contract", fee)
        if self.max_quote_age_seconds <= 0 or self.option_fee_per_contract < 0:
            raise ValueError("Invalid quote-age or fee policy")


class PaperEngine:
    """Persists paper fills atomically and rejects all unknown/unsafe execution."""

    def __init__(self, database: Path, starting_cash: Decimal, policy: RiskPolicy):
        self.database = Path(database)
        self.policy = policy
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS account (
                    id INTEGER PRIMARY KEY CHECK(id = 1), cash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT NOT NULL, asset TEXT NOT NULL, multiplier TEXT NOT NULL,
                    quantity TEXT NOT NULL, avg_cost TEXT NOT NULL,
                    PRIMARY KEY(symbol, asset)
                );
                CREATE TABLE IF NOT EXISTS orders (
                    client_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                    timestamp TEXT NOT NULL, symbol TEXT NOT NULL, asset TEXT NOT NULL,
                    side TEXT NOT NULL, quantity TEXT NOT NULL, status TEXT NOT NULL,
                    reason TEXT NOT NULL, fill_price TEXT, fee TEXT,
                    realized_pnl TEXT NOT NULL DEFAULT '0',
                    signal_id TEXT, limit_price TEXT, quote_bid TEXT, quote_ask TEXT,
                    quote_source TEXT, quote_asof TEXT, quote_delayed INTEGER
                );
            """)
            # Existing v0.1 SQLite journals must remain readable and recoverable.
            current = {row["name"] for row in conn.execute("PRAGMA table_info(orders)")}
            for name, column_type in {
                "signal_id": "TEXT", "limit_price": "TEXT", "quote_bid": "TEXT",
                "quote_ask": "TEXT", "quote_source": "TEXT", "quote_asof": "TEXT",
                "quote_delayed": "INTEGER",
            }.items():
                if name not in current:
                    conn.execute(f"ALTER TABLE orders ADD COLUMN {name} {column_type}")
            conn.execute("INSERT OR IGNORE INTO account(id, cash) VALUES(1, ?)",
                         (str(amount(starting_cash)),))

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def snapshot(self) -> dict:
        with self._connect() as conn:
            cash = Decimal(conn.execute("SELECT cash FROM account WHERE id=1").fetchone()[0])
            positions = [dict(row) for row in conn.execute("SELECT * FROM positions ORDER BY asset, symbol")]
            return {"cash": str(cash), "positions": positions, "paper_only": True}

    def orders(self) -> list[dict]:
        with self._connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM orders ORDER BY timestamp, client_id")]

    def performance(self) -> dict:
        """Observed *paper* exits only, not a forecast or strategy backtest."""
        records = self.orders()
        exits = [Decimal(row["realized_pnl"]) for row in records
                 if row["side"] == "sell" and row["status"] == "FILLED"]
        wins = sum(value > 0 for value in exits)
        losses = sum(value < 0 for value in exits)
        return {
            "paper_only": True,
            "filled_orders": sum(row["status"] == "FILLED" for row in records),
            "rejected_orders": sum(row["status"] == "REJECTED" for row in records),
            "closed_exits": len(exits),
            "winning_exits": wins,
            "losing_exits": losses,
            "realized_pnl": str(sum(exits, Decimal("0"))),
            "win_rate": str(Decimal(wins) / Decimal(len(exits))) if exits else None,
            "warning": "Exit-leg statistics only; no out-of-sample edge or live performance implied",
        }

    def daily_risk_state(self, asof: datetime) -> dict:
        """Report the persisted, account-wide UTC-day realized-loss guard."""
        when = _utc(asof)
        with self._connect() as conn:
            return self._daily_risk_state(conn, when)

    def _daily_risk_state(self, conn: sqlite3.Connection,
                          when: datetime) -> dict:
        start = when.date().isoformat()
        end = (when.date() + timedelta(days=1)).isoformat()
        rows = conn.execute(
            "SELECT realized_pnl FROM orders "
            "WHERE status='FILLED' AND side='sell' "
            "AND timestamp>=? AND timestamp<?",
            (start, end),
        )
        realized = []
        try:
            realized = [Decimal(row[0]) for row in rows]
        except (ArithmeticError, TypeError, ValueError):
            realized = []
        if not all(value.is_finite() for value in realized):
            realized = []
        if not realized and conn.execute(
                "SELECT COUNT(*) FROM orders WHERE status='FILLED' AND side='sell' "
                "AND timestamp>=? AND timestamp<?", (start, end)).fetchone()[0]:
            return {
                "asof_utc": when.isoformat(),
                "gross_realized_loss": None,
                "net_realized_pnl": None,
                "limit": str(self.policy.max_daily_loss),
                "halted": True,
                "reason": "Malformed realized P/L journal; fail-closed halt",
            }
        gross_loss = sum((max(Decimal("0"), -value) for value in realized),
                         Decimal("0"))
        net = sum(realized, Decimal("0"))
        halted = gross_loss >= self.policy.max_daily_loss
        return {
            "asof_utc": when.isoformat(),
            "gross_realized_loss": str(gross_loss),
            "net_realized_pnl": str(net),
            "limit": str(self.policy.max_daily_loss),
            "halted": halted,
            "reason": ("Account-wide daily realized-loss limit reached"
                       if halted else "Within daily realized-loss limit"),
        }

    def submit(self, order: PaperOrder, quote: Quote, now: datetime) -> dict:
        """Attempt a single immediate limit fill. Unfilled limits are NOT queued."""
        when = _utc(now)
        canonical = {
            "symbol": order.instrument.symbol, "asset": order.instrument.asset,
            "multiplier": str(order.instrument.multiplier), "side": order.side,
            "quantity": str(order.quantity), "limit_price": str(order.limit_price),
        }
        if order.signal_id:
            canonical["signal_id"] = order.signal_id
        fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            previous = conn.execute("SELECT * FROM orders WHERE client_id=?", (order.client_id,)).fetchone()
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise ValueError("Client ID reused for a different order")
                return dict(previous)  # idempotent; no second fill

            status, reason, fill, fee, pnl = "REJECTED", "", None, Decimal("0"), Decimal("0")
            if quote.instrument != order.instrument:
                reason = "Quote instrument does not match order"
            elif quote.delayed:
                reason = "Delayed quote cannot validate an immediate entry"
            elif (_utc(quote.asof) > when or (when - _utc(quote.asof)).total_seconds() > self.policy.max_quote_age_seconds):
                reason = "Quote is stale or from the future"
            elif (quote.ask - quote.bid) / ((quote.ask + quote.bid) / 2) > self.policy.max_spread_fraction:
                reason = "Bid/ask spread exceeds policy"
            else:
                side_price = quote.ask if order.side == "buy" else quote.bid
                crosses = side_price <= order.limit_price if order.side == "buy" else side_price >= order.limit_price
                if not crosses:
                    status, reason = "NOT_FILLED", "Limit price not executable at quoted bid/ask"
                else:
                    fee = (self.policy.option_fee_per_contract * order.quantity
                           if order.instrument.asset == "option" else Decimal("0"))
                    fill = side_price
                    status, reason, pnl = self._execute(conn, order, fill, fee, when)
                    if status != "FILLED":
                        fill, fee = None, Decimal("0")

            conn.execute("""INSERT INTO orders
                (client_id, fingerprint, timestamp, symbol, asset, side, quantity,
                 status, reason, fill_price, fee, realized_pnl, signal_id,
                 limit_price, quote_bid, quote_ask, quote_source, quote_asof, quote_delayed)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (order.client_id, fingerprint, when.isoformat(), order.instrument.symbol,
                 order.instrument.asset, order.side, str(order.quantity), status, reason,
                 str(fill) if fill is not None else None, str(fee), str(pnl),
                 order.signal_id or None, str(order.limit_price), str(quote.bid),
                 str(quote.ask), quote.source, _utc(quote.asof).isoformat(),
                 int(quote.delayed)))
            return dict(conn.execute("SELECT * FROM orders WHERE client_id=?", (order.client_id,)).fetchone())

    def _execute(self, conn: sqlite3.Connection, order: PaperOrder, price: Decimal,
                 fee: Decimal, now: datetime) -> tuple[str, str, Decimal]:
        key = (order.instrument.symbol, order.instrument.asset)
        pos = conn.execute("SELECT * FROM positions WHERE symbol=? AND asset=?", key).fetchone()
        cash = Decimal(conn.execute("SELECT cash FROM account WHERE id=1").fetchone()[0])
        qty, mult = order.quantity, order.instrument.multiplier
        proceeds = qty * mult * price
        if pos and Decimal(pos["multiplier"]) != mult:
            return "REJECTED", "Position multiplier mismatch", Decimal("0")

        if order.side == "buy":
            cost = proceeds + fee
            exposure = sum(Decimal(row["quantity"]) * Decimal(row["avg_cost"])
                           for row in conn.execute("SELECT quantity, avg_cost FROM positions"))
            risk = self._daily_risk_state(conn, now)
            if risk["halted"]:
                return "REJECTED", risk["reason"], Decimal("0")
            losses = Decimal(risk["gross_realized_loss"])
            if cost > cash:
                return "REJECTED", "Cash-only buying power exceeded", Decimal("0")
            if cost > self.policy.max_order_cost:
                return "REJECTED", "Per-order cost cap exceeded", Decimal("0")
            if exposure + cost > self.policy.max_total_exposure:
                return "REJECTED", "Open exposure cap exceeded", Decimal("0")
            if exposure + cost + losses > self.policy.max_daily_loss:
                return "REJECTED", "Worst-case daily risk budget exceeded", Decimal("0")
            old_qty = Decimal(pos["quantity"]) if pos else Decimal("0")
            old_basis = Decimal(pos["avg_cost"]) if pos else Decimal("0")
            total_qty = old_qty + qty
            avg_cost = (old_qty * old_basis + cost) / total_qty
            conn.execute("INSERT OR REPLACE INTO positions VALUES(?, ?, ?, ?, ?)",
                         (*key, str(mult), str(total_qty), str(avg_cost)))
            conn.execute("UPDATE account SET cash=? WHERE id=1", (str(cash - cost),))
            return "FILLED", "Paper buy filled at ask", Decimal("0")

        held = Decimal(pos["quantity"]) if pos else Decimal("0")
        if held < qty:
            return "REJECTED", "Cannot sell more than held; shorting disabled", Decimal("0")
        realized = proceeds - fee - qty * Decimal(pos["avg_cost"])
        remaining = held - qty
        if remaining:
            conn.execute("UPDATE positions SET quantity=? WHERE symbol=? AND asset=?",
                         (str(remaining), *key))
        else:
            conn.execute("DELETE FROM positions WHERE symbol=? AND asset=?", key)
        conn.execute("UPDATE account SET cash=? WHERE id=1", (str(cash + proceeds - fee),))
        return "FILLED", "Paper sell-to-close filled at bid", realized
