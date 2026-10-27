# SatisfyForge Trading Lab — isolated paper execution v0.1

This is an **offline simulation component**, not a broker integration, strategy,
predictor, live scanner or claim of profitability. It deliberately has **no
network calls and no production trading entrypoint**. All quotes are caller-
supplied; the included demo uses fictional symbols and synthetic values.

## What is implemented

- Stocks, long standard 100-share options, and crypto (fractional crypto only).
- Conservative immediate-limit simulation: buy at ask, sell-to-close at bid.
- Cash-only buying power, worst-case exposure/daily-loss caps, order-cost caps,
  quote age, delay and spread rejection, with no naked shorting or margin.
- Stable client-order IDs with SQLite transactional duplicate protection,
  position cost basis including modeled option fees, realized P&L, and a journal.
- A descriptive paper-only performance summary (not a signal or strategy edge).
- Exact decimal accounting and UTC timestamps; no dependencies beyond Python.
- Fail-closed: a limit that cannot fill **is not queued** for later execution.

## Run the synthetic smoke demo

```bash
python trading-lab/demo.py --database /tmp/satisfyforge-synthetic-paper.sqlite3
python -m unittest discover -s trading-lab -p 'test_*.py' -v
```

Rerunning against the same database does not place duplicate paper orders.
The demo's starting balance and policies are testing values, **not** your live
account figures or standing trading limits.

## Important boundaries and roadmap

1. No broker API keys in this public GitHub repository or test logs. Future
   sandbox adapters must use separate secret storage, verified account identity
   and an explicit paper-mode credential allowlist. Never fall back to live.
2. Tradier sandbox data is 15 minutes delayed; those quotes fail this engine's
   immediate-entry freshness policy by design. Paper *order API* testing can be
   done separately from time-sensitive market-signal evaluation.
3. Historical/live quote feeds, actual event-driven monitoring, option contract
   metadata (especially adjusted multipliers), corporate actions, exchange
   calendars, fills/partial fills, real fee schedules, slippage and assignment
   risk are **not** implemented. Never infer deployability from passing tests.
4. Next: historical data ingestion with provenance, regime-aware backtesting,
   out-of-sample evaluation, statistical performance reporting and controlled
   broker adapter contract tests. Only then consider approved live execution.
