# SatisfyForge: stock + long-option historical virtual trading experiment

Verified October 26, 2026, after the US regular market close. Research ONLY.
The trading account is not linked to an active broker execution route.
No paper-broker, crypto exchange or live-money orders were placed.

## What was actually practiced

- Read Tradier SANDBOX historical 5-minute stock OHLC/volume bars for F, AAL, CLF for the complete October 26 regular trading session.
- Predeclared stock control: simulated purchase of exactly one share of each stock at its 10:00 a.m. ET historical open plus $0.01 friction, simulated $0.01 fee each side, conservative 2% stop/3.5% target or latest 15:55 five-minute closing-bar exit, with stop-first when both thresholds touch a bar. Entries <= $30. Outcome: 3 completed historical virtual trades, net -$0.46 on an independent hypothetical $150 account.
- Also replayed the already tested fixed-rule long-only stock volume-breakout PaperEngine against the same three stock feeds (15-minute-lookback logic implemented through 5-minute bars with 12-bar lookback, not an optimized trade signal). It produced ZERO trades, net $0.00. Choosing not to trade can be the right control outcome.
- Read historical daily option premiums for AAL261106P00011500 and F261106C00013000, Oct 1-26, both expiring Nov 6. Simulated one long option contract per selected predeclared every-fourth historical session where the entire entry premium x100 plus $0.65 per-contract fee fit within $30. Modeled entry premium as that day's OPEN+0.01, and exit as CLOSE-0.01, plus $0.65 exit fee. Same-day virtual closes, no overnight exercise/assignment in this model. Approximate T+1 availability across distinct trading sessions rather than same-day reinvestment.
- Actual output: FIVE completed historical long-option round trips, ONE profitable, total net simulated loss -$15.50 on a DIFFERENT independent $150 virtual account. Daily OHLC does not contain actual executable bid/ask quotes; this is a control exercise, not reliable option execution P/L.

The file with complete historical observations and events is in the Mac owner-private local directory at ~/.satisfyforge/trading/stock_option_history_virtual_20261026T222317Z.json with 0600 permissions. Nothing was posted to a broker and account or API tokens were not logged.

## Commands on Mac

In the branch under /Users/leighannbatze/SatisfyForge/worktrees/stock-option-virtual-history-20261026/algo-trading:

The tests can run without a secret:
  python3 -m unittest discover -s tests -q

To repeat the read-only historical fetch/replay, place only the Tradier SANDBOX token in the local process environment and run:
  python3 stock_option_history_trial.py

Do NOT put sandbox tokens in repository, chat, shared files or CI logs.

## What this DOES NOT mean

These are historical virtual fills, not user-confirmed live market trades.
Each type is evaluated with its own independent historical cash account.
DO NOT ADD these simulated balances to the 87 closed historical crypto trades
or to the three OPEN forward virtual Kraken crypto positions.

AAL / Ford cheap options do not necessarily offer a good expected return;
small premium contracts may be very far out of the money. True options paper
execution needs current market spreads, Greeks/time decay, expiration and
assignment controls, mock and sandbox parity, and separate broker authorization.
Tradier SANDBOX quotes are delayed about 15 minutes. That limitation remains
even if an order is accepted in its paper environment.

The pre-existing one-share SOFI Tradier SANDBOX position still requires exact
historic exit-order reconciliation. Historical data GETs neither repair nor
cancel this position. Real-money trading remains permanently disabled unless
separately and explicitly authorized after forward testing and risk review.
