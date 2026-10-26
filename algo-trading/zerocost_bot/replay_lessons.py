"""Fail-closed review of SHORT crypto historical replay: no broker authorization.

Never mutate strategy parameters based on one holdout; doing so overfits.
The module records why a strategy failed to beat doing nothing.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation


def _d(x):
    try:
        v = Decimal(str(x))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError("invalid backtest number") from None
    if not v.is_finite():
        raise ValueError("non-finite backtest number")
    return v


def review_crypto_trial(report):
    if (not isinstance(report, dict) or
            report.get("mode") != "HISTORICAL_OFFLINE_REPLAY_NO_BROKER_ORDERS" or
            report.get("source") != "KRAKEN_PUBLIC_OHLC_15MIN_LAST_CANDLE_EXCLUDED" or
            report.get("paper_broker_orders_sent") != 0 or
            report.get("live_money_orders_sent") != 0):
        raise ValueError("report is not a verified-format historical experiment")
    strategies = report.get("results")
    if not isinstance(strategies, dict) or set(strategies) != {
        "control", "breakout", "reversal"
    }:
        raise ValueError("missing precommitted comparator")
    controls = {}
    for name, runs in strategies.items():
        if not isinstance(runs, dict) or set(runs) != {"development", "holdout"}:
            raise ValueError("incomplete partition")
        for stage in ("development", "holdout"):
            x = runs[stage]
            if not isinstance(x, dict) or x.get("strategy") != name:
                raise ValueError("invalid strategy identity")
            closes = x.get("virtual_closes")
            if type(closes) is not int or closes < 0 or closes != x.get("wins", 0) + x.get("losses_or_flats", 0):
                raise ValueError("inconsistent closes")
            for k in ("net_pnl_after_estimated_costs", "estimated_fees",
                      "max_drawdown_pct", "return_pct"):
                _d(x[k])
        test = runs["holdout"]
        pnl = _d(test["net_pnl_after_estimated_costs"])
        fees = _d(test["estimated_fees"])
        if fees < 0:
            raise ValueError("invalid costs")
        reasons = []
        if test["virtual_closes"] < 30:
            reasons.append("INSUFFICIENT_HOLDOUT_SAMPLE_30_TRADES")
        if pnl <= 0:
            reasons.append("NONPOSITIVE_HOLDOUT_NET_PNL")
        if pnl + fees > 0 and pnl <= 0:
            reasons.append("ESTIMATED_FEES_ERASE_GROSS_EDGE")
        if _d(test["max_drawdown_pct"]) > 3:
            reasons.append("HOLDOUT_DRAWDOWN_ABOVE_3PCT")
        controls[name] = {
            "research_grade": "REJECT" if reasons else "NEEDS_MORE_FORWARD_DATA",
            "why": reasons,
            "virtual_holdout_trades": test["virtual_closes"],
            "virtual_net_after_costs": str(pnl),
            "estimated_fees": str(fees),
            "not_a_trade_recommendation": True,
        }
    return {
        "mode": "POSTMORTEM_NO_ORDERS_OR_AUTONOMOUS_OPTIMIZATION",
        "outcome": "NO_STRATEGY_READY_FOR_PAPER_BROKER_EXECUTION",
        "broker_paper_execution_authorized": False,
        "live_money_execution_authorized": False,
        "strategies": controls,
        "next_valid_experiments": [
            "Run longer independent out-of-sample periods; do not tune on this holdout.",
            "Collect genuine forward fills/market prices and realistic fees/spreads.",
            "Compare new precommitted rules to cash/no-trade and passive baselines.",
            "Track failed signals, session gaps, max drawdown and trade count.",
        ],
    }
