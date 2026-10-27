# Decisions

| Date | Decision | Notes |
|------|----------|-------|
| 2026-10-07 | Initialized shared workspace | README, WORKSPACE.md, docs/, src/ |
| 2026-10-13 | Consolidate prior chat/thread work into one Master Command Center | `docs/MASTER_COMMAND_CENTER.md` is the canonical non-sensitive cross-thread index. New recurring needs should be folded into the existing master systems before adding duplicate loops/watchers/schedulers. The active ChatGPT Master Command Center conversation is the human-facing control point; GitHub/Floot remain persistent state. |
| 2026-10-27 | Focus development on trading research and original video quality | Keep live trading, publishing, external account changes and expenses behind specific approval gates. Build an offline cash-only paper ledger and extend the owned FFmpeg QA before adding broker connections, new subscriptions or always-on workers. |
| 2026-10-27 | Preserve existing paper research branch in canonical source | Historical-bar strategy and gated Alpaca paper adapter from `feature/zero-cost-paper-trader-20261020` are complementary to the new paper order ledger. Keep both dormant until one integration contract, dedupe/position state and data provenance are verified; reuse existing code rather than creating another bot. |
| 2026-10-27 | Prepare an explicitly read-only sandbox/paper data preflight | Use only official fixed GET endpoints; rely on local environment or opt-in, exact-named macOS Keychain entries. Report only sanitized connectivity status, never keys or accounts. Missing credentials keep broker access unverified; no new order authorization or background worker is implied. |
