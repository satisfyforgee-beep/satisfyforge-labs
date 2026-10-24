"""Fail-closed SANDBOX read-only reconciliation supervisor.

This code never posts, modifies or cancels an order. A clean heartbeat means
the program is running, NOT that the trading strategy is profitable. An
uncertain broker response permanently HALTS the run; no automatic restarts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
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
_ZERO_HASH = "0" * 64
_JOURNAL_LIMIT = 8 * 1024 * 1024
_SAFE_NOTES = frozenset((
    "Unsafe or incomplete order/exit linkage; manual brokerage check required",
    "Simulated order lifecycle ended; stop polling this order",
    "Verified read-only sandbox status; no orders allowed",
    "Broker data unavailable, invalid or inconsistent; do not automatically retry",
    "Owner stopped the read-only monitor",
))


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


def _journal_event(report: SupervisorReport):
    """Return a strictly allowlisted event; raw broker responses are impossible."""
    event = report.as_dict()
    if event.get("reason") not in _SAFE_NOTES:
        raise ValueError("journal reason is not sanitized")
    if event.get("environment") != "TRADIER_SANDBOX_ONLY":
        raise ValueError("journal environment mismatch")
    if event.get("paper_order_submission_enabled") is not False:
        raise ValueError("paper order writes must remain disabled")
    if event.get("live_order_enabled") is not False or event.get("can_trade") is not False:
        raise ValueError("journal cannot record an enabled trading state")
    if event.get("schema_version") != 1:
        raise ValueError("journal schema version invalid")
    if event.get("supervisor_state") not in {"MONITORING", "HALTED", "STOPPED"}:
        raise ValueError("journal supervisor state invalid")
    if event.get("brokerage_state") not in _BROKER_STATES | {"UNKNOWN"}:
        raise ValueError("journal brokerage state invalid")
    errors = event.get("consecutive_errors")
    if type(errors) is not int or errors not in (0, 1):
        raise ValueError("journal error count invalid")
    checked = event.get("checked_at_utc")
    try:
        stamp = datetime.fromisoformat(checked)
    except (TypeError, ValueError):
        raise ValueError("journal timestamp invalid") from None
    if stamp.tzinfo is None:
        raise ValueError("journal timestamp must include timezone")
    return event


def _record_hash(previous_hash, event):
    canonical = json.dumps(event, allow_nan=False, sort_keys=True,
                           separators=(",", ":"))
    return hashlib.sha256((previous_hash + "\n" + canonical).encode("utf-8")
                          ).hexdigest()


def _validate_journal_bytes(raw):
    """Validate every record and hash link before trusting or extending a log."""
    if len(raw) > _JOURNAL_LIMIT:
        raise ValueError("private journal exceeds bounded size")
    if raw and not raw.endswith(b"\n"):
        raise ValueError("private journal has a truncated final record")
    previous = _ZERO_HASH
    count = 0
    for line in raw.splitlines():
        if not line or len(line) > 8192:
            raise ValueError("private journal record malformed")
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("private journal is not valid JSON lines") from None
        if not isinstance(row, dict) or set(row) != {
                "sequence", "previous_hash", "event", "event_hash"}:
            raise ValueError("private journal record schema mismatch")
        count += 1
        if row.get("sequence") != count or row.get("previous_hash") != previous:
            raise ValueError("private journal sequence or chain mismatch")
        event = row.get("event")
        if not isinstance(event, dict):
            raise ValueError("private journal event missing")
        report = SupervisorReport(
            event.get("supervisor_state"), event.get("brokerage_state"),
            event.get("reason"), event.get("checked_at_utc"),
            event.get("consecutive_errors"),
        )
        if _journal_event(report) != event:
            raise ValueError("private journal event schema mismatch")
        expected = _record_hash(previous, event)
        if row.get("event_hash") != expected:
            raise ValueError("private journal hash mismatch")
        previous = expected
    return count, previous


def _open_private_journal(root, flags):
    target = root / "paper_order_journal.jsonl"
    if target.is_symlink():
        raise ValueError("refuse symlinked journal destination")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(target), flags | nofollow, 0o600)
    except OSError:
        raise ValueError("unable to open private journal safely") from None
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise ValueError("private journal must be one regular file")
    os.fchmod(fd, 0o600)
    return fd, target


def append_private_journal(report: SupervisorReport, *, directory: Path):
    """Append one fsynced, hash-linked, mode-0600 sanitized lifecycle event."""
    if not isinstance(report, SupervisorReport):
        raise ValueError("only sanitized supervisor reports may be journaled")
    event = _journal_event(report)
    root = Path(directory)
    _trusted_dir(root)
    fd, target = _open_private_journal(root, os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.lseek(fd, 0, os.SEEK_SET)
        raw = b""
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            raw += chunk
            if len(raw) > _JOURNAL_LIMIT:
                raise ValueError("private journal exceeds bounded size")
        count, previous = _validate_journal_bytes(raw)
        digest = _record_hash(previous, event)
        record = {
            "sequence": count + 1,
            "previous_hash": previous,
            "event": event,
            "event_hash": digest,
        }
        payload = (json.dumps(record, allow_nan=False, sort_keys=True,
                              separators=(",", ":")) + "\n").encode("utf-8")
        if len(payload) > 8192 or len(raw) + len(payload) > _JOURNAL_LIMIT:
            raise ValueError("private journal append exceeds bounded size")
        os.lseek(fd, 0, os.SEEK_END)
        pending = memoryview(payload)
        while pending:
            written = os.write(fd, pending)
            if written <= 0:
                raise ValueError("private journal append was incomplete")
            pending = pending[written:]
        os.fsync(fd)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    return target


def verify_private_journal(*, directory: Path):
    """Read-only integrity check returning only count and tail hash."""
    root = Path(directory)
    _trusted_dir(root)
    target = root / "paper_order_journal.jsonl"
    if target.is_symlink():
        raise ValueError("refuse symlinked journal destination")
    if not target.exists():
        return {"entries": 0, "tail_hash": _ZERO_HASH, "valid": True}
    fd, _ = _open_private_journal(root, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_SH)
        raw = b""
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            raw += chunk
            if len(raw) > _JOURNAL_LIMIT:
                raise ValueError("private journal exceeds bounded size")
        count, tail = _validate_journal_bytes(raw)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    return {"entries": count, "tail_hash": tail, "valid": True}
