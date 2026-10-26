# SatisfyForge: real-price historical replay and forward virtual paper practice

Status October 26, 2026: OFFLINE VIRTUAL simulation ONLY. No exchange, Tradier, Alpaca, Robinhood, or actual paper-broker order was submitted. No real money, credentials, brokerage funds, or real positions touched.

## Results already verified

- Real historical Kraken public 15-minute completed OHLC bars for BTC/USD, ETH/USD, SOL/USD. Last forming bar excluded; aligned only on complete common UTC intervals.
- Three precommitted strategies: scheduled control, volume breakout and reversal. Development 70% and isolated held-out 30%, with distinct $150 hypothetical starting accounts. Next-bar-open modeled fills; 0.4% modeled taker fee each side, 0.05% slippage each side; 2% stop, 3.5% target, four-hour maximum holding period. OHLC stop-target collisions assume stop first.
- First historical replay: 87 CLOSED virtual crypto trades in total. All three strategy results were NEGATIVE after modeled costs. No strategy is cleared for brokerage-paper or real-money execution. Private original history file: ~/.satisfyforge/trading/crypto_real_history_replay_20261026T220400Z.json
- Started THREE separate forward virtual crypto positions (BTC/USD, ETH/USD, SOL/USD), each approximately $15 debit including modeled fees, in a single new $150 offline virtual account. The private ledger is ~/.satisfyforge/trading/crypto_virtual_forward.sqlite3. At first readback, $105.09 remaining virtual cash, three crypto positions, zero realized P/L, estimated whole-account liquidation $149.60. These are MODEL FILLS and must not be called broker-paper executions.
- A subsequent one-shot script reads current Kraken public quotes and checks software-only 2% stop / 3.5% target / 24-hour maximum hold, recognizing profits or losses after model fees if a modeled exit occurs. Crypto stop is not resting at any exchange. Outages and gaps can exceed thresholds. Event IDs prevent duplicate entries; the trial allows only three lifetime virtual buys.

## How to run on the connected Mac

From the dedicated trading branch folder:
  cd /Users/leighannbatze/SatisfyForge/worktrees/multiasset-historical-trial-20261026/algo-trading
  python3 crypto_virtual_runner.py --check
  python3 crypto_historical_trial.py
  python3 -m unittest discover -s tests -q

Each historical rerun creates a NEW owner-private file. Cross-asset virtual portfolio checks only run when invoked; there is no newly installed background monitor.

## To finish the user's full vision

1. Stocks: reconcile the existing October 21 SOFI Tradier SANDBOX paper-share exit history before any new Tradier broker writes. Current-session zero orders does NOT prove historical OTOCO exits never existed. The already installed separate 15-minute Tradier stock virtual forward QA experiment is NOT this account; never merge its profit with our new $150 portfolio.
2. Options: delayed Tradier sandbox chain is accessible, and a read-only Oct 26 scan saw November 6 AAL/F contracts priced under $30 before fees. None is a recommended purchase. Market is closed, so options virtual forward execution must wait for a market-session-validated quote. Verify spread, liquidity, contract multiplier, expiration/assignment and 100% premium-loss risk, not just the low price.
3. Crypto broker-paper simulation: attach eligible PAPER ONLY account at Alpaca and separately verify that account and its permissions before attempting authenticated paper orders. Public Kraken prices are NOT connected broker fills.
4. Integrate broker-verified fills, fees and settlement into the existing tested offline PaperCapital ledger. Add independent risk gates, controls for session, liquidity, duplicate orders, partial fills, cash restrictions, and transparent max daily drawdown.
5. Use longer, predeclared and genuinely forward trials, with reporting against cash/no-trade and passive baselines. A profitable short backtest is not proof of predictable future gains. Current strategies lost.
6. Install a bounded scheduled runner on this shared Mac only with the owner's permission. The current crypto forward check is not unattended; the machine may sleep or disconnect.

This work is for fake-money research; NO actual brokerage paper trades were added, NO real trades, and NO supported claim of profitability.