# Rift Raiders v0.31 — Real Furnished-House Blinds and Courier Pickup Fix

**2026-10-21 · Private candidate; NOT a public Roblox release**

## Changes
- The two original detailed furnished Suburban template houses now have **21 functioning window-blind assemblies** with **422 retained original slats**. Real slats animate with server-driven TweenService. Multiple players see the same physical state. Actions require a living nearby avatar and are rate-limited.
- The existing courier pickup prompt advertised 8 studs but the server previously denied interactions beyond 6; the server radius now matches its prompt. Rewards remain server-validated and nonduplicate.
- Game version attribute, ready print, and Studio smoke assertion now identify the integrated build as **v0.31.0** instead of stale v0.30.0.
- Original furnished-house models, 20 room-light circuits, secure doors, traffic, cars, jobs, and progression are retained. No new purchases, imports or third-party scripts.

## Verified integration history
- PR #76: https://github.com/satisfyforgee-beep/satisfyforge-labs/pull/76 was squash-merged into the private feature/rift-raiders branch at commit 868315e.
- Initial feature isolated branch and real Roblox Studio smoke/two-player tests passed. Fresh integrated v0.31.0 checks are recorded in V0_31_QA.md.
- Previous Mac worktree contains unrelated uncommitted content and historical game artifacts. Integration uses a new clean worktree, leaving originals untouched.

## Release gates remain open
This is NOT a claim of public release, real-player enjoyment or retention, licensed asset completeness, or measured low-end phone FPS. Still require human furnished-room/stairs traversal, actual iOS/Android testing, private DataStore leave/rejoin, source asset compliance review, multi-user playtests, and owner approval before publishing. See SHIP_CRITERIA.md.
