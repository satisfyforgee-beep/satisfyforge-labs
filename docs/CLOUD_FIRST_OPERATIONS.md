# SatisfyForge Cloud-First Operations

## Goal
Run as much of SatisfyForge as possible without depending on the owner's physical computer.

## Operating rule
Use cloud-capable tools first. Only require the owner's computer when a task truly depends on local desktop software or a local device session.

## Cloud stack

### Browser / websites
- TinyFish is the preferred interactive browser for user-directed website workflows.
- Use saved Browser Context Profiles only when they are confirmed signed in for the target site.
- Never store passwords, tax IDs, bank details, or other secrets in this repository.
- If an account needs owner-only identity, payment, tax, or verification input, record the blocker and continue another cloud-capable task.

### Code / files / automation
- GitHub repository `satisfyforgee-beep/satisfyforge-labs` is the canonical cloud workspace for code, docs, tests, product assets, and automation source.
- Work on short-lived branches, verify changes, and merge into `main`.
- Prefer GitHub Actions or connector-driven cloud validation when it can be done at $0.
- Replit may be used only when the account supports it without a new charge. As of 2026-10-12, creating a new Replit app is blocked by an active-subscription requirement, so do not spend money to enable it.

### Publishing / commerce / outreach
- Prefer the existing connected Buffer, Wix, Payhip-related browser workflows, Hunter/outreach tools, Gmail, and other authenticated connectors before asking for a desktop session.
- Avoid duplicate posts, duplicate products, and repeated retries of the same blocked action.
- Preserve the standing $0 rule unless the owner explicitly approves a specific charge.

## Task classification

### Cloud-capable now
- GitHub code and documentation changes
- Publisher development and automated tests
- Website/source maintenance that can be done through GitHub or connected web tools
- Social scheduling/publishing through connected services
- Payhip product copy and storefront/browser work when authenticated
- Outreach research and sequence monitoring
- Gmail/Google web tasks where an authenticated connector/profile is available
- Research, content planning, productization, and monetization analysis

### Cloud-capable after one-time sign-in
- Browser workflows for sites whose TinyFish profile exists but does not yet show a saved authenticated session
- Amazon/KDP web steps that are not owner-only identity/tax/banking actions
- Roblox website/dashboard steps that do not require Studio

### Local-only / desktop-dependent
- Roblox Studio play testing
- Mobile/emulator tests that require software installed on the owner's machine
- Any proprietary desktop-only application with no connected cloud/browser interface
- Hardware/device-specific checks

## Current browser-profile status (2026-10-12)
- SatisfyForge Gmail: saved Google sign-in is present.
- Default profile: exists but no confirmed signed-in sites are recorded.
- SatisfyForge Business Gmail ONLY: profile exists; no saved signed-in sites are recorded.
- SatisfyForge Social Direct: profile exists; no saved signed-in sites are recorded.
- SatisfyForge Amazon KDP: profile exists; no saved signed-in sites are recorded.
- SatisfyForge Roblox: profile exists; no saved signed-in sites are recorded.

## Failure policy
When any task is blocked by login, verification, a local-only program, account limits, unknown cost, or a paid feature:
1. Record the blocker once.
2. Do not buy or start anything paid without explicit approval.
3. Do not repeatedly retry the same unresolved blocker.
4. Immediately continue the highest-value cloud-capable task.

## Definition of done
A task may be called complete only when its real external state is verified. Prepared, queued, pending, or blocked work must not be described as live or finished.
