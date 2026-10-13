# SatisfyForge Creator OS

Creator OS is the owned, zero-cost-first control surface for creator operations. It is intended to reduce dependence on recurring creator SaaS subscriptions by combining useful internal workflows we can lawfully build ourselves.

## Current v1 capabilities

- Local-first command center with no hosting or subscription requirement.
- Original hook/title/caption/structure generator using deterministic templates.
- Publishing queue with status tracking.
- Export into the existing `publisher/queue.json` shape for ready/scheduled items.
- Manual analytics for views, engagement, clicks and revenue.
- $0-first money experiment tracker with buyer, offer, price, spend, revenue and profit signals.
- Owned-tool inventory showing which external subscription categories we are replacing and which modules are still unfinished.
- JSON backup/restore.

## Important boundary

This app does **not** publish directly by itself. The existing `publisher/` project remains the authoritative direct-publishing engine because it has queue validation, duplicate protection, per-platform state and official API adapters. Creator OS only prepares/export queue data.

It also does not store passwords, OAuth tokens, bank details, tax information, customer secrets or reusable browser cookies.

## Run locally

Open `creator-os/index.html` in a modern browser. Data is stored in browser `localStorage` until exported.

## Revenue/productization path

Internal first, customer-facing later. Do not sell this as a finished SaaS until the following are independently verified:

1. Stable hosted deployment and authentication.
2. Cross-device storage/sync.
3. Reliable AI/provider layer or a useful deterministic mode that stands on its own.
4. Social API integrations and duplicate-safe scheduling.
5. Video assembly/QA pipeline.
6. Tenant isolation, privacy/security review and recovery/export flows.
7. Billing, entitlement and fulfillment tests.
8. Truthful pricing and customer support boundaries.

## Next owned modules

Priority is based on recurring cost avoided **and** usefulness to revenue operations:

1. Video Assembly Engine — local/CI FFmpeg pipeline for lawful source clips, narration, captions, resizing, loudness/frame-rate checks and publish-ready exports.
2. Analytics Importers — normalize exports/APIs from connected platforms into one schema.
3. Research Evidence Store — save competitor/platform observations as mechanics and evidence, never copied creative assets.
4. Lead / Reply Workspace — connect Wix intake, business Gmail and existing Lead Rescue tools without creating duplicate outreach loops.
5. SaaS shell — only after the internal product is actually useful enough to justify a paid version.

## Operating rules

- Spend $0 unless an exact charge is explicitly approved.
- Prefer owned/free infrastructure over metered SaaS where practical.
- Use official APIs and legal integrations; do not bypass payment, licensing, platform controls or authentication.
- Reuse successful mechanics, not proprietary code, protected assets, branding, scripts or footage.
- No fabricated analytics, sales or customer claims.
- Existing canonical systems stay authoritative until an owned replacement is tested end to end.
