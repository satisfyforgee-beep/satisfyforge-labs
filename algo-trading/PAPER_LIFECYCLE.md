# Tradier sandbox paper order lifecycle (v0.5 review)

**Working software is NOT a running bot.** The connected sandbox API and a
GitHub Actions secret were verified separately on October 20, 2026.
This review adds one-share, **SANDBOX-only** OTOCO brackets with preview,
strict risk checks, idempotency and broker status readback. It has no
production host, live-money order route, cloud trade scheduler, deposit
handling, or automatic strategy-triggered submission.

## Exact service boundaries

| Capability | Status |
|---|---|
| Tradier sandbox authentication via existing GitHub secret | Previously verified in successful GitHub Actions run |
| Read sandbox profile / balances / orders / positions | Implemented; requires working token at runtime |
| Construct equity OTOCO entry plus profit and stop exits | Implemented and offline-tested against official form specification |
| PREVIEW order with `preview=true` | Implemented; simulated broker validation, **no order** |
| Sandbox paper BUY with native conditional exits | **Implemented but OFF**: per-call flag, separate environment kill switch, durable journal and broker checks all mandatory |
| Check broker order by exact ID | Implemented; distinguishes pending/open/partial/filled/rejected |
| Check OTOCO child leg activation/fill and recover from partial fills | **Not yet complete**; client warns; do NOT run unattended |
| Live funds / live broker orders / options trading | **NOT implemented/authorized** |
| Realtime live execution signal | **NOT available from sandbox**; delayed market data |

## Zero-cost verification in GitHub Actions

The **existing** `.github/workflows/tradier-sandbox-readonly.yml` is extended,
not duplicated. The new branch-specific job runs the original read-only
user/quote check and then validates an OTOCO with **preview=true only**.

- Reuses repository secret: `TRADIER_SANDBOX_TOKEN`.
- Does not read a production secret; only host compiled is
  `https://sandbox.tradier.com/v1`.
- CI explicitly unsets `SF_TRADIER_PAPER_ENABLE` and never calls
  `submit_paper()`. All HTTP requests are limited to whitelisted read-only
  routes and POST `preview=true`.
- Sandbox quote is **15-minute delayed**; use it for integration smoke tests,
  never as a live trading signal or guaranteed executable price.
- The preview uses **exactly one** equity share, $1–$20 maximum limit,
  symbols SOFI/AAL/F/CLF only; the broker may return a preview warning or
  account error. On any broker uncertainty it fails closed.
- Warnings and ambiguous JSON are denied; output excludes customer name,
  exact account ID, API secrets, raw brokerage responses and URLs.
- No robot continuously monitors markets. Running GitHub Actions after a
  push **does not imply** a trading bot is running.

To test locally without any credentials:

```bash
cd algo-trading
python3 -m unittest discover -s tests -q
python3 tradier_paper_cli.py --help
```

To test through existing GitHub Actions authorization, run the branch job
**Tradier Sandbox Validation and Protected Order Preview**. No additional
secret should be pasted into chat, GitHub code, workflow inputs or logs.

## What the paper-order adapter enforces

- **One paper order/account/day.** Current-day broker orders or *any* open
  positions block a new entry. A durable SQLite journal also reserves
  an account/day identity before submitting, so repeated calls are denied
  even if the broker is slow to show the first order. Missing or truncated
  broker order lists are blockers; account identifiers are not logged.
- **Unleveraged notional:** $20 cap, quantity exactly one, local account
  total cash must cover the entire limit. Never treats margin buying power
  or sandbox virtual equity as a live personal cash balance.
- **Trading window:** 9:35 a.m.–2:44 p.m. New York time, business days,
  for the *paper POST* only. A sandbox preview may be inspected outside
  trading hours but is not an executed order.
- **Bilateral protection requested in one submission:** Tradier OTOCO:
  entry limit buy, ~3.5% target limit sell, ~2% stop-market sell; broker
  controls the OCO relationship once the entry fills, subject to actual
  brokerage acceptance and market rules. Stop orders can fill worse than
  their trigger; a gap can exceed modeled losses. Duration is DAY for
  testing; the bracket is not an overnight protection guarantee.
- **No production trading:** The transport is hard-coded to Tradier's
  SANDBOX host; API keys for other environments cannot create live trades.
- **Two independent simulated-write gates:** a per-call explicit boolean
  and exact `SF_TRADIER_PAPER_ENABLE=SANDBOX_ONLY_APPROVED` setting.
  The CLI and Actions workflow **do not contain a submit option**.
- **Broker response not equivalent to a fill:** A successful POST only
  acknowledges receipt; the exact order must be read back to determine
  filled, rejected, cancelled, expired or partially filled status.
  Confirm child exit orders separately before trusting automated exits.
- **Uncertain POST:** write UNKNOWN to journal, halt and manually reconcile.
  No auto-retry and no accidental duplicate orders.

### Required remaining work before an actual paper-order experiment

1. Confirm API PREVIEW response and broker account restrictions using the
   existing sandbox secret. Separate owner authorization is needed before
   arming the simulated write path.
2. Add post-submit **exact order and child-leg reconciliation**, broker
   cancel/replace behavior, partial-fill repair, and audit logs. Test all
   against the real sandbox, not just mocks.
3. Connect fresh, licensed live market data and quality gates to candidate
   selection. Do not use the 15-minute-delayed sandbox quotes to day trade.
4. Build a reliable persistent owner-operated runner with watchdogs,
   network-failure shutdown, business-day market calendar, and hard risk
   budgets. GitHub Actions jobs are unsuitable for fast continuous trading.
5. Validate many sessions of out-of-sample paper P/L, costs and failures;
   only then design a *different*, explicitly reviewed, separately armed
   live-money adapter. Trading real capital will require owner-approved
   account, funded amount, per-trade/day ceilings, kill switch and risks.

Docs: https://docs.tradier.com/docs/trading ,
https://docs.tradier.com/docs/account-details ,
https://docs.tradier.com/docs/endpoints

**Software-test passing or PREVIEW_OK does NOT demonstrate a 90% win rate,
a profitable strategy, continuous operation, or filled brokerage orders.**
