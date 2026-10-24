# SatisfyForge Trading Lab v0.6 — Read-only sandbox order supervisor

**Status:** Built and offline-tested. This is NOT an active trading bot, real
money or paper order submitter, scheduled GitHub bot, public website, hosted
service, or a profitable trading strategy. The private monitor remains OFF
until its owner intentionally runs it with a SANDBOX token and a real
SANDBOX order ID.

This update stacks on the existing v0.5 Tradier sandbox order builder and
the v0.4 local dashboard. It adds strict *independent* brokerage order and
exit reconciliation, a bounded owner-operated GET-only monitor, and
sanitized heartbeat integration in the **existing** SatisfyForge dashboard.

## What this version verifies

The entry order, the user's positions, and both linked protective exits
are separate evidence. The original broker receipt is NOT treated as a
fill. The reconciler requires an exactly identified parent order and two
independent child order GETs, with a broker-provided parent link on the
order-list record AND on the exact child record. It does not "guess"
association based on symbols or similar trade times. Before declaring a
position protected, it checks:

- Parent ID, stock symbol, side, executed quantity, and status;
- Exactly two child orders with IDs distinct from the parent;
- Each child has a matching broker-provided `parent_id` OR
  `parent_order_id` field, a one-share **sell** quantity and the
  expected stock symbol; contradictory link fields are not accepted;
- One positive-priced limit target and one positive-priced stop;
- Both child statuses are open or pending when one share is held;
- A closed position requires one fully filled exit, the other
  canceled, and zero remaining shares.

The statuses are `AWAITING_ENTRY`, `ENTRY_NOT_FILLED`,
`PROTECTED_PAPER_POSITION`, `CLOSED_PAPER_POSITION`, and
`HALT_AND_RECONCILE`. Incomplete, contradictory, partial, or
unavailable evidence *halts*. The existing v0.5 trader remains
paper-POST-disabled until separately armed.

**Actual sandbox OTOCO group schema verified, October 21, 2026.**
Tradier returned one composite `class=otoco` order group, with an
embedded `leg` ARRAY of exactly three order records. The group itself
has no top-level `symbol`, `quantity`, or `exec_quantity`; those live
on the child legs. This explains why the earlier simple-order readback
failed. The grouped-order schema was independently fetched using GET
only and verified against a one-share sandbox position. The reconciler
now detects native composite groups and checks each of its three
broker-reported legs and the account position. **This confirms the
test fill/protective legs at the inspection time, not permanent
protection or guaranteed stop-price execution.** Additional session,
partial-fill, expiration, restart, and live-data tests remain required.
Evidence: https://github.com/satisfyforgee-beep/satisfyforge-labs/actions/runs/39621609697 .

## Run offline tests ($0, no broker secrets)

```bash
cd algo-trading
python3 -m unittest discover -s tests -q
python3 -m compileall -q zerocost_bot/tradier_reconciliation.py zerocost_bot/paper_supervisor.py tradier_watch.py
```

The monitor has no test-fixture order IDs embedded, no trading endpoint,
and cannot operate without an existing sandbox order.

## Owner-operated paper monitor (later)

On the Mac **after** a separately authorized real SANDBOX order exists
and a SANDBOX credential is securely present in the local process
environment (never paste it into chat or GitHub source):

```bash
cd algo-trading
python3 tradier_watch.py --order-id <SANDBOX_ORDER_ID> --symbol SOFI
```

This does **ONE** read-only reconciliation and writes
`~/.satisfyforge/trading/paper_order_status.json` with owner-only
filesystem permissions. The report contains no order IDs, customer data,
API credentials, raw broker payloads, or secret tokens.

Every successful poll also appends the same sanitized state to
`paper_order_journal.jsonl` in that owner-private directory. The journal:

- is mode `0600` inside the mode-`0700` status directory;
- uses a monotonic sequence and SHA-256 link to the prior event;
- validates the complete chain before every append and refuses a truncated,
  edited, symlinked, oversized, or schema-expanded file;
- fsyncs each bounded append before monitoring continues;
- contains no account/order identifiers, broker response, signal, token,
  executable action, or enabled trading flag.

This makes lifecycle changes and outages auditable during forward-paper
testing. It is **tamper-evident, not magically immutable**: an owner with
filesystem access can replace the whole directory, and loss of the computer
still loses the local log. A journal integrity failure stops the watcher
rather than starting a new chain or erasing evidence.

To monitor while the **owner-controlled computer and this terminal
remain running**:

```bash
python3 tradier_watch.py --order-id <SANDBOX_ORDER_ID> --symbol SOFI --watch --interval 15 --max-polls 120
```

- Polling is bounded to 10–60s minimum/maximum and 720 polls maximum.
- A filesystem lock prohibits duplicate simultaneous watchers on this
  computer. This is not a distributed cloud lock.
- Broker timeouts, unknown statuses, missing exits, child mismatches,
  inconsistent position quantities and any unexpected action field
  **halt immediately without automatically retrying**.
- The loop ends when a bracket is closed, rejected, cancelled or expired.
- Ctrl+C stops the local process. There is NO daemon/autostart or cloud
  uptime guarantee. If the Mac sleeps, no further monitoring happens.
- A stock-specific order could still be exposed to gap losses, unfilled
  stops, rejected broker exits, and erroneous data. The watcher **does
  not automatically repair or cancel orders**.
- No order placement (paper or live) is supported by this CLI.
- Tradier SANDBOX market data is delayed ~15 minutes. It MUST NOT be
  used as real-time live execution signals.

## Existing local dashboard integration

The original local dashboard now accepts an **optional** private
monitor status path:

```bash
cd algo-trading
python3 dashboard_server.py --monitor-report "$HOME/.satisfyforge/trading/paper_order_status.json"
```

Open `http://127.0.0.1:8765/` on the **same computer**.

- The dashboard is LOCAL ONLY, unauthenticated, read-only and not
  publicly available on your phone or the internet.
- The status API receives only allowlisted fields and a timestamp.
- A heartbeat older than 30 seconds shows `STALE`, never "running".
- The original stock/crypto research feed status is independent from
  the optional broker/order monitor.
- No broker account, production host or trade permission is supplied to
  the dashboard server.

## Remaining gates before live money

1. Test ONE explicitly approved SANDBOX order, independently confirm
   parent/child identifiers, all transitions, and reversals/partial fills.
   No user trading funds are at risk in SANDBOX.
2. Prove persistence, continuity, recovery, alerting, market calendar,
   and child-order safeguards across realistic faults and disconnections.
   The current bounded local monitor alone is NOT always-on execution.
3. Integrate quote provenance, licensed consolidated live data, research
   agent coordination and risk budgets. Store account secrets only in a
   secure owner-managed runtime, never browser JS/GitHub code.
4. Record meaningful **forward paper** sample performance, not just
   offline code tests. Include bid/ask spreads, network latency,
   broker-rejected orders, slippage, exchange fees and adverse exits.
5. Separately review broker approval, cash versus margin, allowed options
   level, live funding, exact personal spend limits, kill switch and
   trade authorization before adding any REAL-money order routes.
6. Commercial customer accounts require secure hosting, per-user
   permissions, data licensing and securities-regulatory advice. This
   private research UI must not be marketed as a proven automated
   trading product.

Reference: https://docs.tradier.com/docs/trading and
https://docs.tradier.com/reference/brokerage-api-accounts-get-account-order

All live-money and automatic order-write capabilities remain OFF.
