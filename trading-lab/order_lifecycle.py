"""Deterministic, offline reconciliation of broker order lifecycle observations.

This module does not open a socket, call a REST endpoint, read credentials, or
submit/cancel/replace an order.  It is a fail-closed contract fixture for future
paper adapters.  Provider observations remain non-authoritative after a stream
gap until the caller supplies an independently read REST snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Dict, Iterable, Mapping, Optional


TRADE_UPDATES = "trade_updates"

KNOWN_EVENTS = {
    "new", "accepted", "pending_new", "partial_fill", "fill", "canceled",
    "expired", "done_for_day", "replaced", "rejected", "stopped",
    "pending_cancel", "pending_replace", "calculated", "suspended",
    "order_replace_rejected", "order_cancel_rejected",
}

TERMINAL_EVENTS = {"fill", "canceled", "expired", "replaced", "rejected"}
FILL_EVENTS = {"partial_fill", "fill"}
OPERATION_REJECTIONS = {"order_replace_rejected", "order_cancel_rejected"}
REST_STATUSES = {
    "new", "accepted", "pending_new", "partially_filled", "filled", "canceled",
    "expired", "done_for_day", "replaced", "rejected", "stopped",
    "pending_cancel", "pending_replace", "accepted_for_bidding", "calculated",
    "suspended",
}


def _decimal(value: object, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a decimal") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return number


def _fingerprint(update: Mapping[str, object]) -> str:
    encoded = json.dumps(update, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass
class OrderState:
    order_id: str
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    status: str = "unknown"
    last_event: str = "unknown"
    terminal: bool = False
    rest_verified: bool = False
    seen_observations: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "quantity": str(self.quantity),
            "filled_quantity": str(self.filled_quantity),
            "status": self.status,
            "last_event": self.last_event,
            "terminal": self.terminal,
            "rest_verified": self.rest_verified,
        }


class OrderLifecycleReconciler:
    """Pure state machine for recorded observations from a future paper adapter."""

    def __init__(self) -> None:
        self.listening = False
        self.readback_required = False
        self.orders: Dict[str, OrderState] = {}

    def acknowledge_streams(self, streams: Iterable[str]) -> dict:
        self.listening = TRADE_UPDATES in set(streams)
        return self.readiness()

    def disconnect(self) -> dict:
        self.listening = False
        self.readback_required = True
        for state in self.orders.values():
            state.rest_verified = False
        return self.readiness()

    def readiness(self) -> dict:
        authoritative = self.listening and not self.readback_required
        return {
            "trade_updates_acknowledged": self.listening,
            "rest_readback_required": self.readback_required,
            "state_authoritative": authoritative,
            # This fixture is evidence about reconciliation only, never execution.
            "broker_submission_enabled": False,
            "mode": "OFFLINE_ORDER_LIFECYCLE_RECONCILIATION",
        }

    def apply_rest_snapshot(self, snapshots: Iterable[Mapping[str, object]]) -> dict:
        """Replace order state after reconnect using caller-supplied REST records."""
        if not self.listening:
            return self._halt("HALT_SUBSCRIPTION_UNVERIFIED")

        rebuilt: Dict[str, OrderState] = {}
        for snapshot in snapshots:
            order_id = str(snapshot.get("id", "")).strip()
            if not order_id:
                raise ValueError("REST order snapshot requires id")
            quantity = _decimal(snapshot.get("qty"), "qty")
            filled = _decimal(snapshot.get("filled_qty", "0"), "filled_qty")
            if quantity <= 0 or filled > quantity:
                raise ValueError("REST quantities are inconsistent")
            status = str(snapshot.get("status", "unknown"))
            if status not in REST_STATUSES:
                raise ValueError("REST order status is unknown")
            previous = self.orders.get(order_id)
            rebuilt[order_id] = OrderState(
                order_id=order_id,
                quantity=quantity,
                filled_quantity=filled,
                status=status,
                last_event="rest_readback",
                terminal=status in {"filled", "canceled", "expired", "replaced", "rejected"},
                rest_verified=True,
                seen_observations=dict(previous.seen_observations) if previous else {},
            )
        missing = set(self.orders) - set(rebuilt)
        if missing:
            return self._halt("HALT_REST_READBACK_INCOMPLETE")
        self.orders = rebuilt
        self.readback_required = False
        return {"result": "REST_READBACK_APPLIED", **self.readiness(),
                "orders": [state.as_dict() for state in self.orders.values()]}

    def apply_trade_update(self, update: Mapping[str, object],
                           observation_id: Optional[str] = None) -> dict:
        if not self.listening:
            return self._halt("HALT_SUBSCRIPTION_UNVERIFIED")
        if self.readback_required:
            return self._halt("HALT_RECONNECT_READBACK_REQUIRED")

        event = str(update.get("event", ""))
        if event not in KNOWN_EVENTS:
            self.readback_required = True
            return self._halt("HALT_UNKNOWN_EVENT")
        order = update.get("order")
        if not isinstance(order, Mapping):
            raise ValueError("trade update requires an order object")
        order_id = str(order.get("id", "")).strip()
        if not order_id:
            raise ValueError("trade update order requires id")

        quantity = _decimal(order.get("qty"), "order.qty")
        cumulative = _decimal(order.get("filled_qty", "0"), "order.filled_qty")
        if quantity <= 0 or cumulative > quantity:
            self.readback_required = True
            return self._halt("HALT_INCONSISTENT_QUANTITY", order_id)

        if event in FILL_EVENTS:
            key = str(update.get("execution_id", "")).strip()
            if not key:
                self.readback_required = True
                return self._halt("HALT_EXECUTION_ID_MISSING", order_id)
        else:
            key = str(observation_id or "").strip()
            if not key:
                raise ValueError("non-fill events require deterministic observation_id")

        fingerprint = _fingerprint(update)
        state = self.orders.get(order_id)
        if state is None:
            state = OrderState(order_id=order_id, quantity=quantity)
            self.orders[order_id] = state
        elif quantity != state.quantity:
            self.readback_required = True
            return self._halt("HALT_ORDER_QUANTITY_CHANGED", order_id)

        prior_fingerprint = state.seen_observations.get(key)
        if prior_fingerprint is not None:
            if prior_fingerprint == fingerprint:
                return self._result("DUPLICATE_IGNORED", state)
            self.readback_required = True
            return self._halt("HALT_OBSERVATION_ID_CONFLICT", order_id)

        if cumulative < state.filled_quantity:
            self.readback_required = True
            return self._halt("HALT_CUMULATIVE_FILL_REGRESSION", order_id)
        if state.terminal:
            self.readback_required = True
            return self._halt("HALT_EVENT_AFTER_TERMINAL", order_id)
        if event == "partial_fill" and not (state.filled_quantity < cumulative < quantity):
            self.readback_required = True
            return self._halt("HALT_INVALID_PARTIAL_FILL", order_id)
        if event == "fill" and cumulative != quantity:
            self.readback_required = True
            return self._halt("HALT_INCOMPLETE_FILL_EVENT", order_id)

        state.seen_observations[key] = fingerprint
        state.filled_quantity = cumulative
        state.last_event = event
        state.rest_verified = False

        if event in OPERATION_REJECTIONS:
            # The requested operation failed; do not guess the underlying order's
            # current status or future eligibility from the stream message alone.
            self.readback_required = True
            return self._halt("HALT_OPERATION_REJECTED_READBACK_REQUIRED", order_id)

        state.status = event
        state.terminal = event in TERMINAL_EVENTS
        return self._result("APPLIED", state)

    def _result(self, result: str, state: OrderState) -> dict:
        return {"result": result, **self.readiness(), "order": state.as_dict()}

    def _halt(self, result: str, order_id: Optional[str] = None) -> dict:
        payload = {"result": result, **self.readiness()}
        if order_id and order_id in self.orders:
            payload["order"] = self.orders[order_id].as_dict()
        return payload
