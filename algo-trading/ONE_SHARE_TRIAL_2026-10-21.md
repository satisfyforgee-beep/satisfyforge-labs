# Owner-approved ONE SOFI simulated test — 2026-10-21

**Authorization:** In conversation, owner explicitly approved *one* SOFI
share in Tradier SANDBOX, with a maximum $20 entry limit, ~2% protective
stop and ~3.5% take-profit. Approval does NOT include live brokerage
money, options, margin borrowing, a second order, recurring trades,
automatic retries or future real-money execution.

**Current implementation:** New isolated branch
`feature/tradier-one-share-paper-20261021` adds a one-use, date-gated
sandbox experiment to the existing SatisfyForge trading lab. It DOES
NOT turn on any always-on trading bot or commercial customer service.
The GitHub Actions workflow uses the existing sandbox secret without
displaying it or moving it to an owner desktop.

## Entry and execution gates

1. Strict NY time: **Wednesday Oct 21, 2026, 9:35 AM–2:44 PM ET**.
   Premarket push does *nothing* to brokerage. The future market-hours
   workflow retry is one-time, not recurring.
2. Tradier's **SANDBOX** market clock must report `state=open` and
   the same local trade date. A timeout/mismatch blocks trading.
3. Test asset fixed to **SOFI common stock**, quantity fixed to
   **exactly one share**, cash only, no options.
4. Delayed Tradier sandbox ask sets the simulated test LIMIT at
   ask+$0.01, provided LIMIT <= $20. This is solely an API/engineering
   test, **not a real-time profitable entry signal**.
5. Broker state checks no existing orders, positions or pending orders
   on the selected sandbox account. The account must have enough
   simulated cash for the 1-share limit price.
6. Native OTOCO conditional bracket: buy limit first, linked 3.5%
   target limit sell and 2% stop-market sell, rounded conservatively.
   Broker's actual accept/fill and exit activation must be separately
   verified; stop triggers are not guaranteed fill prices.
7. A fresh `POST preview=true` must show no alerts and total simulated
   debit **at or below $20, including estimated fees**. A missing or
   invalid cost is a BLOCK, never defaulted to zero.
8. After preview, read broker balances, orders, positions, and market
   clock AGAIN. A durable per-account/day journal blocks a duplicate
   within a run; the broker's current-day orders/positions further
   protect against duplicate attempts across workflow jobs.
9. **Exactly one** sandbox POST without `preview=true`, only if all
   requirements pass. No repeated POST after a network or response error,
   no fallback to live brokerage.
10. Upon broker acknowledgement, use exact order ID *internally* to
    read entry status and independently verify linked protective legs,
    without publishing account numbers/order IDs/API tokens. Stop
    on missing linkage, partial fills, rejected data, timeout or
    inconsistency.

## Automatic scheduling and safeguards

Workflow:
`.github/workflows/tradier-single-approved-sandbox-test.yml`

The initial GitHub Actions push before market hours is safe: the
date/time gate skips all brokerage requests. A subsequent market-hours
**rerun of the same specific job** is needed for the one user-approved
experiment, scheduled separately by the assistant at approximately
10 a.m. EDT on October 21. It is NOT a standing daily automated trade,
and MUST NEVER be rerun for a different date or symbol.

A rerun may be blocked, queued, unavailable or rejected by the broker;
those outcomes should be reported as such rather than claiming a fill.

GitHub workflow has a fixed branch, one resource-concurrency group,
readonly GitHub permissions, short timeout and only the existing
`TRADIER_SANDBOX_TOKEN` secret. It contains NO production keys.

## What is NOT guaranteed

- Tradier paper quotes are delayed 15 minutes.
- A submitted order can remain unfilled, reject, or expire.
- An OTOCO preview is not an executed or filled order.
- Tradier may represent OTOCO children differently from the
  strictly validated offline test fixtures. A filled parent with
  unverifiable children must be flagged, not labeled protected.
- A two-minute readback during the GitHub Actions job is not
  an always-on 24/7 order monitor.
- A stop market order can fill below its trigger; the 2% figure
  references the entry *limit*, not necessarily a different fill.
- Simulated fills don't show real-world spread, slippage or live
  execution performance. This test is NOT expected to make money.

**Evidence required next:** Actual sandbox job output showing its broker
accepted one paper order, entry fill status and child-order linkage
with the proper protected/closed/unverified classification. Until then
report **prepared/scheduled**, NOT traded.

## Owner review

The test may be inspected at the branch's workflow and
`algo-trading/tradier_one_share_test.py`. No sensitive values, API tokens
or account identifiers should be pasted into GitHub comments or chat.

Before activating any live-money route, complete independent broker
permissions, cash/margin checks, full risk controls, and forward paper
profitability validation. None are authorized by this one-time test.
