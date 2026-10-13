# Snackquake Expedition v0.2.1 — save reliability patch

Prepared October 8, 2026 at $0. This is a local patch, not a public Roblox release. The existing canonical v0.2 filenames are retained; the embedded version is `0.2.1-save-fix`.

## Fixed

- **Progress lost during a slow departure save:** Previously, a departing player waited up to 12 seconds behind an autosave. If that wait expired, player cleanup removed the record while the autosave still held an older snapshot. That older write could finish without saving the later rewards. A departure now queues a final save on the existing writer before waiting. The writer retains the record and then saves a fresh snapshot and releases its lease, even when the active-player table has already been cleaned up.
- **Save ordering and duplicate departure:** New autosaves cannot overtake a closing profile. Repeated final-save requests are idempotent after a successful release. A failed final save remains retryable while the record is available. Loss of lease ownership still prevents writes to another server's profile.
- **Late reward mutation:** Round-end rewards skip closing records so the final snapshot is not followed by another round bonus during departure.
- **Duplicate initialization:** A player already being initialized is not initialized a second time by overlapping startup enumeration and the player-added event. Shutdown also rejects new initialization.
- **False Studio failure:** The structural smoke check now expects the configured 105-second round and checks that the warning precedes panic and the end of the round. It previously still expected 90 seconds.
- **Build evidence:** The build manifest reads the version from Config and records this patch as not yet Studio-tested or published. The previous build's observed open/spawn/private-save milestones are retained separately.

## Regression evidence

The slow-autosave regression failed on the prior implementation at `departure preserves progress earned during slow autosave`. It passes with the patched writer.

Fresh 2026-10-13 rerun of the canonical Library archive:
- 9 Lua-compatible Luau source files parsed.
- 38 persistence assertions passed, including delayed departure, cleanup-before-completion, lost-lease and retry cases.
- 9,046 pure-rule assertions passed.

The delayed-write cases use controlled coroutine scheduling and a fake datastore. They exercise the production persistence module but are not a Roblox engine or real DataStore service test. A server shutdown before its outstanding writes finish, or a sustained service outage, can still prevent a final save. No durability guarantee is claimed.

## Resume in Studio

1. Preserve the existing private v0.2.0 place.
2. Open the updated `Snackquake_Expedition_v0_2_Playtest.rbxlx`, or the `Brainrot_Rescue_Snackquake.rbxlx` bundled in the source archive.
3. Run the structural smoke check and the existing two-client rescue/disaster tests.
4. On a private published test copy, verify balances and collections after join/leave/rejoin, including departure during an autosave. Studio itself deliberately uses session-only data.
5. Keep the game private until the remaining tests pass.

No game pass was enabled, no real purchase was made, and no live player data was modified during this patch.
