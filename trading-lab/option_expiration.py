"""Offline, readback-only long-option expiration reconciliation.

This module never connects to a broker and never creates, modifies, or infers an
order.  It journals normalized provider observations only after independent
account, position, and non-trade-activity (NTA) readbacks.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


def _utc(value: datetime | str | None, label: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid {label}") from None
    if not isinstance(value, datetime):
        raise ValueError(f"Invalid {label}")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _decimal(value, label: str, *, signed: bool = False) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{label} must use an exact decimal")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Invalid {label}") from None
    if not parsed.is_finite() or (not signed and parsed < 0):
        raise ValueError(f"Invalid {label}")
    return parsed


@dataclass(frozen=True)
class OptionExpiryTerms:
    symbol: str
    underlying: str
    kind: str
    expiration: date
    quantity: Decimal
    exercise_underlying_delta_per_contract: Decimal
    exercise_cash_delta_per_contract: Decimal

    def __post_init__(self) -> None:
        if (not self.symbol or not self.underlying
                or any(c.isspace() for c in self.symbol + self.underlying)):
            raise ValueError("Option and underlying symbols are required")
        if self.kind not in {"call", "put"}:
            raise ValueError("Long option kind must be call or put")
        quantity = _decimal(self.quantity, "option quantity")
        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError("Option quantity must be a positive whole number")
        underlying_delta = _decimal(
            self.exercise_underlying_delta_per_contract,
            "exercise underlying delta", signed=True)
        cash_delta = _decimal(self.exercise_cash_delta_per_contract,
                              "exercise cash delta", signed=True)
        if underlying_delta == 0:
            raise ValueError("Exercise underlying delta cannot be zero")
        if self.kind == "call" and (underlying_delta <= 0 or cash_delta >= 0):
            raise ValueError("Call exercise must receive underlying and debit cash")
        if self.kind == "put" and (underlying_delta >= 0 or cash_delta <= 0):
            raise ValueError("Put exercise must deliver underlying and credit cash")
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "exercise_underlying_delta_per_contract",
                           underlying_delta)
        object.__setattr__(self, "exercise_cash_delta_per_contract", cash_delta)


@dataclass(frozen=True)
class ExpiryObservation:
    observation_id: str
    as_of: datetime
    account_checked_at: datetime | None
    positions_checked_at: datetime | None
    activity_checked_at: datetime | None
    option_position_quantity: Decimal | None
    underlying_quantity_delta: Decimal | None
    cash_delta: Decimal | None
    cash_before_expiry: Decimal | None
    underlying_before_expiry: Decimal | None
    activities: tuple[dict, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id or self.observation_id.isspace():
            raise ValueError("Stable observation_id required")
        object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        for name in ("account_checked_at", "positions_checked_at",
                     "activity_checked_at"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))
        for name in ("option_position_quantity", "cash_before_expiry",
                     "underlying_before_expiry"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _decimal(value, name))
        for name in ("underlying_quantity_delta", "cash_delta"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _decimal(value, name, signed=True))
        if not isinstance(self.activities, tuple):
            raise ValueError("Activities must be an immutable tuple")


def _activity_at_cutoff(terms: OptionExpiryTerms,
                        observation: ExpiryObservation) -> dict | None:
    unique: dict[str, dict] = {}
    for activity in observation.activities:
        if not isinstance(activity, dict):
            raise ValueError("Malformed option activity")
        activity_id = activity.get("activity_id")
        if not isinstance(activity_id, str) or not activity_id:
            raise ValueError("Option activity_id required")
        prior = unique.get(activity_id)
        if prior is not None:
            if prior != activity:
                raise ValueError("Conflicting duplicate option activity")
            continue
        unique[activity_id] = activity

    eligible = []
    for activity in unique.values():
        observed = _utc(activity.get("observed_at"), "activity observed_at")
        effective = _utc(activity.get("effective_at"), "activity effective_at")
        if effective > observed:
            raise ValueError("Option activity observed before effective time")
        if observed > observation.as_of:
            continue
        if activity.get("symbol") != terms.symbol:
            raise ValueError("Cross-contract option activity")
        if activity.get("kind") not in {"exercise", "expiration"}:
            raise ValueError("Unsupported option activity kind")
        quantity = _decimal(activity.get("quantity"), "activity quantity")
        if quantity != terms.quantity:
            raise ValueError("Option activity quantity mismatch")
        if effective.date() < terms.expiration:
            raise ValueError("Option activity predates expiration")
        normalized = dict(activity)
        normalized["observed_at"] = observed.isoformat()
        normalized["effective_at"] = effective.isoformat()
        normalized["quantity"] = str(quantity)
        eligible.append(normalized)
    if len(eligible) > 1:
        raise ValueError("Ambiguous option expiration activities")
    return eligible[0] if eligible else None


def reconcile_expiration(terms: OptionExpiryTerms,
                         observation: ExpiryObservation) -> dict:
    """Return pending or confirmed state without mutating cash or positions."""
    if observation.as_of.date() <= terms.expiration:
        status, reason = "PENDING_NOT_EXPIRED", "Expiration date has not passed"
        activity = None
    else:
        activity = _activity_at_cutoff(terms, observation)
        checks = (observation.account_checked_at,
                  observation.positions_checked_at,
                  observation.activity_checked_at)
        if any(value is None for value in checks):
            status, reason = ("PENDING_INCOMPLETE_READBACK",
                              "Independent account, position, and activity checks required")
        elif any(value > observation.as_of for value in checks):
            raise ValueError("Readback timestamp is after reconciliation cutoff")
        elif any(value.date() <= terms.expiration for value in checks):
            status, reason = ("PENDING_NEXT_DAY_READBACK",
                              "Same-day readback cannot finalize paper expiration")
        elif activity is None:
            status, reason = ("PENDING_ACTIVITY_READBACK",
                              "No eligible non-trade activity observed by cutoff")
        elif any(value is None for value in (
                observation.option_position_quantity,
                observation.underlying_quantity_delta,
                observation.cash_delta,
                observation.cash_before_expiry,
                observation.underlying_before_expiry)):
            status, reason = ("PENDING_UNKNOWN_ACCOUNT_STATE",
                              "Cash, position, and delta evidence must be complete")
        elif observation.option_position_quantity != 0:
            status, reason = ("PENDING_POSITION_MISMATCH",
                              "Expired option position is still present")
        elif activity["kind"] == "expiration":
            if (observation.underlying_quantity_delta == 0
                    and observation.cash_delta == 0):
                status, reason = ("CONFIRMED_EXPIRED",
                                  "Expiration activity and zero deltas independently match")
            else:
                status, reason = ("PENDING_STATE_MISMATCH",
                                  "Expiration activity conflicts with account deltas")
        else:
            expected_underlying = (
                terms.exercise_underlying_delta_per_contract * terms.quantity)
            expected_cash = terms.exercise_cash_delta_per_contract * terms.quantity
            if expected_cash < 0 and observation.cash_before_expiry < -expected_cash:
                status, reason = ("PENDING_CASH_INSUFFICIENT",
                                  "Pre-expiry cash could not fund observed exercise")
            elif (expected_underlying < 0
                  and observation.underlying_before_expiry < -expected_underlying):
                status, reason = ("PENDING_UNDERLYING_INSUFFICIENT",
                                  "Pre-expiry underlying could not fund put exercise")
            elif (observation.underlying_quantity_delta != expected_underlying
                  or observation.cash_delta != expected_cash):
                status, reason = ("PENDING_STATE_MISMATCH",
                                  "Exercise activity conflicts with account deltas")
            else:
                status, reason = ("CONFIRMED_EXERCISED",
                                  "Exercise activity and independent deltas match")

    return {
        "mode": "OFFLINE_OPTION_EXPIRATION_RECONCILIATION",
        "paper_only": True,
        "observation_id": observation.observation_id,
        "symbol": terms.symbol,
        "as_of_utc": observation.as_of.isoformat(),
        "status": status,
        "reason": reason,
        "activity_id": activity["activity_id"] if activity else None,
        "final": status.startswith("CONFIRMED_"),
        "warning": "Audit only; no fill, order, balance, or position mutation.",
    }


class OptionExpiryJournal:
    """Atomically persist idempotent reconciliation observations."""

    def __init__(self, database: Path):
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS option_expiry_reconciliations (
                observation_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                as_of_utc TEXT NOT NULL, symbol TEXT NOT NULL, status TEXT NOT NULL,
                reason TEXT NOT NULL, activity_id TEXT, final INTEGER NOT NULL
            )""")

    def record(self, terms: OptionExpiryTerms,
               observation: ExpiryObservation) -> dict:
        result = reconcile_expiration(terms, observation)
        canonical = {"terms": asdict(terms), "observation": asdict(observation)}
        payload = json.dumps(canonical, sort_keys=True, default=str)
        fingerprint = hashlib.sha256(payload.encode()).hexdigest()
        with sqlite3.connect(self.database, timeout=10) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute(
                "SELECT * FROM option_expiry_reconciliations WHERE observation_id=?",
                (observation.observation_id,)).fetchone()
            if prior:
                if prior["fingerprint"] != fingerprint:
                    raise ValueError("Observation ID reused for different evidence")
                return dict(prior)
            conn.execute("""INSERT INTO option_expiry_reconciliations
                (observation_id, fingerprint, as_of_utc, symbol, status, reason,
                 activity_id, final) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (observation.observation_id, fingerprint, result["as_of_utc"],
                 result["symbol"], result["status"], result["reason"],
                 result["activity_id"], int(result["final"])))
            return dict(conn.execute(
                "SELECT * FROM option_expiry_reconciliations WHERE observation_id=?",
                (observation.observation_id,)).fetchone())

    def records(self) -> list[dict]:
        with sqlite3.connect(self.database) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(
                "SELECT * FROM option_expiry_reconciliations "
                "ORDER BY as_of_utc, observation_id")]
