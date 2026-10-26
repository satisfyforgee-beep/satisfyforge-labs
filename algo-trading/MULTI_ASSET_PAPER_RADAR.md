# Multi-asset paper radar — dry-run only

**Status (October 26, 2026):** Research-only, supports stocks, long option
premium (100 shares per contract), and unleveraged spot crypto. It never
touches a broker, starts a schedule, executes an order or claims proven alpha.
Built on the prior offline paper capital ledger and quote-quality gate.

The user's broader objective is to screen opportunities across many symbols,
place bounded *broker-connected paper* trades after explicit safeguards, and
reinvest only realized, settled simulated proceeds. **This first part is
neither an execution adapter nor a fully automated strategy.**

### Try public crypto data without any API token

```bash
cd algo-trading
python3 opportunity_report.py --pairs BTC/USD ETH/USD SOL/USD
```

Live public Kraken prices are a **single-venue research reference**. The
command uses a temporary $150 **offline hypothetical** ledger to show whether
a $30-or-less long-only position could be sized at the observed ask, assuming
a placeholder $0.25 entry cost. No actual paper brokerage capital or
position changes, and no artificial profit is credited.

### Safety rules

- A research proposal requires a verified-format offline capital snapshot,
  validated and current quote, acceptable spread and positive remaining
  settled cash after reservations. It respects five combined positions and
  unfilled entry intents, with a $30 inclusive cap per new position.
- Stock buying assumes whole shares. Options assume long **one or more whole
  100-share contracts**, require at least seven calendar days to expiration,
  must fit the entire premium inside the cap, and require current consolidated
  quotes during the regular equity session. Crypto uses long fractional units
  to 8 decimal places, with order minima and actual fees still unverified.
- Tradier Sandbox stock/options prices are delayed about 15 minutes, which
  is not suitable for selecting rapid entries. Alpaca crypto paper trading is
  documented, but **no Alpaca crypto account credentials have been connected
  here**. Crypto public quote access does not give order authority.
- A fresh affordable quote is **not a strategy signal**. A later candidate
  ranking pipeline needs auditable prior-completed data (price/volume trend,
  bid/ask depth and fees), independently checked catalysts, walk-forward
  testing, maximum drawdown and benchmark comparison.
- SOFI's existing unverified paper exit history remains an independent
  position block. No new Tradier equity or option orders may bypass it.
- Nothing here changes the user's existing approval of up to five $30
  **stock-only** sandbox entries. Options/crypto broker submissions require
  separately verified venue permissions, execution safety and bounded consent.
  Real money, leverage, naked options, shorts and unrestricted unattended
  execution remain disabled.

Run `python3 -m unittest discover -s tests -q` offline.
