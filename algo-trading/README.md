# SatisfyForge zero-subscription trading lab (paper-only)

**Current status: v0.1 tested research prototype, no connected broker, no persistent
runner, no live-money trading, no profit claim.** This project is not investment advice.
A guarded paper-broker adapter is implemented but has NOT been authenticated or used
to submit even simulated broker orders.

This implementation is original standard-library Python: its inspiration is
the published architectural patterns of event-driven trading frameworks, not
copied proprietary StockHero/Trade Ideas/Option Alpha AI code.

## Why this broker/data stack?
- **Alpaca** supports free paper brokerage accounts and free IEX equity data
  with partial venue coverage, plus documented paper-order and bracket-order
  APIs for a later stage. Documentation: https://docs.alpaca.markets/
- IEX is NOT a consolidated exchange-wide market tape. Do not infer all trades,
  full order-flow, or robust strategy alpha from it.
- This version uses an offline simulator with Alpaca *read-only* historical/latest
  feeds when owner-owned paper credentials are supplied locally.
- An **optional, separately gated** Alpaca paper-broker adapter constructs long-stock
  bracket orders with take-profit/stop-loss instructions. It is not live and not activated.
- No subscription, remote hosted worker, persistent daemon, broker login or
  live-money permission is created by this branch.

## Run with no dependencies, no credentials, no network

```bash
cd algo-trading
python3 -m unittest discover -s tests -v
python3 cli.py --demo --starting-cash 39.41 --output /tmp/sf-paper-demo.json
python3 cli.py --replay your_minute_bars.csv --starting-cash 1000
```

CSV header: `symbol,time,open,high,low,close,volume`. Time must include timezone.

## Optional official paper data (read-only)
1. Create an Alpaca **paper account** at https://app.alpaca.markets/paper/dashboard .
2. Put API credentials in LOCAL environment variables, never in Git or chat:
   `ALPACA_PAPER_KEY`, `ALPACA_PAPER_SECRET`.
3. Query a current IEX minute without trading:
   `python3 cli.py --iex-latest SOFI AAL F`
4. Test historical IEX minute bars (availability depends on account/feed):
   `python3 cli.py --alpaca-history SOFI --from-utc 2026-10-19T13:30:00Z --to-utc 2026-10-19T20:00:00Z --starting-cash 1000`

## Optional paper-broker integration (NOT activated)
- **Read-only preflight:** `python3 paper_executor.py --symbol SOFI` once a paper
  account's credentials are locally configured. It fetches IEX minute bars and
  checks account/position/market status when a signal appears.
- **Paper-only order mode** is dual-gated: the explicit `--paper-submit` flag AND
  `SF_PAPER_ORDER_ENABLE=PAPER_ONLY_APPROVED`; do not enable either before user
  specifically approves connecting the paper account and testing paper orders.
  The adapter has the hardcoded host `https://paper-api.alpaca.markets`.
- No live broker endpoint, short selling, options trading, persistent launcher,
  schedule, or background polling is supplied. Dry-run is the default.
- No account has been connected and no Alpaca paper orders have been placed.

## What v0.1 does
- Ingest timestamped OHLCV bars.
- Find a volume-backed breakout using only completed bars.
- Simulate a **next-bar entry**, fee/slippage estimates, allocation cap, stop
  losses, take profit, session liquidation, cooldown and max round trips/day.
- Reject out-of-order duplicate bars.
- Log every simulated entry/exit with timestamp and realized P/L.
- Show win rate AND net return, not misleading hit rate by itself.

## Strict limits
- **No option contracts**, no short sales, no fractional shares, no leverage.
- **No orders have been submitted**; the broker adapter is prepared for optional
  Alpaca paper-order tests but not enabled. Local demo/replay never sends orders.
- Synthetic demo data is a wiring demonstration, **not a backtest result**.
- OHLC stop/target collision assumes worst-case stop first. Market gaps and
  slippage can exceed modeled assumptions, and real bracket orders aren't
  guaranteed.
- Backtesting a strategy on the data used to choose it overfits; add a
  walk-forward/out-of-sample sample, trading costs, and paper forward test.
- No guarantee of 90% wins, profits, or instant fills.
- At $39.41, the default 20% allocation is insufficient to buy a single
  ~$14 SOFI share, deliberately preventing unsuitable oversized entries.
  Do not increase size just to force a trade.

## Planned gates (all remain disabled)
1. Broker-authorized Alpaca paper account connection; separate paper-only keys.
2. Streaming completed IEX bars, staleness/market-hours gates, reconnection and
   deduplicated orders.
3. Simulated paper-broker parity, rejected orders, manual shutdown, hard daily
   loss cap, max order value and kill switch; no unattended run before tests.
4. Walk-forward performance and days/weeks of paper-forward verification;
   compare with a buy-and-hold baseline.
5. Only then evaluate **specific approval** for a real-broker integration,
   funding and live trading, including exchange/regulatory account limits.

Never place brokerage secrets or account numbers in the public GitHub repo.
