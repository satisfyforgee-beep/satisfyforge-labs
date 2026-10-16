# SatisfyForge: Tile Panic

Separate Roblox survival-game prototype extracted from the verified root archive `SatisfyForge_Roblox_Prototype.zip` on 2026-10-13. It is **not** the primary Roblox project and must not overwrite Brainrot Rush / Snackquake work.

## Current prototype

- Procedural neon 8×8 tile arena.
- 10-second lobby countdown.
- 18 escalating disappearing-tile waves.
- Simple survivor tracking.
- Winners receive 1 session-only Win and 50 session-only Coins.
- Server-created HUD, lobby spawn, arena and round loop.
- Server-side arena boundary checks every 0.2 seconds: contestants who escape to the safe lobby, fall, or fly outside the arena are eliminated rather than rewarded as survivors.
- Contestants are assigned distinct starting tiles until all 64 are used, avoiding unnecessary spawn overlaps in ordinary servers.

## Verified October 16, 2026 regression

- Rojo build and real Roblox Studio engine smoke: **PASS** (64 tiles, lobby and arena loaded).
- Two-client Roblox Studio multiplayer boundary test: **PASS**. One client left the arena for the lobby and was returned as eliminated; the second client's position remained unchanged.
- Automated runner: `python3 tools/roblox-studio/run_tile_multiplayer.py`.
- These checks do not establish full 18-wave payout correctness, mobile controls, live DataStore saving, performance on low-end phones, or public-launch readiness.

## Source

- `ServerScriptService/Game.server.lua`

The original extracted prototype was a 4,315-byte server script with one README. The current server script has been improved since extraction; the original ZIP remains at the repo root for comparison.

## Truthful status

This is a prototype, not a commercially ready or published Roblox experience. On 2026-10-13 the owned Roblox Studio runner built this source and passed an engine runtime smoke: the place loaded, simulation started, the lobby existed and all 64 arena tiles were created. Current gaps include:

- full round/elimination/winner-flow playtest
- multiplayer contention/round testing
- mobile/gamepad UX
- persistence/DataStore handling
- analytics
- monetization design and purchase-path validation
- moderation/publication checks
- retention/balance testing

## Studio test path

1. Automated structural/runtime smoke can be repeated with `python3 tools/roblox-studio/run_smoke.py --game tile-panic`.
2. Run solo Play and verify HUD, full countdown, falling/elimination, winner payout and respawn behavior.
3. Run at least a 2-player local server test before any public launch.
4. Test phone/tablet and gamepad UX.
5. Do not enable paid monetization until persistence/economy behavior is designed and tested.

## Project priority

Keep this as an alternate/simple prototype. The Master Command Center should prioritize the stronger primary Roblox project unless a future test shows Tile Panic has a materially better retention or development path.
