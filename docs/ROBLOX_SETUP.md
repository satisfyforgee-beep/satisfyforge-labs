# SatisfyForge Brainrot Rush — Roblox Studio setup and release gate

This is an original playable prototype, not a published Roblox experience yet.

## Verified repository state

- Server source: `src/roblox/BrainrotRush.server.lua`
- Client HUD: `src/roblox/BrainrotRush.client.lua`
- Version: v0.3
- Server blob reviewed: `ea1337ad73745ea74821d9325f976e64b5b239a5`
- Client blob reviewed: `27f04fbd0af7d5a30e9fb1bee3372a2abbd3e9fc`
- Gameplay commit: `6fa4caa98e896a4744c9822a036009b521247f08`
- Mobile HUD commit: `2d01c867e0752cb49f3346a399277d99392b8a20`
- Engine-smoke/DataStore fallback commit: `689a0c33a4ddaf851063931d0370e519108d8fd0`

Repository review confirms the features exist in source. On 2026-10-13, the owned Roblox Studio runner also built the current source, started simulation, created the arena/spawn/upgrade/rebirth pads, spawned Brainrot orbs, and reported `SF_SMOKE_PASS BrainrotRush`. That smoke does not prove real character controls, mobile devices, multiplayer contention, published DataStore persistence, moderation or public launch.

## Install v0.3

1. Open Roblox Studio on Windows or macOS and create or open the SatisfyForge test experience.
2. In **ServerScriptService**, add a Script and paste `src/roblox/BrainrotRush.server.lua`.
3. In **StarterPlayer > StarterPlayerScripts**, add a LocalScript and paste `src/roblox/BrainrotRush.client.lua`.
4. Press **Play**. The server script should build the arena automatically.
5. Keep the first validation place private. Do not overwrite a known-good public place during testing.

## Current gameplay

- Collect glowing Brainrot orbs.
- Common / Rare / Epic / Legendary rarity tiers.
- Green upgrade pad increases earnings up to level 20.
- Purple rebirth pad unlocks at level 20 + 2500 Brainrot and gives a permanent +50% earnings bonus per rebirth.
- Fast collection builds a combo up to x5.
- A Snackquake event starts every 90 seconds for 20 seconds with 2x rewards and faster spawns.
- Mobile-friendly HUD shows Brainrot, level, collected count, rebirths and combo.
- Player progress uses DataStore persistence and autosaves every 60 seconds.
- Rewards, upgrades, rebirths and rarity rolls are calculated on the server. The only RemoteEvent in v0.3 sends announcements from server to client; it does not accept reward commands from clients.

## Current Roblox Studio test tooling

The repeatable owned runner is `tools/roblox-studio/run_smoke.py`; its assertions live in `tests/roblox/brainrot_runtime_smoke.luau`. The verified 2026-10-13 run is recorded in `docs/ROBLOX_RUNTIME_STATUS_2026-10-13.md`. This covers engine boot and structural gameplay smoke only.

Roblox now documents a beta **Device Simulator** toolbar plus **Network Simulator**. These should be used in the next Studio session to cover more devices and connection conditions without requiring separate physical hardware for every case.

To enable the current simulator tooling:
1. In Studio open **File > Beta Features**.
2. Enable **New Device Simulator** and restart Studio.
3. During playtests, use Device Simulator to switch among phone/tablet/desktop/console-style profiles and verify scaling/touch behavior.
4. Use the Network control to apply repeatable connection presets such as Home Wi-Fi, Standard Mobile (4G/LTE), and Bad Connection (3G).
5. Re-run reward/pad/announcement/rejoin-sensitive interactions under at least one mobile-like network preset so delayed server confirmation does not create duplicate rewards or misleading UI.

Roblox also documents Studio-only scripted test services, including multi-client simulation and virtual input. They can reduce repetitive manual testing later, but they still require a real Studio environment and do not make the current cloud GitHub runner a Roblox engine runtime.

Official references:
- https://create.roblox.com/docs/studio/device-simulator
- https://create.roblox.com/docs/studio/network-simulator
- https://create.roblox.com/docs/studio/testing-modes

## Safe DataStore preparation

1. Publish only a private test copy first.
2. In that test copy, enable **Game Settings > Security > Enable Studio Access to API Services** only when persistence testing is required.
3. Never change `DATASTORE_NAME` on a production build without a deliberate migration plan; a new name makes existing progress appear lost.
4. Use test accounts and small test values. Do not edit live player data to speed up a test.
5. Confirm the Output window shows no DataStore budget, authorization or serialization errors.

## Required release-gate matrix

Record Pass / Fail / Blocked plus the date, Studio version and device for every row.

| Area | Test | Pass criteria |
| --- | --- | --- |
| Boot | Start a fresh private server | Arena, spawn, upgrade pad and rebirth pad appear once; Output has no red errors. |
| Collection | Touch each rarity orb | Exactly one reward is granted, Collected increases once and the orb disappears. |
| Contention | Two players touch the same orb together | Only one player receives the reward; no duplicate payout occurs. |
| Combo | Collect within and outside the 8-second window | Combo climbs to x5, caps at x5 and resets to x1 after the window. |
| Upgrade | Buy several levels, then attempt with insufficient funds | Correct cost is deducted once; level rises once; insufficient funds never create a level. |
| Upgrade cap | Reach level 20 | Further upgrade attempts do nothing and the next-cost attribute becomes 0. |
| Rebirth | Attempt below requirements, then at level 20 + 2500 Brainrot | Early attempt is rejected; valid attempt resets Brainrot/level and adds exactly one rebirth. |
| Reward math | Compare base, level, rebirth, combo and Snackquake payouts | Observed integer payout matches server formula with no unexpected client multiplier. |
| Snackquake | Observe a complete event cycle | Event begins near 90 seconds, lasts near 20 seconds, doubles rewards, speeds spawning and returns to normal. |
| Announcements | Trigger upgrade, failure, rebirth and Legendary messages | Intended clients receive readable messages; no permanent or overlapping banner remains. |
| Autosave | Play longer than 60 seconds and inspect Output | Save attempt completes without error or freezing gameplay. |
| Rejoin | Earn progress, leave cleanly and rejoin | Brainrot, Collected, Level and Rebirths restore correctly. |
| Failure recovery | Disable API access or simulate unavailable persistence in a test copy | Gameplay remains usable, errors are warnings, and no false “saved” claim is shown. |
| Shutdown save | Close a private server after changing progress | Rejoin restores the latest confirmed state within Roblox shutdown limits. |
| Respawn | Reset character during normal play and during Snackquake | HUD remains present, values stay synchronized and collection still works. |
| Two-player HUD | Run **Test > Start** with at least 2 players | Each player sees only their own stats; global announcements reach both. |
| Phone portrait | Use Device Simulator with a narrow phone viewport | Top bar and hint remain readable and do not cover movement/jump controls. |
| Phone landscape | Switch the same phone profile to landscape and try another common profile | All five stats fit without clipping or overlap. |
| Touch interaction | Use touch/device emulation to activate both pads | Prompts are reachable and usable without keyboard input. |
| Mobile network | Apply Standard Mobile (4G/LTE) in Network Simulator | Collection/pads/announcements stay understandable; delayed confirmation never duplicates rewards. |
| Poor network | Apply Bad Connection (3G) preset | Gameplay degrades gracefully with no reward duplication, runaway requests or permanent stuck UI. |
| Performance | Observe server/client performance with 34 active orbs and Snackquake | No runaway orb count, repeated arena parts, severe frame drop or growing error spam. |
| Reconnect loop | Join/leave repeatedly with two test accounts | No duplicated leaderstats, HUD, remotes, pads or arena objects. |

## Manual security review

Before public launch, confirm all of the following:

- No client RemoteEvent or RemoteFunction can award Brainrot, change Level or add Rebirths.
- Upgrade and rebirth prices are recalculated by the server.
- A client cannot receive the same orb twice.
- Player data is numeric, non-negative and bounded where the game defines a maximum.
- Repeated prompt activation cannot produce free currency or duplicate rebirths.
- DataStore failures never reset a known-good record during a retry.
- Public-server Output does not expose secrets or personal data.

The current v0.3 source uses server-side rewards and server-side prompt handlers. Engine boot and structural spawning passed in Studio; reward contention, prompt economy behavior, multiplayer and persistence still require the release-gate tests above.

## Test evidence to capture

Keep one compact evidence packet before launch:

- Screenshot of the clean Output window after boot.
- Screenshot or short recording of two-player orb contention.
- Before/after values for one upgrade and one rebirth.
- Snackquake start/end timestamps and one verified payout.
- Rejoin screenshot showing restored progress.
- Device Simulator screenshots for phone portrait and landscape.
- Network Simulator preset used plus any observed delay/error behavior.
- Studio place version or private-save timestamp.
- Any error messages copied exactly.

Do not upload credentials, private account information, tax/bank data or secret tokens.

## Release decision

### Ready for private playtest

All Boot, Collection, Combo, Upgrade, Rebirth, Reward math, Snackquake, HUD and Output checks pass.

### Ready for limited external test

Private playtest passes, two-player contention passes, DataStore rejoin passes and Device Simulator/mobile-network checks pass. At least one real phone test remains strongly preferred before public launch.

### Ready for public launch

Limited external test passes, Creator Dashboard metadata/age guidance is complete, moderation accepts the assets, public permissions are deliberately enabled, and a fresh public-server smoke test passes.

Until the public-launch gate passes, describe Brainrot Rush as **source-complete v0.3** or a **private prototype**—never as live, released, popular or earning revenue.

## DevEx tax note for future monetization

Roblox states that beginning November 1, 2026, DevEx payments will be classified as royalties and tax information moves into Creator Hub. This is not a current launch blocker because the game is not earning DevEx, but any future tax-information step is owner-controlled. Never place an SSN/TIN, W-9 data, bank details or other tax identifiers into GitHub or chat.

Reference: https://create.roblox.com/docs/production/monetization/tax-information

## Rollback

If a new edit breaks the test place:

1. Stop public or external testing.
2. Preserve the failing Output text and exact reproduction steps.
3. Restore the last known-good Studio place version.
4. Compare repository changes against the reviewed v0.3 commits listed above.
5. Fix in a private copy and rerun the failed row plus the full Boot/Collection/Persistence smoke set.

Do not delete player data or rename the DataStore as a first-line fix.

## Still intentionally unverified

- Full character/control gameplay for the current GitHub sources (engine boot and structural spawning already passed).
- Real-device mobile performance.
- Multiplayer load beyond a small test server.
- Public-server DataStore behavior.
- Roblox moderation/launch approval.
- Retention and monetization performance.

No paid assets or external packages are required.
