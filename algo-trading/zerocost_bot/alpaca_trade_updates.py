"""Offline, non-authoritative Alpaca paper ``trade_updates`` ingestion.

Alpaca's trading stream delivers JSON messages in binary WebSocket frames.  This
module deliberately does not open a socket or call a broker.  It validates
captured fixtures, journals event observations durably, and keeps every order in
a GET-required state until a separate read-only broker reconciliation confirms
the result.

Missing stream messages are never evidence that an order did not fill.  A
disconnect/reconnect gap therefore changes tracked orders to
``UNKNOWN_REQUIRES_GET`` and replayed duplicates cannot clear that condition.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import sqlite3


MAX_FRAME_BYTES = 1_048_576


class TradeUpdateError(ValueError):
    """The offline frame or journal transition is unsafe to accept."""


def _utc_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise TradeUpdateError("trade update timestamp is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TradeUpdateError("trade update timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise TradeUpdateError("trade update timestamp must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _quantity(value: object) -> str:
    try:
        quantity = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise TradeUpdateError("filled quantity is invalid") from exc
    if not quantity.is_finite() or quantity < 0:
        raise TradeUpdateError("filled quantity is invalid")
    return format(quantity.normalize(), "f")


def parse_binary_frame(frame: object) -> dict[str, str]:
    """Decode one captured Alpaca binary frame without any network access."""
    if not isinstance(frame, (bytes, bytearray, memoryview)):
        raise TradeUpdateError("trade_updates must be supplied as a binary frame")
    raw = bytes(frame)
    if not raw or len(raw) > MAX_FRAME_BYTES:
        raise TradeUpdateError("binary frame is empty or too large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TradeUpdateError("binary frame is not UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("stream") != "trade_updates":
        raise TradeUpdateError("unexpected Alpaca stream")
    data = payload.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("order"), dict):
        raise TradeUpdateError("trade update data/order is missing")
    order = data["order"]
    event = data.get("event")
    order_id = order.get("id")
    client_order_id = order.get("client_order_id")
    status = order.get("status")
    if not all(isinstance(item, str) and item for item in
               (event, order_id, client_order_id, status)):
        raise TradeUpdateError("trade update identity/status is incomplete")
    occurred_at = _utc_timestamp(data.get("timestamp") or order.get("updated_at"))
    filled_qty = _quantity(order.get("filled_qty", "0"))
    normalized = {
        "event": event.lower(),
        "order_id": order_id,
        "client_order_id": client_order_id,
        "status": status.lower(),
        "occurred_at": occurred_at,
        "filled_qty": filled_qty,
    }
    normalized["event_key"] = hashlib.sha256(
        (order_id + "\0" + normalized["event"] + "\0" + occurred_at).encode()
    ).hexdigest()
    normalized["payload_sha256"] = hashlib.sha256(
        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return normalized


class TradeUpdateJournal:
    """Durable idempotency and fail-closed state for offline stream fixtures."""

    def __init__(self, path: str):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS events (
                event_key TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                client_order_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                observed_status TEXT NOT NULL,
                filled_qty TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                client_order_id TEXT NOT NULL,
                last_occurred_at TEXT NOT NULL,
                last_event_key TEXT NOT NULL,
                observed_state TEXT NOT NULL,
                reconciliation_state TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stream_gaps (
                gap_key TEXT PRIMARY KEY,
                occurred_at TEXT NOT NULL,
                reason TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def ingest_frame(self, frame: object) -> dict[str, object]:
        event = parse_binary_frame(frame)
        with self.connection:
            existing = self.connection.execute(
                "SELECT payload_sha256, order_id FROM events WHERE event_key = ?",
                (event["event_key"],),
            ).fetchone()
            if existing:
                if existing["payload_sha256"] != event["payload_sha256"]:
                    self._mark_unknown(event["order_id"])
                    return {"result": "CONFLICT_UNKNOWN", "broker_confirmed": False}
                return {"result": "DUPLICATE_IGNORED", "broker_confirmed": False}

            current = self.connection.execute(
                "SELECT * FROM orders WHERE order_id = ?", (event["order_id"],)
            ).fetchone()
            self.connection.execute(
                """INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (event["event_key"], event["order_id"], event["client_order_id"],
                 event["occurred_at"], event["event"], event["status"],
                 event["filled_qty"], event["payload_sha256"]),
            )
            if current and event["occurred_at"] <= current["last_occurred_at"]:
                if event["occurred_at"] == current["last_occurred_at"]:
                    self._mark_unknown(event["order_id"])
                    return {"result": "AMBIGUOUS_ORDER_UNKNOWN", "broker_confirmed": False}
                return {"result": "OUT_OF_ORDER_IGNORED", "broker_confirmed": False}

            observed = "OBSERVED_" + event["event"].upper() + "_PENDING_GET"
            self.connection.execute(
                """INSERT INTO orders
                   (order_id, client_order_id, last_occurred_at, last_event_key,
                    observed_state, reconciliation_state)
                   VALUES (?, ?, ?, ?, ?, 'GET_REQUIRED')
                   ON CONFLICT(order_id) DO UPDATE SET
                    client_order_id=excluded.client_order_id,
                    last_occurred_at=excluded.last_occurred_at,
                    last_event_key=excluded.last_event_key,
                    observed_state=excluded.observed_state,
                    reconciliation_state='GET_REQUIRED'""",
                (event["order_id"], event["client_order_id"], event["occurred_at"],
                 event["event_key"], observed),
            )
        return {"result": "OBSERVED_PENDING_GET", "broker_confirmed": False}

    def _mark_unknown(self, order_id: str) -> None:
        self.connection.execute(
            """UPDATE orders SET observed_state='UNKNOWN_REQUIRES_GET',
               reconciliation_state='GET_REQUIRED' WHERE order_id=?""", (order_id,)
        )

    def mark_stream_gap(self, reason: str, occurred_at: str) -> dict[str, object]:
        """Persist a disconnect/reconnect gap; never infer no fill from silence."""
        if not isinstance(reason, str) or not reason.strip():
            raise TradeUpdateError("stream gap reason is required")
        timestamp = _utc_timestamp(occurred_at)
        gap_key = hashlib.sha256((timestamp + "\0" + reason).encode()).hexdigest()
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO stream_gaps VALUES (?, ?, ?)",
                (gap_key, timestamp, reason.strip()),
            )
            self.connection.execute(
                """UPDATE orders SET observed_state='UNKNOWN_REQUIRES_GET',
                   reconciliation_state='GET_REQUIRED'"""
            )
        return {"result": "STREAM_GAP_UNKNOWN", "broker_confirmed": False}

    def order_state(self, order_id: str) -> dict[str, object] | None:
        row = self.connection.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["broker_confirmed"] = False
        return result

    def event_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])
