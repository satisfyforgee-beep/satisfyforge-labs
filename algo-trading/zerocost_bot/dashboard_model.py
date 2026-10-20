"""Sanitized, fail-closed view model for the private SatisfyForge dashboard.

This module is READ ONLY. It does not import any broker or execution clients.
All performance is explicitly UNVERIFIED until a separate verified trade ledger
exists; a synthetic example can never become a live result.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re


_SOURCES = {
    "alpaca_iex", "tradier_live", "tradier_sandbox",
    "alpaca_options_indicative", "kraken_public",
}
_ASSETS = {"stock", "option", "crypto"}
_STATUSES = {"DATA_READY", "RESEARCH_ONLY", "BLOCKED"}
_COVERAGE = {"consolidated", "single_venue", "indicative", "delayed"}
_SYMBOL = re.compile(r"^[A-Z0-9./]{1,30}$")
_MAX_BYTES = 262144
_MAX_AGE_SECONDS = 15

_COMPONENTS = [
    {
        "name": "Technical analysis",
        "description": "Trend, breakout, volume and volatility reviewers",
        "state": "IMPLEMENTED_OFFLINE",
    },
    {
        "name": "News / catalyst AI",
        "description": "Not connected to a licensed or validated news feed",
        "state": "NOT_CONNECTED",
    },
    {
        "name": "Local AI advisers",
        "description": "Optional Ollama research roles; no model running",
        "state": "OPTIONAL_NOT_RUNNING",
    },
    {
        "name": "Execution / exit engine",
        "description": "Paper-only adapter guarded; no hosted trading service",
        "state": "DISABLED",
    },
    {
        "name": "Risk controller",
        "description": "Offline checks for spend, losses and duplicate orders",
        "state": "IMPLEMENTED_OFFLINE",
    },
]


def _utcnow():
    return datetime.now(timezone.utc)


def _time(raw):
    if not isinstance(raw, str) or len(raw) > 70:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None:
            return None
        return value.astimezone(timezone.utc)
    except (ValueError, OverflowError, TypeError):
        return None


def _finite_float(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def _read_report(path):
    """Read only a consciously supplied local report, never .env or credentials."""
    if path is None:
        return None, "No market-data report configured"
    try:
        p = Path(path)
        if not p.is_file() or p.stat().st_size > _MAX_BYTES:
            return None, "Report missing or oversized"
        with p.open("rb") as file:
            raw = file.read(_MAX_BYTES + 1)
        if len(raw) > _MAX_BYTES:
            return None, "Report too large"
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            return None, "Unexpected report format"
        return obj, None
    except (OSError, ValueError, TypeError, UnicodeError):
        return None, "Unable to read or parse report"


def build_snapshot(report_path=None, now=None):
    """Never present synthetic/stale prices as executable quotes.

    Returns only allowlisted fields. Raw market files, account identifiers,
    user information and any extra JSON keys are never emitted.
    """
    now = now or _utcnow()
    if now.tzinfo is None:
        raise ValueError("timezone-aware clock required")
    now = now.astimezone(timezone.utc)
    report, error = _read_report(report_path)
    asof = _time(report.get("at_utc")) if report else None
    mode = report.get("mode") if report else None
    valid_mode = mode in ("READ_ONLY_RESEARCH", "SYNTHETIC_TEST_ONLY")
    age = (now - asof).total_seconds() if asof else None
    valid_age = (age is not None and 0 <= age <= _MAX_AGE_SECONDS)
    synthetic = mode == "SYNTHETIC_TEST_ONLY"
    market_status = (
        "NO_FEED" if error else
        "INVALID" if not valid_mode or not asof or age is None or age < 0 else
        "STALE" if not valid_age else
        "SYNTHETIC" if synthetic else "READ_ONLY"
    )
    reports = []
    if report and valid_mode and isinstance(report.get("reports"), list):
        for item in report["reports"][:30]:
            if not isinstance(item, dict):
                continue
            if (item.get("source") not in _SOURCES or
                    item.get("asset") not in _ASSETS or
                    item.get("status") not in _STATUSES or
                    item.get("coverage") not in _COVERAGE):
                continue
            symbol = item.get("symbol")
            if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol):
                continue
            bid, ask = _finite_float(item.get("bid")), _finite_float(item.get("ask"))
            if bid is None or ask is None or bid <= 0 or ask < bid:
                continue
            reports.append({
                "symbol": symbol, "asset": item["asset"],
                "source": item["source"], "coverage": item["coverage"],
                "bid": round(bid, 8), "ask": round(ask, 8),
                "data_status": item["status"] if valid_age and not synthetic else
                               ("SYNTHETIC" if synthetic else "STALE"),
                "live_order_authorized": False,
            })
    return {
        "schema_version": 1,
        "name": "SatisfyForge Trading Lab",
        "generated_at_utc": now.isoformat(),
        "market": {
            "status": market_status, "data_asof_utc": asof.isoformat() if asof else None,
            "age_seconds": round(age, 2) if age is not None and age >= 0 else None,
            "is_synthetic": synthetic,
            "quotes": reports,
            "source_status": (
                "No feed connected" if error else
                "Invalid report metadata" if market_status == "INVALID" else
                "Prices are not current" if market_status == "STALE" else
                "Synthetic prices only" if synthetic else
                "Read-only quotes, not brokerage execution"
            ),
        },
        "execution": {
            "live_enabled": False,
            "paper_enabled": False,
            "broker_connected": False,
            "background_runner_running": False,
            "orders_submitted_by_dashboard": 0,
        },
        "performance": {
            "validated_trade_count": 0,
            "verified_net_pnl": None,
            "verified_win_rate_pct": None,
            "status": "NO_VERIFIED_FORWARD_TRADES",
        },
        "components": [dict(c) for c in _COMPONENTS],
        "notice": (
            "Private, read-only research dashboard. No live order controls, "
            "broker credentials, or proven strategy returns."
        ),
    }
