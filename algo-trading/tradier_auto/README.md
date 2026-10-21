# Tradier Sandbox Auto-Execution Prototype (v0.2)

**Status: source code + offline mock tests passed; NOT connected to Tradier, NOT running,
NOT trading, NOT real-time, and NOT authorized for live capital.**

This extends the existing SatisfyForge paper-trading research with a separate
**Tradier sandbox-only** options order engine. It is not a profit-making guarantee,
an optimized trading strategy, or a live brokerage integration. The older Alpaca
paper simulator is unchanged.

## What it actually does

- On `--watch` polls Tradier's **sandbox** account, underlying + OCC option quotes,
  existing orders/positions, and balances. At least 15 seconds between polls;
  default is 20 seconds. It runs only while you keep the terminal/process running.
- Checks a specific **predefined** call/put price trigger (not an AI predictor),
  current option bid/ask, maximum spread, quote ages, trading hours, available
  **cash** and option buying power, existing positions/orders, and daily loss cap.
- In fully armed **paper mode only**, previews an options OTOCO order and, **if
  Tradier accepts the preview**, submits the exact same order once. The entry is
  a buy-to-open limit with contingent sell-to-close profit and stop orders.
- Leaves a durable SQLite journal and Tradier order tag to avoid repeat entries.
  A timeout means *uncertain state, no retry*; inspect brokerage orders by tag.
  Subsequent polls report broker order status, not assumed fills.
- Maximum configured premium is **$60 inclusive of estimated fees**; more than
  one open order/position is refused; stops and targets are priced in option
  dollars **per share**, not whole-contract dollars. A 5-cent increase on two
  standard 100-share contracts is $10 gross, NOT guaranteed.
- Trade entry times are 9:35–14:59 **New York time, weekdays**; after hours,
  weekends, or stale quotes cause refusal. Trading sessions and holidays beyond
  weekends are validated by broker preview, *not* by a full exchange calendar.

## Critical limitations

Tradier sandbox equity and options **market data is delayed ~15 minutes**, with
no sandbox market-data streaming (see
https://docs.tradier.com/docs/market-data and https://docs.tradier.com/docs/faq).
This can test code/order semantics but **cannot validate sub-minute scalping
performance or a live speed advantage**. Even if paper fills look profitable,
that is not evidence live capital would make the same gains.

- The code never connects to `api.tradier.com`; no production host or live-order
  code path exists. It cannot withdraw or move funds from Robinhood.
- OTOCO exit handling is delegated to **Tradier's broker simulator**: child stop
  orders can fill below their trigger or be rejected; stop limits can also fail
  to execute. Tradier's broker preview must accept this options OTOCO variant.
  If not, the runner refuses to fall back to an **unprotected** naked option.
- `duration=day` means broker-side orders may expire at session end. The runner
  does **not** auto-liquidate residual positions or guarantee stop protection
  overnight. Always inspect positions and expired orders before the market closes.
- No independent stock-news catalyst filter, cross-asset portfolio allocation,
  backtest alpha, external cloud server, streaming feed, or automatic deployment.
- The broker's day-trade rules, approval levels, fees, slippage, outages, and
  available funds can prevent or worsen execution. Risk controls reduce but
  cannot eliminate losses beyond target; the entire premium can be lost.
- `balances.close_pl` is used as a fail-closed account-level risk proxy. If it
  isn't returned by the sandbox, no new entry is permitted. It is not a complete
  broker reconciliation of daily cash flows, transfers, fees, or P&L.
- This engine blocks new orders if the account has ANY open orders or positions.
  Do not share the paper account with other strategies while testing.
- Only **one running process** using the same persistent SQLite journal is
  supported. Starting copies with different journal files destroys local dedup.

## Local setup (read-only and safe by default)

1. Read the existing `algo-trading/README.md` and this file.
2. Configure the Tradier sandbox account in your **own** terminal; DO NOT
   paste credentials in ChatGPT, GitHub, logs or screenshots.

   ```bash
   export TRADIER_SANDBOX_TOKEN='paste-token-locally'
   export TRADIER_SANDBOX_ACCOUNT='paste-sandbox-account-id-locally'
   cd algo-trading
   python3 -m unittest discover -s tests -p 'test_tradier_auto.py' -v
   python3 -m tradier_auto.cli --rules tradier_auto/example_rules.json
   ```

   The sample rule is **disabled**, for illustration only, and references a
   dated AT&T option that may expire. Edit it to a current sandbox option, verify
   its OCC contract with the chain endpoint, review any risk limits, and keep
   `enabled: false` until deliberately testing paper orders.

3. Read-only foreground monitor (does not submit or preview orders):

   ```bash
   python3 -m tradier_auto.cli --rules tradier_auto/example_rules.json --watch --interval 20
   ```

4. **Optional future sandbox-order testing only**, after separately approving
   actual *paper* orders, confirming sandbox account identity and preview support,
   and deliberately enabling all **three gates**:

   - Strategy JSON must contain `"enabled": true`.
   - Set local env var `SF_TRADIER_PAPER_ORDER_ENABLE=SANDBOX_OPTIONS_ONLY_I_APPROVE`.
   - Run with `--sandbox-submit` (optionally `--watch`).

   The runner previews before placing and stops after any broker/API failure.
   **These gates are NOT enabled by the repository or ChatGPT.** No live mode exists.

## Source and verification

- `runner.py`: configuration validation, risk checks, sandbox-only REST adapter,
  OTOCO entry/exit form, SQLite deduplication, broker order reconciliation.
- `cli.py`: one-shot and foreground-only monitor; disarmed by default.
- `example_rules.json`: illustrative **disabled** 2-contract AT&T put entry.
- `../tests/test_tradier_auto.py`: offline fake-broker tests with no network.

Validated offline with Python's standard library. **No broker sandbox POST has
been attempted with real credentials.** Actual Tradier response formats and OTOCO
preview requirements still need live sandbox (paper-only) readback and tests.

Official references:
- https://docs.tradier.com/docs/trading
- https://docs.tradier.com/docs/market-data
- https://docs.tradier.com/reference/brokerage-api-accounts-get-account-orders
- https://docs.tradier.com/docs/rate-limiting
