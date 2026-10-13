# SatisfyForge Owned Tool Stack

Status date: 2026-10-13

This file tracks the SatisfyForge-owned alternatives that reduce dependence on recurring creator/business SaaS while preserving truthful status boundaries. It complements `docs/MASTER_COMMAND_CENTER.md`; the Master Command Center remains the top-level operating index.

## Operating rule

Build internal capability first. Productize only after the internal workflow is genuinely useful and tested. Spend $0 unless the owner approves an exact charge. Use official APIs and legal integrations; do not bypass subscriptions, authentication, licensing, payment, platform controls or access restrictions.

## Verified / merged owned modules

### Creator OS

Repository: `creator-os/`

Merged 2026-10-13 through PR #19.

Current capabilities:
- local-first creator command center
- original hook/title/caption/structure package builder
- publishing queue and status tracking
- export into the existing Direct Publisher queue shape
- manual views/engagement/click/revenue analytics
- $0-first money experiment tracker
- owned-tool replacement inventory
- JSON backup/restore

Boundary: Creator OS prepares data but does not itself claim publishing success. `publisher/` remains authoritative for actual platform writes, queue validation and duplicate protection.

### Video Assembly Engine

Repository: `video-engine/`

Merged 2026-10-13 through PR #20.

Current capabilities:
- FFmpeg/ffprobe based zero-cost rendering and QA
- 1080x1920 normalization
- forced constant 30 fps output
- H.264 / yuv420p / fast-start MP4
- optional voiceover replacement and loudness normalization
- optional burned SRT/ASS captions
- post-render QA that fails closed on format errors

Local validation before merge: 4 unit tests passed.

This directly addresses the prior class of social-publisher `frame_rate_check_failed` errors without buying another video-normalization subscription.

### Direct Publisher

Repository: `publisher/`

Status from the Master Command Center: owned queue/state engine, duplicate protection and direct Instagram, Facebook, YouTube and TikTok adapter work exist. Actual platform publishing still depends on each platform's official authorization and approval requirements.

### Mail Bridge

Repository: `mail-bridge/`

Status from the Master Command Center: core Gmail API semantics, sender allowlist and idempotency are tested/merged. Live OAuth/UI deployment remains pending the existing Floot free-build reset path. Never store reusable Gmail credentials in this public repository.

### Owned Cloud Browser

Repository: `browser-runner/`

Status from the Master Command Center: GitHub Actions + Playwright/Chromium public-site worker and Control Center result loop are verified. Authenticated third-party automation remains subject to safe-session/provider constraints.

## Next build priorities

Prioritize modules that either eliminate a recurring paid dependency or shorten the path to real revenue.

1. **Video Engine v2 — multi-clip timeline**
   - JSON scene manifest
   - clip trimming/order
   - transitions kept simple and deterministic
   - background-bed mixing/ducking
   - title/lower-third templates
   - thumbnail/frame extraction

2. **Analytics Import Layer**
   - normalize platform exports/API responses into one schema
   - compute view-to-engagement, click-through, revenue-per-1k-views and content-family performance
   - separate observed data from inferred recommendations

3. **Research Evidence Store**
   - retain competitor/platform observations as reusable mechanics: hook, pacing, payoff, offer, CTA, distribution and monetization path
   - store links/evidence and dates
   - never store copied creator scripts, footage or protected creative assets as templates

4. **Lead / Reply Workspace**
   - coordinate Wix lead intake, business Gmail replies, Hunter outreach status and scoping kits
   - do not create duplicate outreach loops or use personal Gmail
   - preserve truthful scopes and verified payment/fulfillment boundaries

5. **Creator OS hosted/SaaS shell**
   - only after internal usefulness is proven
   - accounts, cross-device sync, tenant isolation, security/recovery, billing and entitlements
   - no paid checkout until fulfillment and entitlement behavior are transaction-tested

## External tools that remain temporary bridges

Buffer, Metricool, Wix social tooling, Hunter, Payhip and other connected services may remain useful while their owned replacements are incomplete. Do not remove a working bridge until the replacement is tested end to end.

## Revenue productization candidates

The strongest software-product candidates are the tools that solve repeatable pains already encountered internally:

- Creator OS for creators/small businesses
- Direct Publisher / publishing workflow for teams that want a simpler owned queue
- Video technical QA/normalizer for short-form creators
- Lead Rescue + reply workflow for local businesses
- analytics/experiment tracker focused on revenue rather than vanity metrics

A candidate becomes sellable only when there is a specific buyer, a clear outcome, a supportable price and verified delivery/fulfillment.

## Truth boundary

Do not report a module as live, profitable, customer-tested or fully automated unless that exact state has been independently verified. Repository merge, unit tests, local smoke tests, platform authorization, live deployment, customer purchase and successful fulfillment are separate milestones.
