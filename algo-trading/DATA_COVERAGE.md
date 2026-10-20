# Multi-source market coverage (v0.3 review branch)

**Status: read-only market-data research components. NO order placement, brokerage
funding, live credentials, 24/7 running daemon, options order automation,
live profitability claims, or agent authorization.**

This upgrade lets the original IEX-only trading lab distinguish data-source
coverage rather than treating every quote as equivalent. It adds a read-only
Tradier REST quote adapter, Tradier stream-message parser, free public Kraken
spot order-book reader, and a fail-closed coverage-quality gate.

## What is actually covered

| Domain | Provider | Source type | Available without paid data subscription? | Status in our code |
|---|---|---|---|---|
| U.S. stocks / ETFs | Alpaca free IEX | **Single venue**, not SIP NBBO | Yes, with user Alpaca data credentials | Existing research WebSocket; NO live orders |
| U.S. stocks / ETFs | Tradier *live brokerage* API | **Consolidated market feed**, Level 1 | Yes for eligible live-account holders, brokerage fees/eligibility separate | NEW read-only REST parser/client, not connected |
| U.S. listed options | Tradier *live brokerage* API | **Consolidated market feed**, Level 1 | Yes for eligible live-account holders, brokerage fees/eligibility separate | NEW read-only REST parser/client, not connected |
| U.S. stocks/options | Tradier sandbox | Delayed 15 minutes | Yes with Tradier sandbox | Normalization marks delayed; **never live-ready** |
| U.S. options | Alpaca free options feed | Indicative, NOT OPRA NBBO | Basic paper/live user access | Data-quality category only; no new options streaming connector |
| Crypto spot (USD pairs) | Kraken public PreTrade | Single venue, Kraken spot book | **No account and no token required** | NEW working public read-only snapshot (BTC/USD verified) |
| Crypto spot across *all* exchanges | None | No consolidated universal NBBO | No universal free feed | NOT available |
| All U.S. exchange L2 depth, global order flow | None | Separate licensed services | Not universally free | NOT available |
| Futures, FX, global securities, premium real-time news | None | Varies | Varies | NOT implemented |

**The system does not cover every market yet.** It offers modular source adapters,
not unlimited legally redistributable free market data. The Alpaca IEX stream is
limited to 30 symbols on Basic. The Tradier REST reader is capped to 50 symbols
per call in our implementation; future streaming must honor its session and API
limits. Real-time news/social flow and cross-venue options level 2 are NOT
provided by this branch.

Official sources:
- Alpaca Basic: https://docs.alpaca.markets/us/docs/about-market-data-api
- Tradier live data: https://docs.tradier.com/docs/market-data
- Tradier quotes: https://docs.tradier.com/reference/brokerage-api-markets-get-quotes
- Tradier market stream: https://docs.tradier.com/docs/streaming
- Kraken public PreTrade: https://docs.kraken.com/api/docs/rest-api/get-pre-trade
- Market-data licensing examples: https://www.interactivebrokers.com/en/pricing/market-data-pricing.php

## Run completely free, no brokerage credentials

From the isolated `algo-trading/` directory:

```bash
python3 -m unittest discover -s tests -v
python3 coverage_report.py --demo
python3 coverage_report.py --kraken-public --crypto-pairs BTC/USD
```

`--demo` is **explicitly fabricated prices** to demonstrate source selection.
`--kraken-public` fetches a true public Kraken order-book snapshot (only Kraken
venue data). These commands do **not** connect to any trading or funding endpoint.

## Optional Tradier read-only live quotes (NOT activated)

If the owner chooses to open and authenticate an eligible Tradier live brokerage
account later, configure the production market-data token securely **outside
GitHub, chat, scripts and logs**. The broker token may have trading privileges,
so it is security-sensitive even if this code only issues GET requests.

```bash
# Put the genuine token into the host's secure environment, NOT this shell example.
# The actual variable must be provisioned separately by the account owner.
SF_TRADIER_DATA_ENABLE=READ_ONLY_APPROVED python3 coverage_report.py --tradier-live --symbols SOFI SPY SOFI261023C00015000
```

The exact `TRADIER_LIVE_DATA_TOKEN` must already exist in the host process
environment. Both env vars are required or the adapter makes **zero network
requests**. The only Tradier URL compiled into the adapter is
`https://api.tradier.com/v1/markets/quotes` (GET only). It never posts or
modifies trades. No live-account signup, token, subscription, or brokerage
connection has been done on behalf of the owner.

The REST quote parser requires separate exchange-side timestamps for the bid
and ask. A single stale/missing/crossed price fails closed, even if the last
reported stock trade is recent. Streaming market event parser is available,
but a persistent Tradier WebSocket consumer is **not connected** in this branch.

## Coverage/risk behavior

- Whitelisted provider/asset coverage; raw feed messages cannot promote
  IEX/indicative/delayed quotes into an exchange-wide source.
- Requires authenticated/entitled source adapters before accepting their quotes.
  Kraken public book needs no credentials but remains **single venue only**.
- Rejects non-finite/crossed quotes, missing bid and ask timestamps, source
  timestamp problems, out-of-order updates, overly wide spreads, stale receipt
  times and strongly contradictory simultaneous feeds.
- For a Kraken REST order-book snapshot, a resting best bid/ask may not have
  changed recently. Its exchange-publication timestamps are preserved; the
  authenticated public HTTPS snapshot's receipt time determines **snapshot**
  recency, not last resting order modification.
- `DATA_READY` means **market data can be considered by other read-only
  research/risk stages**. It does NOT mean a profitable trade has been found,
  that the brokerage order will fill, or that live trading is authorized.
- Source disagreement blocks; there is no concealed automatic fallback to a
  potentially worse provider for live-money execution.
- The Alpaca streaming candidate report now includes
  `market_data.coverage = single_venue` and `live_order_authorized = false`.
- **No adapter in this release implements order placement**, modifies
  trading accounts, or bypasses existing broker/risk/owner authorization.

## Next verified development gates (before actual live money)

1. Connect owner-created **paper** Alpaca credentials securely, verify
   actual WebSocket latency and brokerage paper-order reconciliation.
2. If the owner opts in, connect **live quote entitlement only** with Tradier;
   implement persistent read-only streaming, heartbeat/reconnect, separate
   paper brokerage, and conflict/failover alerting. Do not copy data in ways
   violating provider agreements.
3. Extend symbol-universe selection, crypto streaming, economic-event and
   official public filings/news readers, and cross-venue data-quality audits.
4. Benchmark strategy performance out-of-sample and in forward paper trading
   after realistic fees, spread, slippage, latency, bad fills, halts, and gaps.
5. Implement a **separate** explicitly authorized real-money broker adapter
   only after broker suitability, funding, owner-defined dollar limits,
   kill-switch, reconciliation, execution and operational tests pass.

**Software-test passing is not evidence of trading profitability.**
