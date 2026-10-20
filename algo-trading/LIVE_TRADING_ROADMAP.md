# Zero-subscription trading lab: v0.2 architecture and real-money roadmap

**Status (2026-10-20):** offline-tested research components only. The original
Alpaca broker adapter is **paper-only and remains disabled**. The new streaming
research program requires separate paper market-data credentials and has **not**
been connected, launched, or benchmarked on a real exchange feed. No live orders.

## Outcome we are designing for

An eventual autonomous, owner-authorized real-money trading service with:

1. **Fast market ingestion**: free Alpaca IEX event streaming, not chat polling.
   Basic free IEX is **one exchange**, so bid/ask/volume are not consolidated SIP.
   Latest provider specifics: https://docs.alpaca.markets/us/docs/about-market-data-api
2. **Parallel evidence reviewers**: trend, breakout, volume, volatility, market
   benchmark and spread/liquidity. They are *deterministic evidence agents*, **not
   secretly paid AI models**, and their vote total is **not** a win probability.
   Later add asynchronous optional local-model/news/social research; do not put
   slow LLM calls in the price-sensitive order path.
3. **Independent risk governor**: rejects stale bars or quotes, bad market
   regime, overspend, blocked broker, extra open order or position, repeat
   entries, daily drawdown or an unsuitable setup.
4. **Durable idempotency journal**: same strategy/ticker/bar cannot reserve an
   additional proposal on restart. Unknown broker outcomes require broker
   **readback by client order ID**; never retry blindly.
5. **Broker execution**: event-driven, not a ChatGPT scheduled task. Alpaca paper
   bracket orders are in the existing paper-only adapter with a two-part gate.
   A **separate live broker adapter does not yet exist**. Live credentials,
   broker approval, funding, and real-money deployment require distinct steps.
6. **Exit and reconciliation**: exchange/broker-native brackets, event stream
   fills and partial fills, cancelled/rejected status, reconnect/reconcile
   broker state, stale/connection-loss circuit breakers, audit logs.

## Optional free local AI (advisory only)

`zerocost_bot/ollama_advisors.py` adds three parallel local-model research
roles: a technical skeptic, catalyst reviewer, and risk challenger. The code
contacts **localhost only**, filters broker/private keys out of its input, and
labels every response as non-executable commentary. It can run after an owner
installs and authorizes a compatible free Ollama model separately. No local
model binary/server was found in the connected Mac on October 20; no install
or launch was attempted. Local inference can be slow; it will **never** block
or overrule the fast deterministic broker gate.

## What v0.2 actually implements

- `zerocost_bot/agents.py`: completed-bar evidence review, strict freshness,
  trend/breakout/volume quorum and vetoes; original scoring, no paid model.
- `zerocost_bot/risk_gate.py`: standalone pure preflight. Default **$20**
  maximum notional, **50%** maximum account-equity exposure, **$5** reserve,
  **$1** planned risk per position and **$3** max daily equity loss,
  maximum **two** daily entries, no leverage. These are engineering test defaults,
  **not personalized recommendations or guaranteed stop-loss bounds**.
- `zerocost_bot/journal.py`: on-disk SQLite order-intent reservations and
  state transitions. Does not contact the broker; must be integrated with
  reconciliation before unattended execution is even considered.
- `zerocost_bot/streaming.py`: optional read-only free IEX stock WebSocket
  consumer with reauth/reconnect; parses real quotes and completed 1-minute
  bars, validates benchmark, prints research candidates. No order endpoint.
- `stream_research.py`: explicit foreground research-only entrypoint.
- `zerocost_bot/ollama_advisors.py`: optional free localhost AI commentary;
  three separate advisory roles, NO trading authority or paid requests.
- Unit tests include duplicate replay, stale quote, partial bar, low capital,
  bad regime, non-finite prices, duplicate journal, uncertain outcome.

## Free way to test the code, without placing orders

```bash
cd algo-trading
python3 -m unittest discover -s tests -v
python3 cli.py --demo --starting-cash 39.41
python3 stream_research.py --help
```

Network streaming is an **optional future owner-initiated test**, after a
free Alpaca paper account is connected and the free Python `websockets`
package is installed, e.g.:

```bash
# Local environment ONLY; never paste secrets into chat or public GitHub.
# Export ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET yourself.
python3 stream_research.py --symbols SOFI AAL F SPY
```

This runs a **foreground research feed, not an unattended background daemon**.
All suggestions are `candidate` or `pass` decisions, **never trades**.
Once started it needs about 20 completed minute bars for each symbol before
reporting candidates, and the free IEX subset can omit active consolidated-tape
moves. Network failures and stale quotes must yield *no entries*.

## Honest engineering boundaries

- **No verified winning rate or live P/L exists.** 50 unit tests passing is
  software correctness evidence, not investment performance.
- Paper fills can differ from live fills because of queue position, latency,
  gaps and slippage. Stops can fill worse than their trigger. See
  https://docs.alpaca.markets/us/docs/paper-trading .
- Do not claim 9/10 profitable trades without complete live independently
  verified history, net commissions/slippage, drawdown and worst-case losses.
- With ~$39 initial equity, low-cost options concentrate risk; free indicative
  options quotes are **not OPRA executable NBBO**. This version restricts
  itself to whole-share equity research, not short-dated automated options.
- No hosting purchase, model API subscription, live account connection,
  deployment, scheduler, credential, or transfer has occurred.

## Gates before autonomous real-money deployment

1. **Paper broker ownership**: create a free Alpaca paper account, use separate
   scoped PAPER keys only in the local/secure host; never store them in the
   public GitHub repo. Verify host, symbol, market status and permissions.
2. **Stream acceptance**: run read-only IEX for real sessions, log latency,
   outages, missed bars, quote coverage and reconciliation. Compare external
   consolidated price for data-quality mismatches. No phantom fill assumptions.
3. **Replay/walk-forward**: use real out-of-sample historical periods,
   conservative fill modeling, transaction costs, volume and capacity;
   benchmark against doing nothing. Avoid tuning to one day's price path.
4. **Paper broker execution tests**: authorize paper mode explicitly, reconcile
   exits, retry/timeout behavior, partial fills, rejects and kill switches;
   log all paper trades and allow manual shutdown.
5. **Unattended test deployment**: on a user-authorized, reliable host, prove
   watchdog, recovery, uptime and broker-native exits across sessions.
   A chat session or an hourly ChatGPT task is not a low-latency trade engine.
6. **Broker/legal safeguards**: confirm that the desired Alpaca account type
   supports intended frequency and instrument, settlement, intraday margin,
   fees and API permissions. Some brokers have not yet transitioned to the
   June 2026 FINRA intraday-margin rules; verify the specific firm.
7. **Deliberate LIVE activation**: require the owner to confirm the exact
   brokerage account, maximum funded amount, per-trade/day limits, allowed
   securities/strategies, exit policies, operations host and how to halt.
   Introduce a separate live adapter with hardcoded LIVE host and explicit
   environment/reconciliation gates. Start with minimum-size live canary
   and supervision; only scale based on evidence.
8. **Never replace risk governance with an LLM**: discretionary research and
   news intelligence may suggest, but must not circumvent deterministic
   pretrade checks, account restrictions, audit trails or the kill switch.

**No real-money execution is enabled by this branch.**

## Additional reviewed paper-only order coordination

`zerocost_bot/coordinator.py` connects deterministic consensus with a
readback of the Alpaca **paper** broker account, independent cash/position
checks, an idempotency reservation, and the existing paper bracket adapter.
`prepare()` is read-only. `submit()` is disabled unless a separate
`explicitly_armed=True` parameter and the exact
`SF_PAPER_ORDER_ENABLE=PAPER_ONLY_APPROVED` environment gate are both set.
It reconfirms broker state before any paper request. On an uncertain transport
outcome it journals UNKNOWN and will **not retry**. Tests use an entirely
mocked broker; no broker was contacted and no actual paper/live trade occurred.
61 total unit tests passed on October 20, 2026.

This coordinator is **not** activated by the stream research CLI; integration
into a securely hosted, authorized paper-forward runner remains a separate
acceptance gate. It rejects non-PaperBroker adapters. A real-money adapter
remains absent, by design.


## v0.3 quote coverage (new stacked review)

Added a fail-closed multi-provider source registry/quote-quality gate and
provider adapters for IEX, Tradier consolidated LIVE REST/stream message
parsing, and public Kraken crypto spot order-book research. This is
**market data only**, not multi-broker execution. Read-only Kraken BTC/USD
REST retrieval was verified in a live public request on October 20,
2026; test fixture prices are explicitly labeled synthetic. Tradier
account/tokens and all live-money order transports remain absent.
See [DATA_COVERAGE.md](DATA_COVERAGE.md) and do not treat broad source
support as unrestricted full market coverage, profit evidence, or live
authorization.


## v0.4 local private dashboard (separate stacked review)

Added local-only, zero-subscription HTML/CSS/JavaScript status page and
Python HTTP service, read-only `/api/status` endpoint, explicitly
synthetic/stale/quote-quality labels, hardcoded execution disabled,
strict local Host validation, static asset allowlist and security tests.
The dashboard does not connect to a brokerage account or authenticate
remote users. No actual market-monitoring daemon, mobile app publication,
autonomous broker order routes, customer onboarding or revenue.
It provides an accurate readiness view while Tradier account approval
and paper-forward validation remain prerequisites.
See [DASHBOARD.md](DASHBOARD.md).

## v0.5 Tradier sandbox-only order preview and independent paper broker adapter

An isolated Tradier SANDBOX adapter now constructs native OTOCO brackets
for one-share, max-$20 simulated equity trials. Account/balance/position/order
readback and preview=true checks precede ANY separately armed sandbox write.
A durable account/day idempotency journal blocks repeats and marks uncertain
submissions UNKNOWN. The default CLI and GitHub Actions workflow do not
submit even simulated orders; no real-money transport or continuous runner
has been added. Fill confirmations and OTOCO child-exit activation need
further real broker tests. See [PAPER_LIFECYCLE.md](PAPER_LIFECYCLE.md).
