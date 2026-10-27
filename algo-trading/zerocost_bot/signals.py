"""Pure, broker-free signal functions shared by replay and paper evaluation."""
from __future__ import annotations

from math import isfinite

from .engine import Bar, PaperEngine, Settings


def choose_signal(bars: list[Bar]) -> Bar | None:
    """Return a breakout on the latest completed bar, never an order.

    The caller is responsible for confirming that its last bar has closed.
    Invalid, unsorted, duplicate or mixed-symbol history is rejected.
    """
    if len(bars) < 15:
        return None
    first_symbol = bars[0].symbol.upper()
    previous_time = None
    for bar in bars:
        bar.validate()
        if not all(isfinite(value) for value in (bar.open, bar.high, bar.low, bar.close)):
            raise ValueError("Non-finite price in historical bars")
        if bar.symbol.upper() != first_symbol:
            raise ValueError("Signal input must contain only one symbol")
        if previous_time is not None and bar.time <= previous_time:
            raise ValueError("Bars must be unique and strictly time-ordered")
        previous_time = bar.time

    current = bars[-1]
    engine = PaperEngine(Settings())
    for bar in bars[-14:-1]:
        engine.on_bar(bar)
    return current if engine._signal(current.symbol.upper(), current) else None
