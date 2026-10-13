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
- Prefer this system over paid/metred browser services where supported.
- Public-site automation works.
- Authenticated third-party site automation remains subject to secure-session and provider/security constraints; do not store reusable login cookies or passwords in the public repo.

## Revenue and sales

### Payhip
- Payhip is the primary $0-first digital storefront.
- Existing products should be reused/improved before creating near-duplicates.
- Verified historical products include the Holiday Paycheck Command Center and later canonical product IDs recorded elsewhere in repo/commerce docs.
- Payment routing preference: Payhip/PayPal where verified.
- Never expose Chime/bank details to customers.
- Tool Vault checkout is currently treated as **paused/unverified** because a Payhip audit showed a price mismatch ($0 in Payhip while the site had advertised $49).
- Do not promote or restore the Tool Vault paid checkout until the actual Payhip price is independently verified/corrected.
- Earlier alleged service checkout URLs are also unverified and must not be used until rechecked.
- `commerce/checkout_registry.json` is the canonical machine-readable quarantine list. `scripts/validate_commerce_safety.py` now blocks quarantined checkout URLs from customer-facing and automation surfaces; the pull-request validation passed and was merged on 2026-10-13.

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
- Wix request/form flow remains the safe intake route while checkout verification is paused.

## Website and funnel

### Wix Growth Toolbox
- Canonical live site is the existing free Wix Headless deployment.
- Preserve the full production file set on every redeploy; do not rebuild from only the smaller repository subset.
- Follow `docs/LIVE_WIX_SITE_INVENTORY.md` before updating the site.
- Wix Forms is the live lead intake source.
- Tool Vault purchase CTAs were placed into a safe paused/request state after the Payhip pricing mismatch was discovered.
- Do not restore direct checkout CTAs until the checkout and price are verified.

## Publishing and content

### Connected/verified routes
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

### Known scheduled backlog
- Operation Mincemeat: complete; never repost.
- Dancing Plague: already scheduled/handled across the four major channels for 2026-10-13; only retry a definite failure.
- First Computer Bug: already scheduled/handled across the four major channels for 2026-10-14; only retry a definite failure.

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

## Roblox

- Current primary game: Brainrot Rush v0.3.
- GitHub/source validation work exists and should remain the cloud-side source of truth.
- Do not call the game live until these pass:
  - Roblox Studio play test
  - mobile/device test
  - multiplayer test
  - persistence/data-store test
  - public-launch checks
- Roblox Studio/device testing remains a genuine local/desktop requirement unless a supported cloud execution path becomes available.
- Continue code, documentation, balancing, monetization design, and cloud-side validation while local testing is blocked.

## Amazon KDP

- KDP assets can be prepared in the cloud.
- Publishing remains blocked by Amazon authentication and owner-only identity/tax/bank/legal setup where required.
- Do not guess or fill owner identity, tax, or banking data.
- Keep finished listing/interior/cover/keyword/category assets ready so owner-only setup is the smallest possible remaining step.

## Other business workstreams to keep centralized

### Cleaning & restoration business
- Continue research/planning for a cleaning and restoration company covering carpet cleaning, water/fire/mold restoration, HVAC cleaning, tile/grout, concrete/garage floors, exterior washing, bathrooms, pressure washing, auto detailing, and related services.
- Reuse business-plan, equipment, licensing/insurance/training, startup, estimating, branding, and funding work rather than restarting in separate threads.

### 3D printing business
- Product direction: premium, durable, detailed, multicolor, practical products people already buy.
- Priority families include custom mailboxes, pet houses, personalized home/yard products, pet products, organizers, signs, planters, and seasonal decor.
- Designs should be grounded in realistic straight-off-the-printer geometry: modular/snap-fit/bolt-together parts, embossed/recessed detail, texture, and multicolor filament; avoid relying on sanding/painting/glossy molded appearance.

### Grocery/coupon automation
- Keep coupon/deal automation as a separate functional workstream but route status and decisions back through the Master Command Center.
- Prefer direct digital coupon clipping/connected-account workflows over screenshot-only/manual processes when a supported connector exists.

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
