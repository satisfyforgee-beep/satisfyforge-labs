# SatisfyForge Trading Lab — private dashboard v0.4

**This is a local software prototype, NOT an investing service, public app,
hosted bot, exchange data feed, trading account, or real-money service.**

The existing trading-research modules run separately. This dashboard adds a
zero-subscription, stdlib-only, mobile-responsive HTML/CSS/JavaScript interface
to display **sanitized, read-only** research status and readiness. It does
not store or display brokerage credentials, expose an order endpoint, open a
market connection, place any trades, or report unverified earnings.

## Run locally, no external account required

On the **Mac where the repository is checked out**:

```bash
cd algo-trading
python3 -m unittest discover -s tests -q
python3 dashboard_server.py
```

Then visit **http://127.0.0.1:8765/** in the browser **on that Mac**.

The server binds only to `127.0.0.1`. It cannot be reached from your phone
or other computers. It does not run automatically on startup, and closing the
terminal stops it. Press **Ctrl+C** to stop it. The dashboard requests only
`/api/status` on the same local host; it never queries a broker or places
an order. A safe 5-second refresh updates the interface only while the
browser tab is visible.

### Optional explicitly supplied quote report

Run the existing **public, read-only** Kraken USD book command and save
a market-data report to a private local path:

```bash
cd algo-trading
python3 coverage_report.py --kraken-public --crypto-pairs BTC/USD > /tmp/sf-research-only.json
python3 dashboard_server.py --report /tmp/sf-research-only.json
```

Opening the page immediately afterward can show the last research-only
BTC/USD venue quote. The report is deliberately considered **stale after
15 seconds** (regardless of whether the HTTP page refreshes).
This is a one-shot fetch, not a background streaming service.
For an **offline fabricated demonstration**, instead run:

```bash
python3 coverage_report.py --demo > /tmp/sf-synthetic-demo.json
python3 dashboard_server.py --report /tmp/sf-synthetic-demo.json
```

Synthetic data is marked SYNTHETIC and can **never** be displayed as
verified trading P/L or a live-money trade decision.

No other trading or market-data credentials are needed for this dashboard.

## What is ready vs. not ready

**Implemented and tested:** a local UI with a read-only status API,
strictly allowlisted static routes, HTTP method denial for writes, local
host validation, cache and CSP protection, no data re-export or credentials,
disconnected/stale/fabricated data labels, redacted/allowlisted report
fields and hardcoded live execution OFF. Previous offline trading research,
paper-only broker adapter and multi-feed quote code remain unchanged.

**Not implemented or activated:** Tradier brokerage approval or account
connection; live data subscriptions; automatic paper/live fills; a durable
hosted trade runner; secure phone access; customer accounts; payments;
independent profitability verification; live brokerage execution.

The UI shows each component's **software readiness**, not a claim that
individual local AI models are installed or agents are currently running.

## Security and correctness

- Every endpoint is **GET/HEAD only**; attempts to POST, PUT or DELETE get 405.
- HTTP binds only to `127.0.0.1`, checks the Host header to reduce DNS
  rebinding risk, and serves only explicit static assets. No directory listing.
- External report paths must be supplied at process launch, never in a URL.
  Raw report content is never exposed; only small, allowlisted fields are
  returned. Account numbers, arbitrary notes, keys and untrusted
  extra JSON fields are never sent to the UI.
- Reports over 256 KiB are rejected. Quotes are checked for valid symbol,
  source, asset class, finite bid/ask and metadata before showing them.
- Reports are stale after 15 seconds; a stale or missing quote is
  **not usable as a real-money decision**.
- The default dashboard does not infer any existing Tradier connection.
- Private localhost service has **no login** by design; never bind to
  a public IP, open firewall ports, or use an unauthenticated tunnel.
- Never store real brokerage secrets in GitHub, local browser storage,
  URL query strings or screenshots.

## Roadmap to a real mobile app

A mobile-friendly webpage is not a publicly available smartphone app.
Serving this to a phone would require a separate security review:
TLS, authentication, per-user authorization, separation of brokerage
credentials, deployment security, attack-rate limiting and account
audit logs. Customer-subscription features also require billing, legal,
regulatory and market-data licensing review. None is enabled.

Once owner-owned Tradier credentials and brokerage approval exist,
separate live read-only market-data and paper-execution connections
can be tested. A distinct owner-authorized **real-money** execution
adapter must be designed, separately reviewed and activated only after
sufficient forward paper evidence, a kill switch, hard dollar limits
and broker-side reconciliation.

## Tests

```bash
cd algo-trading
python3 -m unittest discover -s tests -q
node --check dashboard_assets/app.js  # optional if Node.js installed
```

On October 20, 2026: **99 unit tests passed** on the Mac. 12 new
dashboard tests cover read-only endpoint security, fake/stale source
labels, allowlist/redaction, invalid quotes and lack of execution.
Software correctness is **not** proof of profitable trading.
