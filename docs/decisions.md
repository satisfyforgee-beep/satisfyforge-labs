# Decisions

| Date | Decision | Notes |
|------|----------|-------|
| 2026-10-07 | Initialized shared workspace | README, WORKSPACE.md, docs/, src/ |
| 2026-10-13 | Consolidate prior chat/thread work into one Master Command Center | `docs/MASTER_COMMAND_CENTER.md` is the canonical non-sensitive cross-thread index. New recurring needs should be folded into the existing master systems before adding duplicate loops/watchers/schedulers. The active ChatGPT Master Command Center conversation is the human-facing control point; GitHub/Floot remain persistent state. |
| 2026-10-27 | Focus development on trading research and original video quality | Keep live trading, publishing, external account changes and expenses behind specific approval gates. Build an offline cash-only paper ledger and extend the owned FFmpeg QA before adding broker connections, new subscriptions or always-on workers. |
