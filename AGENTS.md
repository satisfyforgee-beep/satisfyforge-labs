# SatisfyForge agent operating instructions

This file is an entrypoint for coding assistants, ChatGPT Work/Codex, and automation maintainers. It adds **no new scheduler or paid service**. It does not authorize sending, publishing, purchases, trading, or account changes.

## Read first — source of truth
1. `docs/MASTER_COMMAND_CENTER.md`: priorities, identities, state and established operating rules.
2. `WORKSPACE.md` and `docs/CLOUD_FIRST_OPERATIONS.md`: repository and cloud-first conventions.
3. The README and tests for the specific subsystem being changed.
4. `commerce/checkout_registry.json` and `scripts/validate_commerce_safety.py` before touching any commerce path.

These documents record past observations, not proof of present health. Recheck live state before reporting success.

## Objective
Improve existing SatisfyForge operations and paths to legitimate revenue **without an additional paid subscription**. Finish and validate an existing useful project before launching a new project, automation, account, or product. Maintain one canonical command center.

## Allowed unattended work (within available access)
- Read project files, check service status, research public information and identify blockers.
- Write or improve source code, documentation, tests, draft content, and review-ready proposals on short-lived branches.
- Run local/offline tests and non-publishing, read-only smoke tests.
- Summarize verified results, failed checks, required approvals, and next actions.
- Use existing free and authorized infrastructure within its limits.

## Explicit-action gates
Do **not** infer consent from a general instruction such as "continue" or "do everything." Obtain specific approval or use a previously established, still-valid authorization before:
- Sending emails, initiating prospect outreach, publishing posts, releasing games, changing a live checkout, or enabling a live workflow.
- Spending money, starting trials, upgrading plans, subscribing to APIs, moving funds, or placing trades.
- Modifying an external account's identity, access, authentication, payment, tax or banking settings.
- Installing persistent background software on someone else's device or deleting valuable data.

For any live publishing/outreach flow, verify the exact account, inspect existing queues and external state, compute a stable deduplication key, and require the relevant review/authorization gate. Unknown identity or unknown duplicate state means **do not execute**.

## Account and credential boundaries
- SatisfyForge business identity: `satisfyforgee@gmail.com`. Do not use a personal Gmail connection for business messages or CRM work.
- Never put tokens, keys, passwords, session cookies, personal records, financial information or private browser state in this public repository or logs.
- Keep all work on the $0/free path unless the owner approves an exact cost.
- Metricool is retired; do not rebuild dependencies on it.
- Respect third-party terms, MFA, CAPTCHA and verification steps. Do not bypass them.

## Existing architecture — reuse, don't duplicate
- **GitHub**: canonical code, tests, branches and reviews.
- **GitHub Actions**: bounded, repeatable cloud-worker, smoke-test and publisher-check workflows. Keep the direct publisher's fail-closed gate until verified.
- **Floot SatisfyForge Control Center**: owner-facing operations dashboard, browser-job status and review/approval paths.
- **Airtable SatisfyForge Operations**: research ledger, deduplication keys, review queue, content ledger and revenue evidence.
- **Connected Mac via Remote Desktop Commander**: use only for tasks requiring local files or Roblox Studio; preserve any dirty worktree and active development.
- **ChatGPT Work/Codex**: higher-level reasoning and supervised multistep tasks while available. A ChatGPT subscription does not grant a free unlimited API or permanently running model.

Before creating a scheduler, first review existing GitHub Actions, Control Center jobs, and consolidated ChatGPT tasks. Avoid duplicate polling, redundant publishing or repeated failed-login attempts.

## Start-of-run checklist
1. Confirm requested project, current Git branch/worktree status, and applicable authorization gates.
2. Compare repository docs with actual current state from the relevant provider.
3. Identify the highest-impact safe, unblocked improvement: first security/financial/reputation failures; then real leads and valid offers; then content/product work; then deeper game release checks.
4. Make minimal reversible changes on a short-lived branch, without overwriting unfinished human/agent work.
5. Run the smallest meaningful validation: unit/contract tests, preview, read-only browser check, or supported provider readback.
6. Record **verified / prepared / blocked** distinctly. Include links to runs or PRs when available.

## Definition of done
A change is complete only if the relevant test passes and the resulting external state is verified. A successful scheduler run is **not** proof a post was published or a sale occurred. No fabricated sales, performance data, credentials, approvals or deployment status.

## Handoff format
Briefly report: (1) changed and tested, (2) actual external state, (3) blockers/required owner actions, and (4) highest-value next safe task. Keep the master command center current instead of generating redundant reports.
