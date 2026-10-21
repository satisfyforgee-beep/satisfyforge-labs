# Market signal evaluation (research only)

This is an **offline evidence tool**, not a price feed, automatic learner, trained model, or trading agent. No order endpoints or API credentials.

CSV input:
- `signals.csv`: `symbol,signal_time,signal_price`
- `bars.csv`: `symbol,time,close`

Both timestamps must be timezone-aware ISO-8601. Example: `2026-10-21T10:00:00-04:00`.

Run from this directory:

```sh
python evaluate_signals.py --signals signals.csv --bars bars.csv --cost-bps 20
python -m unittest -v
```

It computes 15-, 60-, and 390-minute descriptive net returns from the first subsequent bar no later than five minutes after each target. It explicitly marks missing observations as null and subtracts a user-provided round-trip cost estimate. That is **not** a realistic order-fill simulation: selection bias, spreads, halts, volatility, partial fills, bar resolution, overnight gaps and venue fees all require richer data. 390 minutes is a clock-time horizon, not necessarily one trading session.

Next gates before using results for decisions: establish a lawful historical market data source, preserve all scan candidates (not only winners), record source and observation timestamps plus scan parameters, run out-of-sample walk-forward tests including losers and cash opportunity cost, and compare against baseline/no-trade performance. Do not enable live trading or spend on data sources without explicit transaction-specific approval.

SatisfyForge's business automation is separate from the personal trading research. No private brokerage records or credentials should be put in this public repository.
