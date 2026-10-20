"""Fail-closed SANDBOX read-only reconciliation supervisor.

This code never posts, modifies or cancels an order. A clean heartbeat means
the program is running, NOT that the trading strategy is profitable. An
uncertain broker response permanently HALTS the run; no automatic restarts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Callable

from .tradier_paper import BrokerUncertain, PaperBlocked

_BROKER_STATES = frozenset((
    "AWAITING_ENTRY", "ENTRY_NOT_FILLED", "HALT_AND_RECONCILE",
    "PROTECTED_PAPER_POSITION", "CLOSED_PAPER_POSITION",
))
_HEALTHY = {"AWAITING_ENTRY", "PROTECTED_PAPER_POSITION"}
_COMPLETED = {"ENTRY_NOT_FILLED", "CLOSED_PAPER_POSITION"}


@dataclass(frozen=True)
class SupervisorReport:
    """All reports explicitly label simulation and disable order writes."""
    state: str
    brokerage_state: str
    note: str
    checked_at_utc: str
    consecutive_errors: int = 0

    def as_dict(self):
        return {
            "schema_version": 1,
            "environment": "TRADIER_SANDBOX_ONLY",
            "supervisor_state": self.state,
            "brokerage_state": self.brokerage_state,
            "reason": self.note,
            "checked_at_utc": self.checked_at_utc,
            "consecutive_errors": self.consecutive_errors,
            "paper_order_submission_enabled": False,
            "live_order_enabled": False,
            "can_trade": False,
        }


class PaperSupervisor:
    """One-shot poller/finite local watcher; treats unknown as halt."""

    def __init__(self, read_broker: Callable[[], dict],
                 clock: Callable[[], datetime] | None = None):
        if not callable(read_broker):
            raise TypeError("read-only broker function required")
        self._read = read_broker
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._halt = False
        self._completed = False
        self._last = None

    @property
    def halted(self):
        return self._halt

    def poll(self):
        if self._halt or self._completed:
            raise RuntimeError("supervisor has ended; do not silently restart")
        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None:
            self._halt = True
            raise ValueError("timezone-aware system clock required")
        stamped = now.astimezone(timezone.utc).isoformat()
        try:
            response = self._read()
            if not isinstance(response, dict) or response.get(
                    "environment") != "TRADIER_SANDBOX_ONLY":
                raise BrokerUncertain("unexpected broker mode")
            state = response.get("readiness")
            if state not in _BROKER_STATES:
                raise BrokerUncertain("unrecognized broker readiness")
            if response.get("live_order_enabled") is not False:
                raise BrokerUncertain("live execution was not explicitly disabled")
            if response.get("order_action") != "DO_NOT_TRADE":
                raise BrokerUncertain("unexpected order action")
            if state == "HALT_AND_RECONCILE":
                self._halt = True
                self._last = SupervisorReport(
                    "HALTED", state,
                    "Unsafe or incomplete order/exit linkage; manual brokerage check required",
                    stamped, 1)
            elif state in _COMPLETED:
                self._completed = True
                self._last = SupervisorReport(
                    "STOPPED", state,
                    "Simulated order lifecycle ended; stop polling this order",
                    stamped)
            else:
                self._last = SupervisorReport(
                    "MONITORING", state,
                    "Verified read-only sandbox status; no orders allowed",
                    stamped)
        except Exception:
            # Broker adapters and future plugins may raise new error types.
            # Always fail CLOSED and never expose raw error text or account
            # fields through the local dashboard or console. KeyboardInterrupt
            # is BaseException and remains a direct owner stop.
            self._halt = True
            self._last = SupervisorReport(
                "HALTED", "UNKNOWN",
                "Broker data unavailable, invalid or inconsistent; do not automatically retry",
                stamped, 1)
        return self._last


def _trusted_dir(directory: Path):
    """No symlink directories: prevent accidental writes to arbitrary paths."""
    if directory.is_symlink():
        raise ValueError("status directory must not be a symlink")
    if not directory.exists():
        directory.mkdir(mode=0o700, parents=True)
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("invalid status directory")
    try:
        current = directory.stat().st_mode
        if current & (stat.S_IRWXG | stat.S_IRWXO):
            directory.chmod(0o700)
    except OSError:
        raise ValueError("unable to protect private status directory") from None


def write_private_report(report: SupervisorReport, *, directory: Path):
    """Atomic, mode-0600 local write. Cannot be published through GitHub."""
    if not isinstance(report, SupervisorReport):
        raise ValueError("only sanitized supervisor reports may be saved")
    root = Path(directory)
    _trusted_dir(root)
    target = root / "paper_order_status.json"
    if target.is_symlink():
        raise ValueError("refuse symlinked status destination")
    payload = json.dumps(report.as_dict(), allow_nan=False,
                         sort_keys=True).encode("utf-8")
    # Constant-sized/allowlisted schema ensures private brokerage metadata
    # can never be exported by accidentally serializing a raw API response.
    if len(payload) > 4096:
        raise ValueError("status payload abnormally large")
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=".sf-paper-", dir=str(root))
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return target
