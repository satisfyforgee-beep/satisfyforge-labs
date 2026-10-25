# Tradier sandbox-only read-only research lab

**Verified baseline (2026-10-20):** GitHub Actions run 39474133636 completed successfully: sandbox token authenticated, one paper account detected, SPY delayed quote retrieved, four offline smoke tests passed. The token is stored as a GitHub Actions repository secret `TRADIER_SANDBOX_TOKEN`; **it is not in GitHub source control.**

**Latest verified test (2026-10-25 14:24 ET): SUCCESS** in GitHub Actions run [40221053330](https://github.com/satisfyforgee-beep/satisfyforge-labs/actions/runs/40221053330). All 32 offline tests passed (4 connection, 10 broad scanner/ledger, 18 historical); sandbox authentication found one paper account; the fixed 107-symbol cross-sector universe completed in bounded batches. Because the run occurred on Sunday, all 107 quotes correctly failed the 30-minute freshness gate, yielding 0 eligible rows and no action. Historical global decision remained **PASS / NO TRADE** because the precommitted SOFI breakout holdout still failed and earlier walk-forward evidence remained insufficient. No brokerage orders, account changes or transfers occurred. A past success does not guarantee future token availability. The live brokerage margin-to-cash request is separate from the sandbox.

## Scope and safeguards

- ONLY `https://sandbox.tradier.com/v1`, with allowlisted GET `/user/profile`, `/markets/quotes` and `/markets/history`; never `api.tradier.com`. No order requests of any kind, even paper orders.
- Sandbox quotes are approximately 15 minutes delayed and can be much staler after market close. `bid_date`, `ask_date` and `trade_date` are epoch milliseconds; the scanner shows the oldest as-of timestamp and flags data older than 30 minutes. A single delayed snapshot is **not** a signal to trade, or proof of executable bid/ask.
- The scanner handles stocks and ETFs only; it estimates affordable **whole shares** with a hypothetical $30 cash-only budget. It accepts a reviewable file of up to 500 unique symbols and makes bounded 50-symbol quote batches. It rejects missing/crossed bids and asks, oversized spreads, non-stock instruments, stale/unavailable timestamps, missing or insufficient average volume, and unavailable top-of-book size. Eligible rows are ranked only by quote usability (spread cost, spread percentage, average volume), never by predicted direction or profit. It does **not** recommend buys.
- The offline replay ledger operates on locally supplied **hypothetical** CSV data. It assumes buys at the supplied ask and sells at the supplied bid, supports manually specified fees, refuses shorts and borrowing, and marks open holdings to the last supplied bid. It does not simulate slippage, volume constraints, taxes, execution uncertainty, liquidity shocks or options greeks, and is not a full backtest.
- The historical research engine uses daily OHLC, sealed holdout, two anchored training-only walk-forward windows and cost/risk stress. Details and validation outcomes: `docs/TRADIER_HISTORICAL_RESEARCH.md`.
- No continuous scanner, scheduled trade strategy, broker order placement, capital transfers or real-money API access. In the current draft PR, scans run only on trusted code pushes to its fixed branch. Manual workflow dispatch may require the workflow to exist on the default branch after review/merge.
- This is a **public repository**. Never commit/log keys, account IDs, actual transactions, other personally identifiable information or brokerage balances. Do not upload local paper journals into public CI/artifacts. Do not run secret-bearing jobs from untrusted PRs.

## How to use

1. To inspect the GitHub sandbox job, visit **Actions → Tradier Sandbox Read-Only Verification**. It runs the offline tests, checks authenticated sandbox read-only access and, **only if that succeeds**, prints non-personal delayed research summaries. It must have a currently authorized sandbox token in the `TRADIER_SANDBOX_TOKEN` repository secret. No paid services or upgrades are required.
2. On your personal, trusted computer, securely set environment variable `TRADIER_SANDBOX_TOKEN` with your **sandbox** token. Avoid shell history, source files and chat messages. Run `python3 scripts/tradier_sandbox_check.py --symbol SPY` to check the sandbox connection.
3. Run `python3 scripts/tradier_paper_lab.py --scan --symbols-file config/trading_universe_us_liquid.txt --budget 30 --top 25` to inspect the fixed 107-symbol cross-sector delayed screen. The file is a reviewable research universe, not a recommendation list. The scanner outputs aggregate rejection counts and at most 25 quote-usability rows; it does not request or print account details.
4. To replay a **fully synthetic or locally stored** hypothetical share ledger, prepare a private CSV with exact headers `timestamp,symbol,action,shares,bid,ask`, timestamp in ISO 8601 with timezone, and chronological rows. Example rows:
   ```csv
   timestamp,symbol,action,shares,bid,ask
   2026-10-20T15:00:00Z,SOFI,BUY,2,9.90,10.00
   2026-10-20T15:15:00Z,SOFI,SELL,1,11.00,11.10
   ```
   These are **made-up numbers**, not actual SOFI market prices. Run locally, not in public GitHub Actions: `python3 scripts/tradier_paper_lab.py --replay /private/path/example.csv --budget 30 --fee 0`. Output is hypothetical P/L, not executed paper trades or real returns.
5. Run read-only historical research: `python3 scripts/tradier_historical_lab.py --symbols SOFI,AAL,F --start 2025-01-02 --budget 30 --cost-bps 20` (NO orders; results may be negative). Verify in `docs/TRADIER_HISTORICAL_RESEARCH.md`.
6. Offline tests (no secret or network): `python3 -m unittest discover -s tests -p 'test_tradier_sandbox_check.py' -v` and `python3 -m unittest discover -s tests -p 'test_tradier_paper_lab.py' -v`.

## Future work

- Validate scanner accuracy against documented Tradier JSON shapes and exception handling; repeat tests with future provider schema changes.
- Support authenticated, **read-only** sandbox historical prices with isolated provider tests if a next phase warrants it, or produce private, owner-reviewed paper-order proposals.
- Any ability to submit even **simulated sandbox orders** must be a separately reviewed code path with explicit authorization and positive controls. Live trade capability remains out of scope.

API references: https://docs.tradier.com/docs/endpoints and https://docs.tradier.com/reference/brokerage-api-markets-get-quotes.
