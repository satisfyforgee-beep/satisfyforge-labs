"""Out-of-sample *historical simulation*, without training or broker calls.

The fixed strategy is replayed independently on chronological train and test
windows.  No settings are tuned on either set.  Results are diagnostic, not a
forecast; data quality, fees and market coverage still matter greatly.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import timezone
from math import isfinite

from .engine import Bar, PaperEngine, Settings


def _check_data(bars: list[Bar]) -> None:
    if not bars:
        raise ValueError("Historical bars required")
    symbol = bars[0].symbol.upper()
    last = None
    for bar in bars:
        bar.validate()
        if not all(isfinite(v) for v in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError("Non-finite historical price")
        if bar.symbol.upper() != symbol:
            raise ValueError("Use a single instrument per evaluation")
        utc_time = bar.time.astimezone(timezone.utc)
        if last is not None and utc_time <= last:
            raise ValueError("Bars must be chronological and nonduplicated")
        last = utc_time


def _window_report(rows: list[Bar], settings: Settings) -> dict:
    engine = PaperEngine(settings)
    peak = settings.start_cash
    worst_drawdown = 0.0
    for bar in rows:
        engine.on_bar(bar)
        mark = engine.equity
        peak = max(peak, mark)
        worst_drawdown = max(worst_drawdown, (peak - mark) / peak if peak else 0.0)
    engine.finalize()  # Forced exit for a fair window-end comparison
    summary = engine.summary()
    return {
        "start_utc": rows[0].time.astimezone(timezone.utc).isoformat(),
        "end_utc": rows[-1].time.astimezone(timezone.utc).isoformat(),
        "bars": len(rows),
        "strategy": summary,
        "max_mark_to_market_drawdown_pct": round(100 * worst_drawdown, 2),
        "buy_hold_price_change_pct": round(100 * (rows[-1].close / rows[0].open - 1), 2),
        "warning": "Buy-and-hold benchmark is price-only; it excludes spreads and commissions",
    }


def evaluate_holdout(bars: list[Bar], settings: Settings | None = None,
                     *, train_fraction: float = 0.70) -> dict:
    """Chronological split, fresh account per window, no parameter search.

    Minimum usable history is required *within each window*.  This avoids
    feeding future or training-period positions into the holdout portfolio.
    """
    settings = settings or Settings()
    settings.validate()
    if not isfinite(train_fraction) or not 0.3 <= train_fraction <= 0.85:
        raise ValueError("train_fraction must be between 0.30 and 0.85")
    _check_data(bars)
    split = int(len(bars) * train_fraction)
    minimum = settings.min_history_bars + 3
    if split < minimum or len(bars) - split < minimum:
        raise ValueError(f"Need at least {minimum} bars in each split")
    return {
        "mode": "OFFLINE_HISTORICAL_HOLDOUT",
        "paper_only": True,
        "strategy_settings_fixed": asdict(settings),
        "train": _window_report(bars[:split], settings),
        "holdout": _window_report(bars[split:], settings),
        "limitations": [
            "No optimization, guaranteed edge, or future prediction",
            "Price-only buy-and-hold comparator and bar-level simulated fills",
            "Real execution, spreads, market impact and option/crypto behavior are not validated",
            "Synthetic data and a single holdout cannot demonstrate statistical significance",
        ],
    }
