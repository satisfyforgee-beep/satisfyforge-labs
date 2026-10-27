# SatisfyForge Trading Lab — offline signal-to-ledger v0.2

This is an **offline simulation component**, not a broker integration, strategy,
predictor, live scanner or claim of profitability. It deliberately has **no
network calls and no production trading entrypoint**. All quotes are caller-
supplied; the included demo uses fictional symbols and synthetic values.

The companion `../algo-trading/` code contains the historical OHLCV breakout
strategy, a read-only IEX data adapter, and an **unarmed** Alpaca paper broker
adapter. `pipeline.py` now imports the broker-free breakout decision and routes
one equity candidate into this SQLite ledger only. The separately gated Alpaca
adapter is NOT connected to the unified ledger and must remain disabled; only
the SQLite ledger owns the integrated simulated fills.

## What is implemented

- Stocks, long standard 100-share options, and crypto (fractional crypto only).
- Conservative immediate-limit simulation: buy at ask, sell-to-close at bid.
- Cash-only buying power, worst-case exposure/daily-loss caps, order-cost caps,
  quote age, delay and spread rejection, with no naked shorting or margin.
- Stable client-order IDs with SQLite transactional duplicate protection,
  position cost basis including modeled option fees, realized P&L, and a journal.
- End-to-end **equity-only signal handoff** from chronological completed-minute
  OHLCV bars, with deterministic signal IDs and persisted market quote provenance.
- Automatic safe migration of pre-v0.2 SQLite order journals without losing rows.
- Emergency skip switch: `SF_TRADING_PAUSED=1` on the one-shot signal evaluator.
- A descriptive paper-only performance summary (not a signal or strategy edge).
- Exact decimal accounting and UTC timestamps; no dependencies beyond Python.
- Fail-closed: a limit that cannot fill **is not queued** for later execution.

## Run the synthetic smoke demo

```bash
python trading-lab/demo.py --database /tmp/satisfyforge-synthetic-paper.sqlite3
python trading-lab/integrated_demo.py --database /tmp/sf-integrated-fictional.sqlite3
python -m unittest discover -s trading-lab -p 'test_*.py' -v
```

Rerunning the integrated demo against the same database does not create a
duplicate paper order; it uses one fictional bar/quote set and stable signal ID.
The demo's starting balance and policies are testing values, **not** your live
account figures or standing trading limits.

## One-shot unified signal evaluation (no broker)

From Python, instantiate `PaperEngine` with your synthetic journal path,
`RiskPolicy` and starting cash; pass **chronological, completed, one-minute**
`zerocost_bot.engine.Bar` objects plus a `Quote` and UTC evaluation time to
`pipeline.evaluate_equity_breakout(journal, bars, quote, now)`. The helper
checks that the signal is recent and quote timestamp follows bar close,
calculates a capped whole-share quantity, and records one simulated limit
attempt with a stable signal/client ID. The order is never sent to a broker.

`pipeline.safety_readiness()` reports capability flags and whether data-feed
environment variables are present; it never prints credential values.

The current adapter only automates **underlying equities**. Options and crypto
are available in the *offline manual/synthetic order ledger* but do not have
validated option-chain or exchange-price signal-to-order adapters. This is a
deliberate safety boundary, not a claim that those asset classes are ignored.

## Important boundaries and roadmap

1. No broker API keys in this public GitHub repository or test logs. Future
   sandbox adapters must use separate secret storage, verified account identity
   and an explicit paper-mode credential allowlist. Never fall back to live.
2. Tradier sandbox data is 15 minutes delayed; those quotes fail this engine's
   immediate-entry freshness policy by design. Paper *order API* testing can be
   done separately from time-sensitive market-signal evaluation.
3. Authenticated IEX quotes are read-only and single-venue, not a whole-market
   consolidated quote. Until actual authorized credentials and data are verified,
   no current feed is connected to this signal handoff.
4. Historical/live quote feeds, actual event-driven monitoring, option contract
   metadata (especially adjusted multipliers), corporate actions, exchange
   calendars, fills/partial fills, real fee schedules, slippage and assignment
   risk are **not** implemented. Never infer deployability from passing tests.
5. Historical holdout evaluation is available in `../algo-trading/evaluate.py`.
   Next are sourced data validation, multi-session comparisons, proper open
   position exits, realistic option/crypto contracts, independent statistical
   evidence, and approved multi-week paper-forward evaluation before any live
   deployment discussion.
