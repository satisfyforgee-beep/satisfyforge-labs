# Tradier delayed-quote forward execution QA — bounded control experiment

**Status:** Zero-dollar automated *virtual* research, not paper-broker orders or a strategy with proven edge. The 2026-10-26 checked-out research branch extends draft PR #72. It does **not** merge or alter the separate Tradier sandbox OTOCO position/exit workflow (PRs #74 and #82).

## Scope and authority

- Start with **at most five** lifetime BUY entries across up to five US stock/ETF symbols; maximum **$30 simulated debit per entry**, **$150 starting virtual cash**, whole shares, no margin, leverage, shorts, options or broker POST endpoints.
- Delayed Tradier SANDBOX quotes are used only to estimate synthetic bid/ask entries and exits; simulated fills are **not Tradier paper fills**, guaranteed prices, current executable NBBO or trading recommendations.
- Baseline policy ranks **spread and quote usability** to test execution/accounting mechanics. It is **not** a directional alpha signal. Do not promote it to real-money execution or claim profit.
- Each virtual buy estimates ask + $0.01/share slippage + $0.01 fee. Exits use bid - $0.01/share slippage - $0.01 fee. A 2% bid stop and 3.5% bid target are virtual checks, not broker-native protection; gap losses can be greater. If a late-session quote is valid at/after 15:40 New York time, exit the virtual position for session end. If laptop sleeps, a stale quote fails closed and the virtual position may stay open.
- Each BUY/Sell is timestamped with the **delayed quote** observation time and system check time, recorded in a private atomic JSON state file. Runs are locked, replay-safe and duplicate entries in the same symbol are forbidden. The five-entry trial does not reset or silently roll forward into unlimited trades.
- The existing October 21 SOFI sandbox brokerage position is separately unresolved; SOFI is excluded from the virtual control experiment by default. No new broker-submitted paper orders are authorized or attempted by this module.

## Verify locally

From the branch root:

```bash
python3 -m unittest discover -s tests -q
python3 -m compileall -q scripts/tradier_forward_qa.py
/bin/zsh -n scripts/run_tradier_forward_qa.sh
```

Mac runner uses an existing macOS Keychain item `satisfyforge-tradier-sandbox` in the logged-in account, never a token file or a hardcoded token. When logged in and awake, user LaunchAgent `com.satisfyforge.tradier-forward-qa` starts the foreground one-shot runner **approximately every 15 minutes**. It is not reliable while the Mac sleeps, Keychain is inaccessible, networking fails, or Tradier is unavailable. An OS login-session job is **not a hosted 24/7 service**.

State: `~/.satisfyforge/trading/forward_execution_qa.json`.
Local log: `~/.satisfyforge/trading/forward_qa_stdout.log`.
The state/log directory is private, owner-only. No token/account number is recorded.

Control/disable installed scheduler without deleting the book:

```bash
launchctl print "gui/$(id -u)/com.satisfyforge.tradier-forward-qa"
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.satisfyforge.tradier-forward-qa.plist"
```

**Critical boundary:** Existing Tradier GET /orders is *current-session only*, so zero orders seen Oct 26 does **not** independently prove the prior Oct 21 OTOCO exits never existed. Existing SOFI broker position cannot be declared protected without exact-order reconciliation; do not use this virtual book to modify or clear it.

## Next gates

1. Collect independent forward delayed-quote observations across market sessions and audit virtual fills, missing polls, spread costs and loss excursions; compare to a no-trade baseline. Reports should include losing outcomes and failures.
2. Resolve sandbox SOFI old-order and protective-exit state separately, from exact historical order ID if available; never infer previous-day order status from today's order list.
3. Only after broker-specific, position-aware, multi-symbol, cash-only risk gates and OTOCO exit checks are independently tested, consider converting controlled virtual entries into actual Tradier SANDBOX submissions. Live brokerage remains entirely unavailable and disabled.
