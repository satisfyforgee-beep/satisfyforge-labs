# SatisfyForge Roblox — $0 Revenue Launch Track
Date: 2026-10-17
Status: private QA only. **No public release, no paid products configured, no verified earnings.**

## Chosen first candidate: Brainrot Rush
Why: existing Roblox Studio runtime and two-client tests, simulated mobile viewport QA, private published test target, and verified live save/rejoin of a basic pickup. Avoid splitting effort among new games until one passes launch gates. Snackquake and Tile Panic remain fallback prototypes, not simultaneous launches.

## Player value first
- Core: collect rare glowing orbs, build combos, upgrade, rebirth, and survive timed Snackquake events.
- Short-term target: clear first-60-second objective and reliable saved progress, without purchases.
- Retention experiments after safe release: a free daily goal, visible collection milestones, and player-requested updates. Measure whether players actually return; do not claim growth before data.

## Free-only route to potential revenue
1. Pass physical Android touch/control check, 15-minute normal-speed performance test, and extended persistence/upgrade/rebirth checks.
2. Review public title, description, thumbnail, age/content questionnaire, and Roblox eligibility/privacy declarations as account owner.
3. Release a playable **free** game only after QA gates; confirm public live URL.
4. Measure first-session completion, retention, crashes, session duration and repeat visits. Do not buy ads, traffic, or bot players.
5. After genuine engagement exists, optionally configure transparent cosmetic-only game passes (for example a guaranteed glowing trail or cosmetic nameplate). The game remains fully playable without payment. Prices, product IDs and Roblox policy compliance require explicit owner review before enabling.
6. Promote using original SatisfyForge footage through the existing approved free business-identity channels; check Buffer and Wix Social Publisher before scheduling to avoid duplicates. Metricool remains retired.

## What money math means (illustration, not a forecast)
Roblox earnings depend on actual eligible Robux earned, marketplace fees, cash-out eligibility, current DevEx rate, taxes and account requirements. Never equate the Reddit screenshot's Robux balance with cash or guaranteed earnings. Do not project $100/day until real analytics justify it.

## Current blockers
- Physical Android playtest and touch usability unverified; simulated iPhone/Galaxy viewport checks passed.
- Long normal-speed orb/event/performance test and expanded persistence checks incomplete.
- Public metadata and Roblox content/eligibility questionnaire require owner review.
- No verified public game URL, paying users, game-pass IDs, or revenue yet.

## Reproducible test
`python3 tools/roblox-studio/run_brainrot_event.py --keep-artifacts`
QA-only accelerated two-player Studio run on 2026-10-17: orb cap, forced cleanup/refill, event activation/deactivation PASS. Production source untouched. Not equivalent to a 15-minute live endurance test.
