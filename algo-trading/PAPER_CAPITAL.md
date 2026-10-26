# SatisfyForge — paper-capital reinvestment ledger (offline research)

**Status (2026-10-26):** Implemented and locally tested as a reusable, standard-library Python **OFFLINE replay** component. It is **not connected to a broker**, is **not a scanner or trading strategy**, and never submits, modifies, cancels, or approves an order. No real or paper brokerage profit is claimed.

## Purpose

Track an experimental **$150 simulated strategy budget**, up to **five combined open positions / pending entry intents**, and **$30 maximum debit per new paper order including estimated fees**, without pretending a closed position paid out before the brokerage settles and releases funds. These are initial engineering limits based on the prior five-equity-trade test authorization; increasing them in a future broker-connected runner needs a specific new authorization and risk review. Research can cover more symbols than the five simultaneously held positions.

This module complements `zerocost_bot/engine.py` (historical replay), `journal.py` (broker-order idempotency), and `tradier_paper.py` (one-share sandbox integration). It does not replace or bypass any of their safeguards.

## Accounting rules

- **Entry:** Reserve the order's maximum paper debit before a buy. Only a subsequently recorded fill decreases settled cash and establishes a long position. Pending reservations reduce immediately available buying power. A partial fill does not free the remainder of the reservation.
- **Exit:** The sale matches confirmed long lots using FIFO cost basis. Realized P/L is proceeds net of exit fees minus entry cost **including allocated entry fees**. Selling more than owned is rejected, rather than opening a short.
- **Reinvestment:** All sale proceeds initially stay **unsettled**, even for crypto, until a separate settlement-confirmed event. After settlement the proceeds become available for the next reserve, subject to the independent $30/order and five-position/intents limits. A cash-account broker may impose other clearing, good-faith, buying-power, options approval, or regulatory rules; its own verified settled cash is authoritative.
- **Assets:** Long US stocks (integer shares), long options (integer contracts, premium × 100), and unleveraged fractional spot crypto (eight decimal places). This is *accounting support only*, **not** authorization or a connected order implementation for crypto or options. No naked options, margin, shorting, futures, perpetuals, loans, or leverage.
- **Evidence:** Duplicate execution IDs are idempotent only if the complete event is identical; conflicting IDs, overspending, unsupported instruments, missing inventory, unpaired settlements, and configuration changes halt. Events persist in a private SQLite file with mode 0600. In a future connected adapter, a fill must be verified from the appropriate paper broker; only a broker-confirmed terminal order can release an outstanding reservation; only independently verified available/settled cash can release sale proceeds.
- **Valuation:** Unrealized gains, stale valuations, paper broker buying power, and brokerage settlement are **not inferred** from this offline ledger. Its reported `realized_net_pnl` is a replay measurement only, not a verified account performance statement. Capital available to spend is not the same as net portfolio equity.

## Run offline tests ($0, no tokens or orders)

```bash
cd algo-trading
python3 -m unittest discover -s tests -p 'test_paper_capital.py' -v
python3 -m unittest discover -s tests -q
```

## Illustrative **synthetic** example

Start with a $150 paper budget. Reserve a two-share SOFI buy at $12/share plus $0.10 total entry fee, so the available settled cash drops to $125.90. If the two fills occur at the reserved amounts and the shares are subsequently sold at $14/share, the **hypothetical** after-cost realized P/L is +$3.90. The $28 proceeds are **not spendable** before a separate settlement-confirmed event; after settlement this synthetic strategy budget is $153.90, but the next order remains capped at $30. Conversely, a losing exit reduces subsequent buying capacity. The exact return is purely illustrative, not a SatisfyForge trading result.

`PaperCapital(path)` / `reserve_buy` / `buy_fill` / `sell_fill` / `confirm_settlement` / `release_terminal_reservation` / `snapshot` expose explicit events for research fixtures. No actual order or broker feed is wired to these methods. Keep the SQLite file under a private owner-only directory, **not** a public repository.

## Required before using with the connected Tradier/Alpaca paper accounts

1. Resolve the existing **SOFI sandbox share with zero listed current orders** and verify whether native exits are truly absent, expired, or elsewhere in broker history. The GET-only 2026-10-26 audit reports `HALT_POSITION_EXITS_UNVERIFIED`, so no new Tradier entries should be sent under the present gate.
2. Build a dedicated **read-only**, broker-specific importer for order executions, fees, and actual settlement/buying-power readbacks. Verify account identity, execution-ID uniqueness, possible partial fills, cancellations, corporate actions, cash transfers, order-history pagination, reconciliation parity and stale/unknown states before feeding this ledger. Mark-to-market and daily loss controls remain independent.
3. Add and test safe connector-specific signal/quote freshness, spread/liquidity, hours/calendar, broker-native protective exits (where supported), actual fills and fees, risk budgets, restart/idempotency locks, abort conditions and a permanent kill switch. Delayed Tradier Sandbox quotes cannot be used as real-time data for a day-trading strategy.
4. Keep new instruments disabled until a separately approved **bounded** paper test. Crypto and options also require different risk, execution, expiry/assignment or 24/7-market safety models; long option contracts can expire at zero and lose all premium.
5. Continue precommitted out-of-sample tests and weeks of forward paper evidence; no strategy is proven profitable. Real-money account access, credentials and execution remain entirely disabled.
