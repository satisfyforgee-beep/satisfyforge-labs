# Crypto Virtual Monitor — bounded macOS schedule

Installed on October 26, 2026 with the user's explicit permission. The monitor observes the existing BTC/USD, ETH/USD and SOL/USD virtual crypto positions every approximately 900 seconds while the Mac is awake and the user is logged in. The macOS job label is com.satisfyforge.crypto-virtual-monitor.

The monitor code is crypto_virtual_monitor_once.py. The scheduled action always invokes the one-shot crypto_virtual_runner.py check path. It never opens new positions or accesses broker or real-money trading endpoints. Market inputs are publicly available Kraken order-book snapshots. The paper entries and exits are local mathematical estimates, not actual exchange fills.

The service writes an owner-private limited-size log in the SatisfyForge trading directory, and uses the existing durable virtual portfolio SQLite ledger. The log summarizes current virtual cash, estimated liquidation value, count of open positions, modeled realized profit/loss and any error class, without copying API responses or credentials.

Failure policy: no ledger, incorrect lifetime buy count, incomplete quotes, excess spread, invalid timestamps, unexpected inventory or unknown broker activity must halt the check. Existing positions and past journal events are preserved. If all three virtual positions close, future checks stop requesting public prices.

This is a local user-session macOS background job, not a cloud service. The Mac may sleep, disconnect or lose network connectivity, so exit targets and stop levels are never guaranteed.

The separate existing Tradier stock virtual QA monitor and unresolved single SOFI Tradier Sandbox position are unaffected by this installation. No additional brokerage-paper trade permissions or real-money orders are enabled. The only actual authorization here was for monitoring these three previously opened local virtual positions.

Installed LaunchAgent definition: ~/Library/LaunchAgents/com.satisfyforge.crypto-virtual-monitor.plist
User-private audit log: ~/.satisfyforge/trading/crypto_virtual_monitor.jsonl
User-private virtual ledger: ~/.satisfyforge/trading/crypto_virtual_forward.sqlite3
