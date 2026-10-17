# SatisfyForge Roblox Creator Playbook — 2026-10-17

## Reference studied, source distinction
- The screenshot supplied by the owner identifies a DitchyDevelopments video with the visible title **“I Gave ChatGPT 1 Prompt to Make a Viral…”**. Its full URL and video contents have NOT been verified; do not claim to have watched that exact video.
- The full 4:05 transcript of **DitchyDevelopments, “How to ACTUALLY get Players in your ROBLOX Game in 2026”** (transcribed 2026-10-14) was reviewed at https://sozai.app/transcript/get-players-roblox-game-2026/.
- This creator reports 40,000+ visits on an earlier Roblox game with no ad spend. This is the creator's claim, not a prediction for SatisfyForge.
- Creator's stated method: polish first; ads do not rescue low-retention games; share progress through regular short videos; build a story viewers want to follow; invite audience suggestions and testing; reach relevant small creators/communities rather than spamming DMs; prioritize thumbnail and first-click appeal. A referenced tool is Forge GUI; no purchase or signup is required for this playbook.

## Design contract / game identity

**Working title:** HYPER MUTATION RUSH
**One-sentence hook:** Race through neon obstacles, grab strange mutations that change your speed and look, beat your personal best, and challenge friends to beat your time.
**Audience:** Roblox mobile and desktop players who enjoy short obstacle runs, fast upgrades, bright effects, and social challenges.
**Primary loop (90 seconds to 5 minutes):** Press RACE NOW → pass numbered checkpoints → collect speed orbs and mutation gates → avoid hazards → finish → earn coins and record personal best → buy earned upgrades/pet → replay faster.
**Secondary loop:** After 2–3 runs, explore distinct side challenges for coins and a 3-activity quest, then return to racing.
**Differentiator to build next:** Mutations must become **visually obvious and mechanically meaningful** (e.g., bounce, slide, hover) with server-validated cooldowns. Speed-only +3 gates are currently insufficiently unique.
**First 30 seconds target:** See start and first checkpoint, understand one-line goal, collect an orb, see instant feedback, and reach the next checkpoint.
**No money spent:** No ads, subscriptions, metered AI, asset packs, or paid plugins. Earned in-game coins only.

## Production phases / gates

1. **Focused hook:** Race Now button, personal best, mobile HUD. Keep map secondary. Run server/client smoke and 2-client checks.
2. **Make mutations exciting:** Add 3 original visible abilities, controlled durations, VFX, cooldowns, clear failure recovery, and tests for exploit resistance.
3. **Make the first minute intuitive:** Prompt at spawn; distinguish checkpoint, hazard and reward visually; include guided progression. Test on physical Samsung, with sound and without sound.
4. **Persistence and fairness:** Implement validated DataStore save/rejoin for wins, earned coins, owned cosmetic pets, best race, versioned schema and Studio-safe testing; handle failures honestly. Do not save per-touch to avoid throttling.
5. **Visual polish and performance:** Distinct map silhouettes, real prop geometry, audio with licensed/free assets, animation, optimized phone rendering, mobile-friendly controls.
6. **Playtest and measure:** Recruit a small opt-in group. Track start → checkpoint 1 → finish funnel, average session length, return rate, error logs, and whether players voluntarily replay. No invented analytics.
7. **Release:** Creator owner verifies ownership, age/content questionnaire, privacy, moderation and release settings. Publish only after private testing and explicit owner go-ahead.
8. **Growth:** Make original development shorts showing actual gameplay. Offer a short public test to willing Roblox communities and small creators, with truthful claims and no unsolicited mass DMs. Test thumbnails. No ad spend.
9. **Monetization only after engagement:** Optional clearly priced cosmetic passes after Roblox policies and owner review; no pay-to-win, misleading scarcity, gambling or paid randomness.

## Short-video plan (drafts, NOT posted)

**Short A: Challenge**
- 0–2s: On-screen hook: “Can AI build a Roblox game people actually WANT to replay?”
- 2–8s: Capture real game start, bright checkpoint, orb pickup.
- 8–16s: Show one mutation and laser failure; cut to successful attempt.
- 16–25s: Show personal-best timer and friend challenge. Text: “Day 1: game works. Day 2: making mutations crazy.”
- 25–30s: Ask: “What mutation should we add next: bounce, hover, or slide?”
- Only use recorded footage from the real game. Do not claim virality or earnings.

**Short B: Before/after**
- Show old flat platform vs updated gameplay, clearly labeled as actual footage, then ask viewers to vote on one next feature.

**Short C: Feedback**
- Demonstrate a real bug and fix in under 25 seconds, with honest outcome.

## Success gates, not promises
- Functional two-client tests and 15-minute physical-phone playtest.
- First-time testers can describe the goal without explanation and finish the first checkpoint.
- At least several independent testers voluntarily replay and can name what they liked.
- Only then assess audience growth and optional monetization.

**Explicitly not done:** exact screenshot video watched, Roblox experience published, real player retention observed, revenue earned, paid marketing.
