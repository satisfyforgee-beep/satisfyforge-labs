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
            losses = sum(max(Decimal("0"), -Decimal(row[0])) for row in conn.execute(
                "SELECT realized_pnl FROM orders WHERE status='FILLED' AND side='sell' AND timestamp>=? AND timestamp<?",
                (now.date().isoformat(), (now.date() + timedelta(days=1)).isoformat())))
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
