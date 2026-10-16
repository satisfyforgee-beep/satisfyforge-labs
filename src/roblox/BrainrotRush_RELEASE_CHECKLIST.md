# Brainrot Rush — Release Readiness Checklist

Current code line: v0.3

Goal: move Brainrot Rush from a repository prototype to a Roblox experience that is safe to call playable/public only after the checks below pass.

## What already exists
- Server-authoritative orb spawning and collection
- Weighted Common / Rare / Epic / Legendary rewards
- Upgrade pad and level-based earnings
- Rebirth loop with permanent multiplier
- Combo mechanic
- Timed Snackquake event with faster spawns and 2x event multiplier
- Leaderstats
- DataStore load/save path with autosave and BindToClose attempt
- Mobile-friendly on-screen HUD foundation
- Server-to-client announcements
- Rojo-style project file

## Do not call the game public/live until all Critical checks pass

### Critical — Roblox Studio
- [ ] Project opens in current Roblox Studio without syntax/runtime errors
- [ ] Server script is in ServerScriptService
- [ ] Client script is in StarterPlayerScripts
- [ ] Remotes are created once and survive respawns correctly
- [ ] Arena floor, spawn, upgrade pad and rebirth pad appear correctly
- [ ] No duplicate arena geometry is created after a test-server restart

### Critical — core gameplay
- [ ] Common/Rare/Epic/Legendary orbs spawn at expected approximate ratios
- [ ] One orb can be claimed only once
- [ ] Orb count does not drift above MAX_ORBS during a 15-minute session
- [ ] Orb cleanup correctly decrements active count
- [ ] Combo resets after the combo window and caps at MAX_COMBO
- [ ] Upgrade price progression matches the displayed NextUpgradeCost
- [ ] Rebirth requires Level 20 + 2500 Brainrot and resets the intended values only
- [ ] Snackquake starts and ends cleanly and does not leave the event multiplier stuck on

### Critical — multiplayer
- [ ] Test with at least 2 local Studio players
- [ ] Players cannot receive another player's pickup reward
- [ ] Simultaneous touches do not double-award an orb
- [ ] Legendary announcements show the correct player
- [ ] Upgrade/rebirth prompts affect only the triggering player
- [ ] One player leaving does not break combos or state for remaining players

### Critical — persistence
- [x] Enable Studio API access only in a safe test environment
- [x] Join private QA, earn Brainrot through a real orb pickup, leave, rejoin; Brainrot and Collected restore correctly
- [ ] Upgrade and rebirth; leave; rejoin; Level/Rebirths and intended values restore correctly
- [ ] A failed DataStore request does not crash the session
- [ ] Autosave does not visibly freeze gameplay
- [ ] Server shutdown save completes for test players
- [ ] Decide whether v1 release needs stronger session locking before public scale

Verified 2026-10-16 against private QA universe `10771127276`, place `103299455198893`. The test began with no profile, collected one real server-spawned Common Brainrot orb (`Brainrot=1`, `Collected=1`), stopped the play session, rejoined with the same values restored from `SatisfyForge_BrainrotRush_v1`, then removed the QA record and verified it returned to nil. Evidence is source-hash locked in `tests/roblox/brainrot_persistence_evidence.json`; changing the Brainrot server/client source invalidates the automated live-persistence gate until it is retested.

### Critical — mobile/device UX
- [x] iPhone 16 portrait and landscape viewport simulation
- [x] Galaxy A06 portrait and landscape viewport simulation
- [x] Simulated top HUD bounds remain onscreen, stat labels meet minimum size, and top HUD does not overlap the bottom hint
- [x] Simulated bottom hint remains onscreen in all four phone-shaped cases
- [ ] Physical Android phone portrait and landscape checks
- [ ] Physical iPhone check if an iPhone is available before launch
- [ ] Proximity prompts are comfortable to use on real touch hardware
- [ ] Collecting orbs does not require precision movement that feels bad on real mobile hardware
- [ ] No important interaction depends only on hover/mouse behavior on a physical device

Verified in Studio device simulation on 2026-10-16 by `tests/roblox/brainrot_mobile_harness.luau`: iPhone 16 at 393x852 and 852x393, Galaxy A06 at 360x800 and 800x360. This evidence covers viewport/layout regressions only; it does **not** count as physical touch-control verification.

## Retention tests for v0.4 candidate
Do not add all of these blindly. Test one loop at a time and keep only what improves play sessions.

1. **First-60-second goal**
   - Make the first upgrade reachable fast enough to teach the loop.
   - Show a clear target rather than adding tutorial walls of text.

2. **Session quest**
   - Example: collect 25 orbs / find one Rare / maintain x3 combo.
   - Reward only in-game progression currency; no fake urgency.

3. **Collection milestone**
   - Cosmetic/title milestone at 100 / 500 / 1,000 collected.
   - Prefer visible status over pay-to-win power.

4. **Snackquake anticipation**
   - Add a short countdown only if it improves retention and does not clutter mobile UI.

5. **Return hook**
   - Consider a non-punitive daily/session reward after persistence is proven.
   - Never use misleading countdowns or loss-threat mechanics.

## Economy/balance checks
- [ ] Time to first upgrade measured with a new account
- [ ] Time to Level 5 / 10 / 20 measured
- [ ] First rebirth time measured
- [ ] Legendary reward does not trivialize the early economy
- [ ] Combo multiplier does not explode progression unexpectedly
- [ ] Rebirth multiplier remains understandable after several rebirths
- [ ] Snackquake reward rate feels exciting without making normal play pointless

## Performance
- [ ] Test with MAX_ORBS = 34 on lower-end mobile emulation
- [ ] No runaway connections or orphaned UI
- [ ] No excessive server warnings
- [ ] Stable frame rate during Snackquake
- [ ] Network ownership / physics is not creating unnecessary traffic (orbs are anchored)

## Safe monetization design — later, not required for first test
If monetization is added, keep the free core loop complete and playable.

Possible fair options:
- Cosmetic orb trails
- Nameplate/title cosmetics
- Emotes
- Cosmetic spawn effects
- Optional convenience that does not invalidate normal progression

Avoid for the initial launch:
- Hard paywalls to basic gameplay
- Misleading limited-time pressure
- Pay-to-win multipliers that make free players irrelevant
- Monetization before retention is proven

## Public-launch gate
Only mark Brainrot Rush as live/public when all of these are true:
- [ ] Studio runtime passes
- [ ] 2+ player test passes
- [ ] persistence test passes
- [ ] mobile test passes
- [ ] no critical errors in Output
- [ ] game icon/thumbnail/description exist
- [ ] age/content questionnaire is reviewed by the account owner
- [ ] privacy/monetization/platform declarations are truthful
- [ ] public experience URL is confirmed

Until then, describe it as a prototype / repository build.
