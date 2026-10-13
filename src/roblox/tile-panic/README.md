# SatisfyForge: Tile Panic

Separate Roblox survival-game prototype extracted from the verified root archive `SatisfyForge_Roblox_Prototype.zip` on 2026-10-13. It is **not** the primary Roblox project and must not overwrite Brainrot Rush / Snackquake work.

## Current prototype

- Procedural neon 8×8 tile arena.
- 10-second lobby countdown.
- 18 escalating disappearing-tile waves.
- Simple survivor tracking.
- Winners receive 1 session-only Win and 50 session-only Coins.
- Server-created HUD, lobby spawn, arena and round loop.

## Source

- `ServerScriptService/Game.server.lua`

The extracted source matches the previously audited archive structure: one README plus one 4,315-byte server script. The original ZIP remains at the repo root as the preserved upload.

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
