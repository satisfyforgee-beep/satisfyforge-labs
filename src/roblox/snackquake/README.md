# Brainrot Rescue: Snackquake — v0.2.1-save-fix

Recovered into the Master Command Center from the canonical Library archive `Snackquake_Expedition_v0_2_Source.zip` (Library version 4) on 2026-10-13.

This is a **separate alternate Roblox project**. It does not replace Brainrot Rush as the current primary project unless later Studio/player evidence makes that a better decision.

## Verified source state

Fresh local regression run on 2026-10-13 against the recovered v0.2 archive:
- 9 Lua-compatible Luau source files parsed
- 38 mocked persistence assertions passed
- 9,046 pure-rule assertions passed
- source archive extracted cleanly

The recovered place/config identifies the embedded version as `0.2.1-save-fix` with 105-second rounds and production DataStore name `SatisfyForge_Snackquake_v1`.

The v0.2.1 patch specifically repaired a departure/save race in which progress earned while a slow autosave was still in flight could otherwise be lost during `PlayerRemoving`. The patched writer retains the closing profile, drains the newest final snapshot, releases the lease, rejects new autosaves on closing profiles, keeps duplicate releases idempotent, and still refuses writes after ownership changes. A delayed-autosave regression test fails on the old behavior and passes on this build.

## Existing game systems

- eight original snack creatures
- rescue/carry/deposit loop
- three food-disaster events
- 105-second rounds with warning/panic timing
- duplicate fusion/evolution
- speed upgrades
- dash
- team frenzy
- round voting
- touch/gamepad/keyboard bindings in source
- UTC daily login streak and daily rescue mission
- server-side reward/interaction validation
- DataStore leases/autosave/shutdown release with explicit session-only fallback
- analytics hooks
- optional Founder Glow cosmetic-pass path, disabled while pass ID remains 0

## Historical Studio milestone

An earlier v0.2.0 place was opened in Roblox Studio, a solo character spawn was observed, and a private experience save was completed. That is useful continuity, but it does **not** validate the v0.2.1 patch or the complete gameplay loop.

## Still required before any launch claim

- import the current v0.2.1 build into Roblox Studio
- inspect the included Studio smoke result and Output
- complete rescue/deposit/evolution/upgrade/disaster tests
- two-client contention and shared-event test
- phone portrait/landscape and real-device test
- gamepad test
- long-session cleanup/performance test
- private cloud save + leave/rejoin verification
- unavailable-DataStore fallback check
- analytics readback
- any optional purchase/pass path test
- moderation/metadata/public access checks
- real-player retention/playtest evidence

Do not call Snackquake live, released, popular or earning revenue until those gates are actually passed.

## Canonical preserved artifacts

The exact latest source package and playtest place remain preserved in the user's Library:
- `Snackquake_Expedition_v0_2_Source.zip` — version 4, recovered size 62,646 bytes
- `Snackquake_Expedition_v0_2_Playtest.rbxlx` — embedded version `0.2.1-save-fix`

This repository intentionally records the project truth and test evidence without pretending GitHub's generic Lua environment is Roblox Studio.
