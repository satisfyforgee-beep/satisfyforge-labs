# Roblox Runtime Status — 2026-10-13

This is the verified local-engine status from the newly authorized SatisfyForge Mac test node. A runtime smoke is **not** the same as a public release or a full human/device playtest.

## Test node

- Roblox Studio installed and authenticated on the authorized Mac.
- Rojo 7.7.1 installed locally at zero cost.
- `tools/roblox-studio/run_smoke.py` builds repository source into temporary `.rbxlx` files and executes explicit runtime assertions through Roblox Studio's `RunScript` task.
- The test runner does not publish experiences or spend money.

## Brainrot Rush v0.3

Verified:
- static source contract passes;
- Rojo place build succeeds;
- Roblox Studio loads the generated place and runs simulation;
- arena floor, spawn, upgrade pad and rebirth pad are created;
- Brainrot orbs spawn during runtime;
- automated runtime smoke reports `SF_SMOKE_PASS BrainrotRush`.

Issue found and fixed:
- the first actual engine run crashed in an unpublished local place because `DataStoreService:GetDataStore()` was called unguarded;
- source now degrades to explicit session-only mode when persistence is unavailable instead of aborting gameplay.

Still open before release claims:
- real character/control playtest;
- two-client multiplayer;
- phone/tablet and gamepad UX;
- private published DataStore persistence;
- moderation/metadata/privacy/public launch checks.

## Tile Panic

Verified:
- Rojo place build succeeds;
- Roblox Studio loads the generated place and runs simulation;
- lobby/spawn are created;
- all 64 arena tiles are created;
- automated runtime smoke reports `SF_SMOKE_PASS TilePanic`.

Still open:
- full countdown/wave/elimination/winner payout flow;
- multiplayer contention;
- device UX;
- persistence/analytics/monetization design;
- release checks.

## Snackquake

The recovered v0.2 source package was materialized locally and tested separately because the full source is not yet canonical in this repository.

Verified locally:
- 9 Lua-compatible Luau files parsed;
- 20 persistence assertions passed;
- 9,046 pure-rule assertions passed;
- a fresh place build succeeded;
- recovered metadata was reconciled to `0.2.1-save-fix` and 105-second rounds;
- Roblox Studio engine smoke passed 15 embedded checks and 0 failed;
- world, rescue chute, 15 rescue spots, 6 refuges, remotes/config and initialized round state were present;
- external harness reported `SF_SMOKE_PASS Snackquake`.

Still open:
- full rescue/deposit/disaster flow with a player character;
- two-client contention;
- real-device/gamepad testing;
- private cloud-save verification;
- analytics readback;
- any purchase/pass path;
- public launch.

## Other local gates re-run on the same Mac

- Video Engine unit tests: 4 passed.
- Analytics Engine unit tests: 3 passed.
- Direct Publisher tests: 9 passed after using the local repo virtual environment.

No sale, publication, DataStore persistence, purchase, or public Roblox launch is claimed by these results.
