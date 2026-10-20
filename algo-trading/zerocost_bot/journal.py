"""Durable idempotent proposal journal.

Guarantees at-most-one LOCAL reservation per strategy/symbol/bar across process
restarts; it does not guarantee exactly-once remote execution. After unknown
outcomes, reconcile broker by client_order_id BEFORE doing anything else.
No broker HTTP or trade calls exist in this module.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import os
import sqlite3


def order_key(strategy: str, symbol: str, completed_bar_at: datetime) -> str:
    if completed_bar_at.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    if not strategy or not symbol:
        raise ValueError("missing identity")
    raw = f"{strategy}|{symbol.upper()}|{completed_bar_at.astimezone(timezone.utc).isoformat()}"
    return "sf-research-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


class OrderJournal:
    """Fail closed: any existing key blocks new submission, including errors."""

    def __init__(self, path: str):
        if not path or path == ":memory:":
            raise ValueError("on-disk journal required for crash recovery")
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with self._connect() as db:
            db.execute("""
            CREATE TABLE IF NOT EXISTS proposal_events (
                client_order_id TEXT PRIMARY KEY,
                strategy TEXT NOT NULL,
                symbol TEXT NOT NULL,
                bar_time TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                broker_order_id TEXT,
                UNIQUE(strategy, symbol, bar_time)
            )""")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA busy_timeout=5000")
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def reserve(self, strategy: str, symbol: str, bar_at: datetime):
        """Returns (new_reservation, immutable client id). NEVER auto-retries."""
        key = order_key(strategy, symbol, bar_at)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT client_order_id FROM proposal_events WHERE client_order_id=?",
                             (key,)).fetchone()
            if row:
                db.execute("COMMIT")
                return False, key
            db.execute("""INSERT INTO proposal_events
                (client_order_id, strategy, symbol, bar_time, state, created_at, updated_at)
                VALUES(?,?,?,?,?,?,?)""", (
                key, strategy, symbol.upper(), bar_at.astimezone(timezone.utc).isoformat(),
                "reserved", now, now
            ))
            db.execute("COMMIT")
        return True, key

    def transition(self, client_order_id: str, new_state: str, broker_order_id: str = ""):
        """Manual reconciliation states. Unknown state MUST NOT be replayed."""
        transitions = {
            "reserved": {"submitted", "unknown", "cancelled"},
            "submitted": {"acknowledged", "filled", "partially_filled", "rejected", "unknown", "cancelled"},
            "unknown": {"acknowledged", "filled", "partially_filled", "rejected", "cancelled"},
            "acknowledged": {"partially_filled", "filled", "rejected", "cancelled"},
            "partially_filled": {"filled", "cancelled"},
            "filled": {"closed"},
            "rejected": set(), "cancelled": set(), "closed": set()
        }
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM proposal_events WHERE client_order_id=?",
                             (client_order_id,)).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise KeyError("proposal not found")
            if new_state not in transitions[row[0]]:
                db.execute("ROLLBACK")
                raise ValueError("unsafe journal state transition")
            db.execute("""UPDATE proposal_events SET state=?,broker_order_id=?,updated_at=?
                          WHERE client_order_id=?""",
                       (new_state, broker_order_id or None,
                        datetime.now(timezone.utc).isoformat(), client_order_id))
            db.execute("COMMIT")

    def status(self, client_order_id: str):
        with self._connect() as db:
            row = db.execute("""SELECT state, broker_order_id
                                FROM proposal_events WHERE client_order_id=?""",
                             (client_order_id,)).fetchone()
            return {"state": row[0], "broker_order_id": row[1]} if row else None
