# SatisfyForge Master Command Center

This file is the canonical non-sensitive operating index for work that used to be spread across multiple chats and threads. The active ChatGPT Master Command Center conversation is the human-facing control surface; this file is the persistent project-facing source of truth.

## Core operating rules

- One command center, not one automation per thread.
- Fold new work into an existing system before creating another loop, watcher, scheduler, repository, site, or dashboard.
- Keep duplicate, superseded, test, or one-time automations paused.
- Spend $0 unless the owner explicitly approves an exact charge.
- Prefer owned/free infrastructure over metered browser tools or paid SaaS when practical.
- Maximize automation and minimize manual owner steps. Reserve owner actions for genuine login, identity, tax, bank, MFA, legal, hardware, or desktop-only requirements.
- Never expose credentials, browser cookies, bank details, identity documents, private tokens, or personal data in this public repository.
- Never call an unverified checkout, post, product, game, integration, or external state complete.
- When one path blocks, record the blocker once and continue the highest-value unblocked work.

## Canonical operating stack

### Master operations
- ChatGPT Master Command Center conversation: canonical human instruction point.
- SatisfyForge Control Center: https://satisfyforge-control.floot.app
  - Persistent owner-facing operations dashboard.
  - Floot-managed database.
  - Owner authentication.
  - Browser job history and system status.
  - Tokenless GitHub OIDC worker integration verified.
- GitHub repository: `satisfyforgee-beep/satisfyforge-labs`
  - Canonical code, docs, tests, browser worker, publishing infrastructure, monetization assets, and operating records.

### Owned cloud browser
- `browser-runner/` contains the SatisfyForge Playwright/Chromium browser runner.
- GitHub Actions provides the primary zero-cost cloud browser worker.
- Tokenless Control Center -> GitHub Actions OIDC -> Chromium -> Control Center result loop is verified.
- Prefer this system over paid/metered browser services where supported.
- Public-site automation works.
- Local repository HTML can also be smoke-tested through `browser-runner/src/local-tasks.mjs`; Forge Frenzy is the first recovered game validated that way.
- Authenticated third-party site automation remains subject to secure-session and provider/security constraints; do not store reusable login cookies or passwords in the public repo.

### Owned business mail
- Paid Superhuman Mail was explicitly rejected and must not be suggested as the solution.
- The owned SatisfyForge Mail Bridge is implemented and live in the Control Center at `https://satisfyforge-control.floot.app`.
- It uses Floot-brokered Google OAuth, an exact `satisfyforgee@gmail.com` sender allowlist, admin-only controls, atomic queue claims, sanitized failures and non-resendable `sent` rows.
- No Gmail password, reusable OAuth token or refresh token belongs in GitHub or the app's own tables.
- Two approved advisor messages remain queued and unsent until the owner connects exactly `satisfyforgee@gmail.com` through the Control Center.
- `docs/MAIL_BRIDGE.md` is the implementation contract and verified-state record.
- One-to-one advisor mail should use the owned bridge after the approved account connects; Hunter remains for legitimate prospecting sequences.

## Revenue and sales

### Payhip
- Payhip is the primary $0-first digital storefront.
- Existing products should be reused/improved before creating near-duplicates.
- Payment routing preference: Payhip/PayPal where verified.
- Never expose Chime/bank details to customers.
- 2026-10-16 signed-out Chrome verification confirmed the public Tool Vault plan at **$49**, but the offer remains **quarantined** because default Payhip membership-template copy is still publicly visible and completed checkout/automatic fulfillment are not transaction-tested.
- 2026-10-16 signed-out Chrome verification also confirmed public Payhip pages for Lead Rescue Sprint at **$299** and Custom Platform / Licensing at **$5,000**. Both remain **quarantined** because they still expose default Payhip coaching-template content; do not promote or route customers to those checkout pages yet.
- Keep quarantined offers on the safe Wix request/form flow until authenticated Payhip seller identity is verified, placeholder copy is replaced with reviewed SatisfyForge-specific copy, and the relevant checkout/fulfillment or service handoff is deliberately tested.
- `commerce/checkout_registry.json` is the canonical machine-readable quarantine list. `scripts/validate_commerce_safety.py` blocks quarantined checkout URLs from customer-facing and automation surfaces.

### Verified digital offer
- Strange True Story Shorts Creator Kit: `https://payhip.com/b/MSLBK`.
- Latest signed-out public verification on 2026-10-16 showed $7.99, correct product title, Add to Cart / Buy Now controls and ZIP disclosure.
- Completed payment and automatic fulfillment have not been transaction-tested; do not claim otherwise.
- A later GitHub-cloud browser check was blocked by Payhip/Cloudflare 403 before page load; this is a runner-access limitation, not evidence the product disappeared.
- Canonical status: `docs/CREATOR_KIT_STATUS.md`.
- Canonical organic campaign asset: `sales/CREATOR_KIT_ORGANIC_LAUNCH_PACK.md`; promotion claims remain constrained by the untested completed-payment/automatic-fulfillment gate.
- First-sale conversion, buyer FAQ, support replies and controlled checkout evidence checklist: `sales/CREATOR_KIT_FIRST_SALE_CONVERSION_KIT.md`.

### Service sales / local business
- Active offer families include:
  - Home Service Lead Rescue
  - Lead Follow-Up Automation
  - Gym Membership Growth
- Hunter business sender: `satisfyforgee@gmail.com`.
- Active Hunter sequences:
  - 904604 — Home Service Lead Rescue - Eastern Window
  - 904608 — Lead Follow-Up Automation - Eastern Window
  - 904610 — Gym Membership Growth - Eastern Window
- Older 904584 / 904585 / 904586 are paused test sequences.
- Current sending account is active; do not create duplicate outreach sequences for the same offer/audience without evidence the existing ones are exhausted.
- 2026-10-13 live sending-window diagnosis: `docs/OUTREACH_AUDIT_2026-10-13.md`.
- Wix request/form flow remains the safe intake route while checkout verification is paused.
- `sales/OUTREACH_REPLY_FULFILLMENT_KIT.md` contains the response/sample system.
- `sales/SCOPING_AND_CLOSE_KIT.md` contains truthful offer boundaries, qualification and close/scoping rules so an interested prospect can move to written scope without invented results or an unverified payment link.

### Business communications identity gate
- Business identity: `satisfyforgee@gmail.com` only.
- Do not use the HubSpot portal connected through `cougarboy1999@gmail.com`, even read-only. It is blocked until HubSpot is reconnected or recreated under the business identity.
- The currently connected ChatGPT Gmail connector also resolves to `cougarboy1999@gmail.com`. Do not search, read, draft, send, label, or otherwise use that mailbox for SatisfyForge. It is blocked until the connector is explicitly reconnected under `satisfyforgee@gmail.com` and the profile identity is reverified.
- Quo is connected to the business identity but currently has zero phone inboxes/numbers. Do not attempt SMS or calls until `list-inboxes` returns a usable business number.

## Website and funnel

### Wix Growth Toolbox
- Canonical live site is the existing free Wix Headless deployment.
- Preserve the full production file set on every redeploy; do not rebuild from only the smaller historical repo subset.
- Follow `docs/LIVE_WIX_SITE_INVENTORY.md` before updating the site.
- Wix Forms is the live lead intake source.
- 2026-10-14 live verification: one enabled form, `SatisfyForge Growth Request` (ID `7632c6db-2dec-4fdc-ace7-3dd72ad81478`), is present with advanced spam protection and required email, business/project name, price-range interest and problem-description fields. The submission query returned **0 submissions**. The intake mechanism is configured; traffic and qualified response generation are the current bottlenecks.
- Tool Vault purchase CTAs remain in a safe paused/request state. The $49 public price is now verified; the remaining blockers are unfinished public page copy, authenticated seller-identity verification, and transaction/fulfillment verification.
- Lead Rescue Sprint ($299) and Custom Platform / Licensing ($5,000) are also quarantined from direct promotion because their public Payhip pages still show default coaching-template copy.
- The historical repository copies of `satisfyforge-site/index.html` and `pricing.html` remain configured so a future source-based deployment does not expose quarantined Payhip checkout links.
- Do not restore direct checkout CTAs until the corresponding `commerce/checkout_registry.json` entry is no longer quarantined after review and verification.
- The owned Chromium worker has passed a full production-page smoke test plus the payment-link safety check.


### Search visibility
- Business Search Console is connected under the approved identity `satisfyforgee@gmail.com` for the canonical Wix host.
- 2026-10-14 audit: the sitemap was accepted without warnings/errors (15 submitted URLs), but Search Console reported 0 indexed URLs and 0 impressions/clicks. The homepage was fetched successfully with indexing allowed and a self-canonical, then classified `Crawled - currently not indexed`; Lead Rescue, Revenue Audit, and ROI Calculator were still unknown to Google.
- This is an acquisition blocker, not evidence of a robots or fetch failure. Do not repeatedly resubmit the same clean sitemap or buy SEO tools. Preserve the full live Wix file set and use `docs/SEARCH_VISIBILITY_AUDIT_2026-10-14.md` as the verification record before any coordinated metadata/content deployment.

## Publishing and content

### Connected/verified routes
- Direct Publisher PR #43 is merged. Its 30-minute workflow is fail-closed behind `DIRECT_PUBLISHER_ENABLED == 'true'`; keep it false until official API authorization, secret setup, queue reconciliation and controlled publish tests pass.
- Metricool identity gate: current scheduled-item metadata identifies `cougarboy1999@gmail.com` as the creator. Do not create, update, delete, reschedule, or otherwise operate Metricool items until Metricool is explicitly reconnected under `satisfyforgee@gmail.com`. Preserve already-submitted First Computer Bug YouTube/TikTok items and let the Daily Publisher verify their terminal outcomes after the intended times; recover a definite failure only through an approved business-identity route.
- Buffer organization: `6accef267d527c51692f8cf9`.
- Instagram: `satisfyforgetv`.
- Facebook: `satisfyforgetv`.
- YouTube: `SatifyForgeVideos`.
- TikTok: `satisfyforge14` through the verified zero-cost Wix Social Publisher route when available.
- Metricool brand: `7271927`.

### Content strategy
- Optimize for real revenue and audience growth, not vanity views.
- Original executions only. Study viral mechanics such as hook, pacing, escalation, payoff, replay/share/save triggers without copying another creator's footage or distinctive expression.
- Current preferred factual short-form lane: narrated strange true stories, mysteries, creepy history, hidden details, and science/technology curiosities.
- Strong first-second hook, frequent visual progression, polished narration/captions, clear payoff, truthful AI disclosure where required.
- No filler posting just to maintain cadence.
- Check Buffer, Metricool, Wix, and recent live posts before publishing so only one scheduler owns each post/platform/time.
- Current platform strategy/research: `docs/GROWTH_SCAN_2026-10-13.md`.
- Dancing Plague is now confirmed complete across all four major channels. TikTok was published automatically through Wix as item `4c739b11-04ff-47c0-befe-4a681cb0780c`; do not recreate or retry it.

### Permanent no-repost history
- Lake Nyos — completed historical episode.
- Lake Peigneur — completed historical episode.
- Demon Core — completed historical episode.
- Operation Mincemeat — completed historical episode.

Use old production packets/performance only as research/reference; do not recreate those as new posts.

### Known scheduled backlog
- Dancing Plague: complete across the four major channels; never retry stale Metricool errors.
- First Computer Bug is confirmed complete across all four major channels:
  - Facebook: https://www.facebook.com/reel/1129238186292682/
  - Instagram: https://www.instagram.com/reel/Deej9dhCS_F/
  - YouTube: https://www.youtube.com/watch?v=3wSwuYGtdRI
  - TikTok: https://www.tiktok.com/@satisfyforge14/video/7696648328284507406
  - YouTube used one Buffer recovery after Metricool's terminal account-limit failure; TikTok used one Wix recovery after the same failure. Do not create or retry another copy on any of the four platforms.

### Next prepared original story
- Great Molasses Flood v5 is rendered and passed technical/motion QA at 1080×1920, 30 fps, 33.248 seconds, with readable captions and no freeze interval of 2 seconds or longer.
- SHA-256: `e11411f868d4c3d92011c4ffe5d66b0d5a909b822fdb2519068b1ca85aaa7588`.
- It is **not scheduled or published**. Recheck all live queues and platform timing before using it.
- The separate 65–80 second deeper-story experiment remains unrendered and should only be produced when it adds genuine platform value.

## Product building

### Daily productization
- Advance existing useful assets before inventing unrelated products.
- Productize internal SatisfyForge utilities when they solve repeatable buyer problems.
- Possible packaging paths: paid web app, plugin, browser extension, API, white-label tool, downloadable asset, or ongoing subscription when recurring value is real.
- Monetization catalog: `docs/MONETIZATION_CATALOG.md`.

### Existing/ongoing asset families
- Direct SatisfyForge Publisher under `publisher/`.
- Lead Rescue tools.
- Lead tracker.
- Message builder.
- Business audits.
- Calculators / mini-apps.
- Digital products / Payhip assets.
- Amazon KDP assets.
- Roblox game assets.
- Recovered browser-game source such as Forge Frenzy.

## Roblox

### Primary: Brainrot Rush v0.3
- Current primary game unless later evidence changes that choice.
- GitHub/source validation work exists and should remain the cloud-side source of truth.
- Do not call the game live until these pass:
  - Roblox Studio play test
  - mobile/device test
  - multiplayer test
  - persistence/data-store test
  - public-launch checks
- `docs/ROBLOX_SETUP.md` includes the release-gate matrix plus current Device Simulator / Network Simulator test guidance.

### Alternate prototype: Tile Panic
- Source recovered into `src/roblox/tile-panic/`.
- Keep isolated from Brainrot Rush.
- It is a simple prototype, not a released experience.

### Alternate project: Snackquake
- Latest canonical version is `0.2.1-save-fix`; the full tested source is now in `src/roblox/snackquake/` on `main`.
- Fresh canonical validation on 2026-10-13/14 passed:
  - 9 Lua-compatible Luau files parsed
  - 20 persistence assertions
  - 9,046 pure-rule assertions
  - real Roblox Studio runtime smoke: `SF_SMOKE_PASS Snackquake` with 15 rescue spots, 6 refuges and 15 embedded checks
- Private existing-place deployment is verified at Roblox place version 4; public visibility was not enabled.
- Real private-player gameplay verified pickup -> carry -> rescue/deposit, Fizz/Rescues changes, clean-round bonus and hazard recovery.
- Open Cloud publishing uses the supported existing-place API; the macOS helper can read the scoped key from local Keychain without exposing it.
- `FounderGlowPassId` remains `0`, so no live paid pass path is enabled.
- Still required before public-launch claims: clean leave/rejoin persistence proof, evolution/upgrade deployed-client tests, multiplayer, phone/gamepad UX, long-session performance, analytics readback, optional purchase-path testing, moderation/metadata and real-player retention evidence.
- Canonical truth boundary: `src/roblox/snackquake/README.md`.

Roblox Studio/device testing remains a genuine local/desktop requirement unless a supported cloud execution path becomes available. Continue code, documentation, balancing, monetization design, and cloud-side validation while local testing is blocked.

## Recovered browser game

### Forge Frenzy v2.1
- Recovered from the old repair kit into `archive/forge-frenzy-v2.1/`.
- Its original 19 browser-logic tests passed again on 2026-10-13.
- A real GitHub/Playwright Chromium smoke also passed: title/UI loaded, Start worked, tutorial closed, timer began counting down, canvas rendered and no page error was captured.
- It is browser-smoke-tested source, not a fully playtested or live deployed game.
- `archive/forge-frenzy-v2.1/README.md` is the truth boundary.

## Amazon KDP

- KDP assets can be prepared in the cloud.
- Holiday Paycheck Command Center interior/cover passed local preflight on 2026-10-13.
- `docs/KDP_PREFLIGHT_2026-10-13.md` is the current file-validation record.
- Publishing remains blocked by Amazon authentication and owner-only identity/tax/bank/legal setup where required.
- Do not guess or fill owner identity, tax, or banking data.
- Do not regenerate already-passing PDFs just to create activity; move only when Previewer/account access reveals a real issue.

## Other business workstreams to keep centralized

### Cleaning & restoration business
- Canonical plan: `docs/CLEANING_RESTORATION_MASTER_PLAN.md`.
- Target service families include carpet/upholstery, tile/grout, exterior cleaning, concrete/garage, auto detailing, water mitigation/structural drying, odor/fire cleaning support, mold/microbial remediation and contents restoration.
- The plan is phased so a Butler truckmount/drying fleet is a later utilization-backed capacity purchase rather than a speculative prerequisite.
- Current Ohio tax/compliance, EPA RRP boundaries, IICRC training path, insurance questions and launch gates are captured in the master plan.
- Keep old personal-Gmail funding drafts historical; use the owned business-mail bridge and business identity for current advisor outreach.

### CurbForge / 3D printing business
- Canonical zero-spend validation plan: `docs/CURBFORGE_PREPURCHASE_VALIDATION.md`.
- Product direction: premium, durable, detailed, multicolor, practical products people already buy.
- Existing first-mailbox STL kit and demand-test pack are preserved in Library.
- Priority families include custom vehicle mailboxes, house-replica mailboxes, pet houses, personalized home/yard products, organizers, signs, planters, and seasonal decor.
- Designs should be grounded in realistic straight-off-the-printer geometry: modular/snap-fit/bolt-together parts, embossed/recessed detail, texture, and multicolor filament; avoid relying on sanding/painting/glossy molded appearance.
- Do not buy a printer/materials to discover demand. Concept-test premium prices first and do not take deposits until production/fulfillment is verified.
- Keep CurbForge positioning separate from the existing SatisfyForge entertainment audience unless a deliberate cross-brand decision is made.

### Grocery/coupon automation
- Keep coupon/deal automation as a separate functional workstream but route status and decisions back through the Master Command Center.
- Prefer direct digital coupon clipping/connected-account workflows over screenshot-only/manual processes when a supported connector exists.
- No Kroger-specific plugin is currently available through the connected Plugin Directory search.
- Kroger's public developer surface exposes product/location/identity/cart capabilities, which can support an owned price/deal/cart intelligence tool, but a supported public coupon-clipping operation has not been established. Do not call a price scanner 'coupon clipping.'
- Actual account coupon clipping remains blocked until an authenticated Kroger-supported workflow exists.

## Automation policy

Active automation slots are scarce. Prefer multifunction loops instead of one task per old chat.

Current intended active functions:
1. Global Money Loop — overall zero-cost operations, blocker recovery, infrastructure, monetization.
2. Daily Publisher — coordinated publishing/backlog/failure handling.
3. Daily Money Product Builder — one realistic income asset or productization advance per day.
4. Growth Scan — current zero-cost opportunity/trend/operator research.
5. Outreach Watch — hourly combined Hunter outreach + Wix lead-form monitoring.

Rules:
- Do not reactivate old duplicate publishing/trend/upload/retry tasks unless the consolidated task cannot cover the requirement.
- Temporary one-time tasks should be paused/deleted/retired after their purpose is complete so they do not consume the active-task limit.
- When a new recurring need appears, first merge it into one of the five canonical loops.

## Paused / superseded systems

Keep old duplicated trend scans, upload loops, retry checks, one-time social posts, and test sequences paused unless a verified gap appears. Their prior knowledge can be reused, but their schedulers should not be restarted just because an old thread mentioned them.

## Priority order

1. Prevent lost money, broken checkout paths, missed leads, failed publishing, duplicate posts, or unsafe payment claims.
2. Convert existing traffic/outreach into a first/next sale.
3. Improve and sell existing products/services/tools.
4. Expand owned infrastructure so paid external tools are less necessary.
5. Continue content distribution and research.
6. Advance Roblox/KDP and other blocked projects as far as cloud-side work permits.
7. Develop additional business ideas only when they have a clear buyer, problem, price path, and distribution path.

## Thread consolidation rule

From now on, prior threads are historical context, not separate operating systems. New instructions, status checks, blockers, and completions should be routed through the Master Command Center and written back to the appropriate canonical source (GitHub docs/code, Floot Control Center, or the consolidated automations). Do not create duplicate state just because a request originated in an older conversation.
