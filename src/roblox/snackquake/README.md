# Brainrot Rescue: Snackquake — v0.2.1-save-fix

Recovered into the Master Command Center from the canonical Library archive `Snackquake_Expedition_v0_2_Source.zip` (Library version 4) on 2026-10-13.

This is a **separate alternate Roblox project**. It does not replace Brainrot Rush as the current primary project unless later player evidence makes that a better decision.

## Verified source state

Fresh local regression run on 2026-10-13 against the recovered v0.2 archive:
- 9 Lua-compatible Luau source files parsed
- 38 mocked persistence assertions passed
- 9,046 pure-rule assertions passed
- source archive extracted cleanly

The recovered place/config identifies the embedded version as `0.2.1-save-fix` with 105-second rounds and production DataStore name `SatisfyForge_Snackquake_v1`.

The v0.2.1 patch specifically repaired a departure/save race in which progress earned while a slow autosave was still in flight could otherwise be lost during `PlayerRemoving`. The patched writer retains the closing profile, drains the newest final snapshot, releases the lease, rejects new autosaves on closing profiles, keeps duplicate releases idempotent, and still refuses writes after ownership changes. A delayed-autosave regression test fails on the old behavior and passes on this build.

## Verified Roblox Studio engine state

On 2026-10-13 the recovered v0.2.1 source was built with Rojo and executed through the real Roblox Studio `RunScript` task on the authorized Mac.

The exact 63,966-byte Rojo build used for deployment passed the external runtime smoke and the embedded Studio smoke:
- `SF_SMOKE_PASS Snackquake`
- embedded version: `0.2.1-save-fix`
- 15 rescue spots found
- 6 high-ground refuges found
- embedded smoke checks: 15 passed / 0 failed

This proves the tested build loads and executes in Roblox Studio and generates its required runtime world. It does **not** prove multiplayer, real-device controls, production DataStore behavior, purchases, retention, or public-release readiness.

## Verified private deployment

A Roblox Open Cloud API key was created with the minimum required `universe-places:write` scope restricted to the Snackquake universe. Its scope was introspected before use.

The exact Studio-smoke-tested Rojo build was then uploaded through Roblox's supported existing-place publishing API on 2026-10-13:
- Universe ID: `10769808558`
- Place ID: `87195614010796`
- returned Roblox place version: **4**
- experience access remained **Private** before deployment; no public-access setting was changed by the publishing workflow

The API key itself is stored only in macOS Keychain on the authorized local Mac and is not committed to this repository.

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

## Still required before any public launch claim

- real private-experience client playtest from spawn through rescue/deposit/evolution/upgrade/disaster loops
- two-client contention/shared-event test
- private cloud save + leave/rejoin verification
- unavailable-DataStore fallback check in a production-like path
- phone portrait/landscape and real-device test
- gamepad test
- long-session cleanup/performance test
- analytics readback
- any optional purchase/pass path test
- moderation/metadata/public access checks
- real-player retention/playtest evidence

Do not call Snackquake public, released to players, popular, or earning revenue until those gates are actually passed.

## Canonical preserved artifacts

The exact latest source package and historical playtest place remain preserved in the user's Library:
- `Snackquake_Expedition_v0_2_Source.zip` — version 4, recovered size 62,646 bytes
- `Snackquake_Expedition_v0_2_Playtest.rbxlx` — embedded version `0.2.1-save-fix`

The authorized Mac also holds the current recovered source, Rojo project, local tests and the exact deployment artifact used for private place version 4. The remaining task is to finish remote-source canonicalization and the release gates above without weakening the private/testing boundary.