"""Durable cash-only PAPER REPLAY capital accounting, not a broker adapter.

Receives ordered, externally *already verified* fill/terminal/settlement events.
No HTTP, broker credentials, background jobs, market predictions or order routes.
The caller must reconcile paper broker evidence before importing events.
Cash freed by a sell is NOT spendable until a distinct settlement event.
All output is explicitly offline simulation, not brokerage account truth.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
import os
import re
import sqlite3

CENT = Decimal("0.01")
TYPES = {"stock": Decimal(1), "crypto": Decimal(1), "option": Decimal(100)}
IDENT = re.compile(r"[A-Za-z0-9_.:-]{1,80}$")
STOCK = re.compile(r"[A-Z][A-Z0-9.]{0,9}$")
CRYPTO = re.compile(r"[A-Z0-9]{2,15}[/\-][A-Z0-9]{2,15}$")
OPTION = re.compile(r"[A-Z]{1,6}[0-9]{6}[CP][0-9]{8}$")


class CapitalBlocked(ValueError):
    """Fail closed: never treat this as an order acceptance."""


def dec(value, *, zero=False):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise CapitalBlocked("invalid decimal") from None
    if not d.is_finite() or (d < 0 if zero else d <= 0):
        raise CapitalBlocked("nonpositive or nonfinite amount")
    return d


def cents(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def ident(value):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise CapitalBlocked("invalid event identity")
    return value


def instrument(asset, symbol, quantity):
    if asset not in TYPES or not isinstance(symbol, str):
        raise CapitalBlocked("unsupported asset type")
    checks = {"stock": STOCK, "option": OPTION, "crypto": CRYPTO}
    if not checks[asset].fullmatch(symbol):
        raise CapitalBlocked("invalid instrument identifier")
    q = dec(quantity)
    if asset != "crypto" and q != q.to_integral_value():
        raise CapitalBlocked("stock shares and option contracts must be whole")
    if asset == "crypto" and q.as_tuple().exponent < -8:
        raise CapitalBlocked("crypto precision exceeds eight decimals")
    return q


def at_utc(when):
    if not isinstance(when, datetime) or when.tzinfo is None:
        raise CapitalBlocked("timezone-aware timestamp required")
    return when.astimezone(timezone.utc).isoformat()


class PaperCapital:
    """An OFFLINE replay ledger; distinct from Tradier/Alpaca broker balances.

    A local, private SQLite database stores replay events. Reserve the maximum
    debit before a buy. A fill debits only settled funds, reduces its hold, and
    cannot spend proceeds awaiting independently confirmed settlement.
    """

    def __init__(self, path, *, opening_cash="150.00",
                 maximum_order_debit="30.00", maximum_reservations=5):
        if not path or str(path) == ":memory:":
            raise CapitalBlocked("durable on-disk paper ledger required")
        self.path = Path(path).expanduser().absolute()
        if self.path.is_symlink():
            raise CapitalBlocked("symlinked ledger denied")
        if self.path.exists() and not self.path.is_file():
            raise CapitalBlocked("invalid ledger file")
        cash = cents(dec(opening_cash))
        cap = cents(dec(maximum_order_debit))
        if cash <= 0 or cap <= 0 or cap > cash:
            raise CapitalBlocked("invalid initial cash/order cap")
        if type(maximum_reservations) is not int or not 1 <= maximum_reservations <= 100:
            raise CapitalBlocked("invalid reservation cap")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.opening_cash = cash
        self.max_order = cap
        self.max_reservations = maximum_reservations
        with closing(self._db()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS capital_config(
                key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS capital_events(
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                reference TEXT NOT NULL,
                asset TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price TEXT NOT NULL,
                fee TEXT NOT NULL,
                amount TEXT NOT NULL,
                observed_at TEXT NOT NULL)""")
            existing = dict(db.execute("SELECT key, value FROM capital_config"))
            expected = {"opening_cash": str(cash), "max_order": str(cap),
                        "max_reservations": str(maximum_reservations)}
            if existing and existing != expected:
                raise CapitalBlocked("ledger policy changed; refuse silent reset")
            if not existing:
                db.executemany("INSERT INTO capital_config VALUES (?, ?)",
                               expected.items())
        os.chmod(self.path, 0o600)

    def _db(self):
        if self.path.is_symlink():
            raise CapitalBlocked("symlinked ledger denied")
        db = sqlite3.connect(str(self.path), timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _reduce(self, rows):
        settled = self.opening_cash
        reserves = {}
        lots = {}
        pending = {}
        realized = Decimal(0)
        for row in rows:
            (_eid, kind, reference, asset, symbol, qty, price,
             fee, amount, _when) = row
            q, p, f, a = map(Decimal, (qty, price, fee, amount))
            key = (asset, symbol)
            if kind == "reserve":
                if reference in reserves:
                    raise CapitalBlocked("duplicate reservation")
                active_positions = sum(
                    sum(lot[0] for lot in holdings) > 0
                    for holdings in lots.values()
                )
                if len(reserves) + active_positions >= self.max_reservations:
                    raise CapitalBlocked("maximum concurrent positions/intents reached")
                if a > self.max_order or a <= 0:
                    raise CapitalBlocked("per-intent simulated debit limit")
                if a > settled - sum((v[2] for v in reserves.values()), Decimal(0)):
                    raise CapitalBlocked("insufficient settled cash after holds")
                reserves[reference] = (asset, symbol, a, q, p, f)
            elif kind == "buy":
                if reference not in reserves:
                    raise CapitalBlocked("buy fill has no pre-reserved intent")
                held_asset, held_symbol, held, remaining_q, limit_p, remaining_fee = reserves[reference]
                if ((held_asset, held_symbol) != key or a <= 0 or a > held
                        or q > remaining_q or p > limit_p or f > remaining_fee):
                    raise CapitalBlocked("buy fill exceeds reserved quantity, price, fee or debit")
                if a > settled:
                    raise CapitalBlocked("cannot spend unsettled proceeds")
                settled -= a
                reserves[reference] = (asset, symbol, held - a,
                                       remaining_q - q, limit_p, remaining_fee - f)
                lots.setdefault(key, []).append([q, a])
            elif kind == "sell":
                remaining = q
                basis = Decimal(0)
                for lot in lots.get(key, []):
                    if remaining <= 0:
                        break
                    take = min(lot[0], remaining)
                    if take:
                        allocation = lot[1] * (take / lot[0])
                        lot[0] -= take
                        lot[1] -= allocation
                        basis += allocation
                        remaining -= take
                if remaining > 0:
                    raise CapitalBlocked("sell without confirmed long inventory")
                if _eid in pending:
                    raise CapitalBlocked("duplicate settlement source")
                pending[_eid] = a
                realized += a - basis
            elif kind == "settle":
                if reference not in pending:
                    raise CapitalBlocked("unmatched or repeated settlement")
                settled += pending.pop(reference)
            elif kind == "release":
                if reference not in reserves:
                    raise CapitalBlocked("release without active reservation")
                del reserves[reference]
            else:
                raise CapitalBlocked("unknown replay event")
            if settled < 0:
                raise CapitalBlocked("negative settled cash")
        reserved = sum((v[2] for v in reserves.values()), Decimal(0))
        if reserved > settled:
            raise CapitalBlocked("reservations exceed settled funds")
        return {
            "mode": "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE",
            "opening_cash": str(self.opening_cash),
            "settled_cash": str(cents(settled)),
            "unsettled_sale_proceeds": str(cents(sum(pending.values(), Decimal(0)))),
            "reserved_cash": str(cents(reserved)),
            "available_for_next_paper_trade": str(cents(settled - reserved)),
            "realized_net_pnl": str(cents(realized)),
            "maximum_order_debit": str(self.max_order),
            "active_reservation_count": len(reserves),
            "positions": [
                {"asset": asset, "symbol": symbol,
                 "quantity": str(sum(x[0] for x in holdings)),
                 "remaining_book_cost": str(cents(sum(x[1] for x in holdings)))}
                for (asset, symbol), holdings in sorted(lots.items())
                if sum(x[0] for x in holdings) > 0
            ],
            "pending_settlement_count": len(pending),
        }

    def snapshot(self):
        with closing(self._db()) as db:
            return self._reduce(db.execute(
                "SELECT event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at FROM capital_events ORDER BY sequence").fetchall())

    def _append(self, event_id, kind, reference, asset, symbol, quantity,
                price, fee, amount, when):
        eid, ref = ident(event_id), ident(reference)
        ts = at_utc(when)
        fields = (eid, kind, ref, asset, symbol,
                  str(quantity), str(price), str(fee), str(amount), ts)
        db = self._db()
        try:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at FROM capital_events WHERE event_id=?",
                (eid,)).fetchone()
            if existing:
                if existing != fields:
                    raise CapitalBlocked("conflicting duplicate paper execution ID")
                db.commit()
                return False
            rows = db.execute(
                "SELECT event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at FROM capital_events ORDER BY sequence").fetchall()
            self._reduce(rows + [fields])
            db.execute("""INSERT INTO capital_events
                (event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""", fields)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def reserve_buy(self, intent_id, asset, symbol, quantity, limit_price,
                    maximum_fee, *, when):
        q = instrument(asset, symbol, quantity)
        p, fee = dec(limit_price), dec(maximum_fee, zero=True)
        debit = cents(q * p * TYPES[asset] + fee)
        if debit <= 0:
            raise CapitalBlocked("invalid reserve debit")
        return self._append("reserve:" + ident(intent_id), "reserve", intent_id,
                            asset, symbol, q, p, fee, debit, when)

    def buy_fill(self, execution_id, intent_id, asset, symbol, quantity,
                 price, fee, *, when):
        q = instrument(asset, symbol, quantity)
        p, f = dec(price), dec(fee, zero=True)
        cost = cents(q * p * TYPES[asset] + f)
        if cost <= 0:
            raise CapitalBlocked("invalid buy fill debit")
        return self._append("buy:" + ident(execution_id), "buy", intent_id,
                            asset, symbol, q, p, f, cost, when)

    def sell_fill(self, execution_id, asset, symbol, quantity, price, fee, *, when):
        q = instrument(asset, symbol, quantity)
        p, f = dec(price, zero=(asset == "option")), dec(fee, zero=True)
        proceeds = cents(q * p * TYPES[asset] - f)
        if proceeds < 0:
            raise CapitalBlocked("negative sell proceeds")
        return self._append("sell:" + ident(execution_id), "sell", execution_id,
                            asset, symbol, q, p, f, proceeds, when)

    def confirm_settlement(self, settlement_id, sale_execution_id, *, when):
        return self._append("settle:" + ident(settlement_id), "settle",
                            "sell:" + ident(sale_execution_id),
                            "none", "none", 0, 0, 0, 0, when)

    def release_terminal_reservation(self, terminal_event_id, intent_id, *, when):
        """Caller MUST first verify broker order terminal state; no broker check here."""
        return self._append("release:" + ident(terminal_event_id), "release",
                            intent_id, "none", "none", 0, 0, 0, 0, when)
