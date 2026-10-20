"""Independent, deterministic evidence reviewers for a zero-subscription trading lab.

'Agents' here are lightweight algorithmic reviewers, NOT paid LLMs or forecasts.
All evidence is calculated from COMPLETED bars. This module never sends orders.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Optional, Sequence
from .engine import Bar


@dataclass(frozen=True)
class Snapshot:
    symbol: str
    bars: Sequence[Bar]
    bid: float
    ask: float
    quote_at: datetime
    evaluated_at: datetime
    benchmark: Optional[Sequence[Bar]] = None


@dataclass(frozen=True)
class Vote:
    agent: str
    verdict: str  # support, oppose, abstain, veto
    detail: str


@dataclass(frozen=True)
class Decision:
    symbol: str
    action: str  # candidate or pass
    votes: tuple[Vote, ...]
    support_count: int
    observed_at: str
    entry_reference: Optional[float] = None

    def as_report(self):
        return {
            "symbol": self.symbol, "action": self.action,
            "supports": self.support_count, "entry_reference": self.entry_reference,
            "observed_at": self.observed_at,
            "votes": [v.__dict__ for v in self.votes],
            "warning": "A vote count is NOT a probability of profit. No order submitted.",
        }


def _ema(values, length):
    weight = 2 / (length + 1)
    result = values[0]
    for val in values[1:]:
        result = weight * val + (1 - weight) * result
    return result


class ConsensusEngine:
    """Require independent confirmation; reject stale, inconsistent inputs."""

    def __init__(self, required_support=4, max_quote_age_seconds=5,
                 max_spread_fraction=.003, max_one_bar_move=.04,
                 max_bar_age_seconds=150):
        if not 3 <= required_support <= 5:
            raise ValueError("invalid quorum")
        self.required_support = required_support
        self.max_quote_age_seconds = max_quote_age_seconds
        self.max_spread_fraction = max_spread_fraction
        self.max_one_bar_move = max_one_bar_move
        self.max_bar_age_seconds = max_bar_age_seconds

    def assess(self, snap: Snapshot) -> Decision:
        now = snap.evaluated_at
        if now.tzinfo is None or snap.quote_at.tzinfo is None:
            raise ValueError("timezone-aware timestamps required")
        now = now.astimezone(timezone.utc)
        symbol = snap.symbol.upper()
        votes = []
        def add(name, verdict, why):
            votes.append(Vote(name, verdict, why))
        def stop(why):
            add("data_integrity", "veto", why)
            return Decision(symbol, "pass", tuple(votes), 0, now.isoformat())

        if (not symbol or not symbol.isascii() or
                not symbol.replace(".", "").isalpha() or len(symbol) > 6):
            return stop("invalid equity symbol")
        if len(snap.bars) < 20:
            return stop("fewer than 20 completed bars")
        for b in snap.bars:
            if not all(isfinite(v) for v in (b.open, b.high, b.low, b.close)):
                return stop("non-finite bar price")
            try:
                b.validate()
            except ValueError as err:
                return stop(str(err))
            if b.symbol.upper() != symbol:
                return stop("bar symbol mismatch")
        if any(a.time >= b.time for a, b in zip(snap.bars, snap.bars[1:])):
            return stop("non-monotonic or duplicate bars")
        last = snap.bars[-1]
        # Bars in this feed are timestamped at their BEGINNING.
        if now < last.time.astimezone(timezone.utc) + timedelta(minutes=1):
            return stop("latest minute bar is not complete")
        if (now - last.time.astimezone(timezone.utc)).total_seconds() > self.max_bar_age_seconds:
            return stop("completed bar is stale")
        quote_age = (now - snap.quote_at.astimezone(timezone.utc)).total_seconds()
        if not (0 <= quote_age <= self.max_quote_age_seconds):
            return stop("quote stale or timestamp in future")
        if (not all(isfinite(v) for v in [snap.bid, snap.ask])
                or snap.bid <= 0 or snap.ask < snap.bid):
            return stop("bad or crossed quote")
        mid = (snap.bid + snap.ask) / 2
        spread = (snap.ask - snap.bid) / mid
        add("liquidity", "support" if spread <= self.max_spread_fraction else "veto",
            f"relative spread {spread:.3%}; maximum {self.max_spread_fraction:.3%}")
        if spread > self.max_spread_fraction:
            return Decision(symbol, "pass", tuple(votes), 0, now.isoformat())
        history = snap.bars[:-1]
        closes = [b.close for b in history]
        trend = _ema(closes[-16:] + [last.close], 5) > _ema(closes[-20:] + [last.close], 13)
        add("trend", "support" if trend else "oppose", "EMA5 above EMA13" if trend else "trend not confirmed")
        recent_high = max(b.high for b in history[-8:])
        breakout = last.close > recent_high * 1.0005
        add("breakout", "support" if breakout else "oppose", f"close {last.close:.4f} vs 8-bar high {recent_high:.4f}")
        mean_volume = sum(b.volume for b in history[-10:]) / 10
        vol_ok = last.volume >= 5000 and mean_volume > 0 and last.volume / mean_volume >= 1.25
        add("volume", "support" if vol_ok else "oppose",
            f"current volume {last.volume}; 10-bar mean {mean_volume:.0f}")
        one_bar_move = abs(last.close / history[-1].close - 1)
        if one_bar_move > self.max_one_bar_move:
            add("volatility", "veto", f"one-bar change {one_bar_move:.2%} too large")
        else:
            add("volatility", "support", f"one-bar change {one_bar_move:.2%}")
        if snap.benchmark is not None:
            if len(snap.benchmark) < 6 or any(
                b.time.tzinfo is None for b in snap.benchmark
            ):
                add("market_regime", "veto", "benchmark bars unavailable/incomplete")
            else:
                bm = snap.benchmark
                if (bm[-1].time < last.time - timedelta(minutes=2)
                        or bm[-1].time > last.time + timedelta(minutes=1)
                        or any(not isfinite(b.close) or b.close <= 0 for b in bm[-6:])):
                    add("market_regime", "veto", "stale or invalid benchmark")
                else:
                    change = bm[-1].close / bm[-6].close - 1
                    add("market_regime", "veto" if change <= -.005 else "support",
                        f"benchmark 5-bar return {change:.2%}")
        supports = sum(v.verdict == "support" for v in votes)
        veto = any(v.verdict == "veto" for v in votes)
        alpha_required = {"trend", "breakout", "volume"}
        alpha_confirmed = all(v.verdict == "support" for v in votes if v.agent in alpha_required)
        action = "candidate" if supports >= self.required_support and not veto and alpha_confirmed else "pass"
        return Decision(symbol, action, tuple(votes), supports,
                        now.isoformat(), round(snap.ask, 4) if action == "candidate" else None)
