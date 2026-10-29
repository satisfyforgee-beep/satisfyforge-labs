# Tradier Historical Research — Sandbox only

Verified 2026-10-20, GitHub Actions run [39504442695](https://github.com/satisfyforgee-beep/satisfyforge-labs/actions/runs/39504442695): **30 offline tests passed** (4 connection, 8 hypothetical ledger, 18 historical); sandbox authentication, delayed quote scanner, public historical daily bars, quality diagnostics and model assessment completed.

## Purpose: disciplined falsification, NOT promised profits

The lab is an evidence filter for a hypothetical **$30 cash-only, whole-share** strategy. It evaluates three interpretable rules (10/40 moving-average trend, 20-session breakout with trend filter, 20-session mean-reversion) and buy-and-hold/cash baselines using daily OHLCV bars. It **does not use any AI prediction model** and should not be called an autonomous profitable AI trader. The advantage is honest model selection, accounting and rejection, not guaranteed prediction.

- The Tradier access token lives exclusively in GitHub Actions `TRADIER_SANDBOX_TOKEN` repository secret. This public GitHub repo never stores it, account numbers, private positions or real trades. The API helper hardcodes `https://sandbox.tradier.com/v1` and only allows GET `/user/profile`, `/markets/quotes` and `/markets/history`. No broker order endpoints of any kind.
- Fetches `GET /markets/history?symbol=...&interval=daily&start=...&end=...`. Uses **completed historical sessions only**; does not use today's unfinished daily candle. Symbols uppercase letters max six characters; 1–4 symbols per request.
- Strictly validates chronological unique trading dates, OHLC consistency, finite positive prices and nonnegative volumes; rejects future dates and price jumps greater than 50%. At most **five** isolated bad bars (and at most 1.5% of rows, with a floor of two) are dropped, never interpolated; more than two consecutive bad bars or other severe anomalies makes the symbol ineligible. Reports the exact count of dropped public OHLC records. Comparisons with cleaned symbols are **sensitivity-limited**.
- Signals are calculated at the *close* of session i from data known by then. A simulated trade can only fill at the **next session's open**, never the same bar that created its signal. Daily bar fills are hypothetical. Default adverse entry/exit cost is 20 basis points per side; 3x cost stress on the holdout. Fixed per-order fee may be specified (default $0). No borrowed funds, fractional shares, naked options, shorting, order placement or automatic profit-taking. One stock held at a time per simulation, max 85% initial budget exposure, 7% previous-close stop loss, 20% portfolio drawdown circuit breaker.
- Splits historical dataset 70% chronological **training** / 30% completely untouched **outer holdout**. Earlier 60 bars are warm-up for indicators. Selects strategies with at least two simulated entries and one exit during training using a precommitted risk-adjusted score (return - 1.5x max drawdown - activity penalty). A separate **cross-symbol candidate** is selected by training score only; it cannot switch to a later holdout winner.
- Two anchored **walk-forward** tests inside the training window each select from their own preceding observations and test on the next unseen interval. If activity is insufficient, folds are labeled abstain/fail, never filled with guessed trades. Both positive folds are required even to classify an outer-holdout winner as needing further independent confirmation.
- Holdout gate requires at least three entries/two exits, positive return beating buy-and-hold and cash, reasonable drawdown, and positive return under 3x modeled execution costs. **Even passing is labeled RESEARCH ONLY — NOT VERIFIED EDGE**. No live trading from this repo; more market regimes, data vendors and forward paper evidence would still be necessary.

## Observations — 2026-10-20

Sandbox historical daily period requested: January 2, 2025 through October 19, 2026; completed data as of Oct 19. These outcomes are *backtested on hypothetical fills*, not brokerage paper orders.

| Symbol | Valid bars / original | Excluded poor-quality bars | Pre-chosen training strategy | Final holdout hypothetical return | Research assessment |
|---|---:|---:|---|---:|---|
| SOFI | 448 / 450 | 2 malformed fields | Breakout | -19.568% | FAIL |
| AAL | 450 / 450 | 0 | Mean reversion | -5.9333% | FAIL |
| F | 445 / 450 | 5 invalid OHLC | Mean reversion | +10.9763% | Research only, unverified |

At a $30 simulated balance, Ford's $3.29 gain occurred across the entire approximately six-month outer holdout, **not per day**. The default model assumes $0 fixed commissions and 20bps per side modeled adverse execution cost; taxes, regulatory charges and portfolio financing are not modeled. These results do not establish a future profit expectation.

**No-hindsight system-level decision:** Training selected **SOFI breakout** as the highest-score ticker+strategy, rather than retroactively selecting F because its holdout was favorable. SOFI then failed both activity-sensitive anchored walk-forward checks and lost 19.568% in the holdout. Thus the entire system says **PASS — NO TRADE**. This is a *correct refusal*, not a successful trade.

## Run and verify

Trusted GitHub Actions workflow `.github/workflows/tradier-sandbox-readonly.yml` runs offline tests, authenticates to the sandbox, fetches delayed quotes, performs research and aggregate QA. It runs on changes to its monitored paths on the fixed review branch; **no recurring scheduler is active**. It is draft PR [#72](https://github.com/satisfyforgee-beep/satisfyforge-labs/pull/72), not merged into `main`.

CLI on trusted local computer, with sandbox key stored securely in environment and **not checked into GitHub**:

```bash
python3 scripts/tradier_historical_lab.py --symbols SOFI,AAL,F --start 2025-01-02 --budget 30 --cost-bps 20 --fee 0
python3 scripts/tradier_historical_lab.py --quality-check --symbols SOFI,AAL,F --start 2025-01-02
python3 -m unittest discover -s tests -p 'test_tradier_historical_lab.py' -v
```

`--require-complete` makes the command fail if any requested ticker cannot be processed; default prints each symbol's explicit result or `NO_RESULT` and fails if **all** are invalid. No silent replacement data, no private logs, no fake fills. Research step run success means code/data processed, **not** that any strategy passed the evidence gate.

## Before claiming a genuine edge

Require additional untouched forward paper-trading outcomes, cross-regime and multi-year evidence, verified corporate-action/dividend adjustments from an appropriate licensed data source, sensitivity to spreads/impact and fees, explicit market hours, and operational checks on orders/partial fills. With a $30 balance, options can quickly lose 100% premium; no options recommendations or paper-order routing have been enabled.

Source: [Official Tradier history endpoint](https://docs.tradier.com/reference/brokerage-api-markets-get-history); [official sandbox endpoint separation](https://docs.tradier.com/docs/endpoints). 
