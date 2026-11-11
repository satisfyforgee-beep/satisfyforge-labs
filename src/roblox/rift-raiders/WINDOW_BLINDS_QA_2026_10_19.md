# Rift Raiders — Original Window Blind Controls (October 19, 2026)

**Status:** Verified isolated development candidate on `automation/rift-blinds-20261019-1714`, based on v0.30 (`7583330`). The in-game version is deliberately still `0.30.0`; this is not a numbered public release.

## Material gameplay change

- Restored **21 interactive original window-blind assemblies** in the two official imported furnished Suburban houses: 10 in the single-story house and 11 in the two-story house.
- All **422 original noncolliding anchored slats** remain in the environment. Players operate the actual slats using a physical pull-rod ProximityPrompt. A 0.42-second server-owned TweenService animation compacts slats at the top, and lowering restores their exact original CFrames.
- Interactions require a living player within 11 studs, enforce a 0.65-second per-window cooldown, and synchronize shared session state between players. No currency, profile schema, or DataStore modifications; no untrusted source scripts.
- Existing house lighting, doors, jobs, collisions and imported meshes remain intact.

## Objective test evidence

- Source asset XML audit: 42 nodes named `Blinds`, 21 actual `Raise` rods and nested slat folders; 422 anchored noncolliding source parts.
- **Rojo build PASS:** `/tmp/satisfyforge-rift-blinds-1806.rbxlx`, approximately 48 MB.
- **Real Roblox Studio smoke PASS:** `/tmp/satisfyforge-rift-blinds-1806-smoke.log`; `SF_RIFT_CHECK original_furnished_window_blinds PASS 21`, all existing smoke assertions, `SF_RIFT_SMOKE_PASS`; no CreatorError lines.
- **Full two-client Studio regression PASS:** `/var/folders/kz/1bl7f14d26gfpsszdfwd64ch0000gn/T/satisfyforge-rift-mp-99da137p/studio.log`; `SF_RIFT_MP_CHECK original_furnished_window_blinds_shared_physical_motion PASS`, `SF_RIFT_MP_SERVER_PASS players=2`, `SF_RIFT_MP_RESULT ok=true result=PASS:rift_multiplayer`, `SF_RIFT_MP_PASS`. Verified remote player rejection, valid local activation, actual slat displacement, cooldown, second-player restoration, and unchanged coins.
- `git diff --check` PASS.

## Remaining limitations and release blockers

These automated tests do **not** establish visual appeal on a real phone, animation smoothness at low FPS, room-by-room human traversal, or native Android/iOS performance. The original v0.30 release gates in `SHIP_CRITERIA.md` remain open, especially actual phone QA, private DataStore leave/rejoin, asset permissions, human playtests, and owner public-release approval.

No purchases, public uploads, Robux, production saves, account changes, or owner-file overwrites.

## Final independent verification — October 19, 2026, 9:10–9:14 p.m. EDT

- Fresh Rojo build: `/var/folders/kz/1bl7f14d26gfpsszdfwd64ch0000gn/T/satisfyforge-rift-blinds-final-smoke-ockpp8f6/rift-raiders.rbxlx`, **49,843,809 bytes**, successful.
- Fresh real Studio smoke: `rift-raiders.studio.log` in the same directory; `SF_RIFT_CHECK original_furnished_window_blinds PASS 21`, `SF_RIFT_SMOKE_PASS`, runner exit 0.
- Fresh complete two-client Studio regression: `/var/folders/kz/1bl7f14d26gfpsszdfwd64ch0000gn/T/satisfyforge-rift-mp-8jz48eyf/studio.log`; `SF_RIFT_MP_CHECK original_furnished_window_blinds_shared_physical_motion PASS`, `SF_RIFT_MP_CHECK physical_courier_pickup_route_pay_no_duplicates PASS`, `SF_RIFT_MP_SERVER_PASS players=2`, `SF_RIFT_MP_RESULT ok=true result=PASS:rift_multiplayer`, runner exit 0.
- The courier server's pickup range was corrected from 6 to 8 studs to match the actual 8-stud prompt; diagnostic in the passing test recorded an accepted pickup at 4.85 studs. A previous complete multiplayer run also passed, but the precise root cause of intermittent earlier failures is not conclusively established.
- `git diff --check` passed. No user Studio session, historical v0.21 place, or lockfile was altered.
- Outstanding: Roblox Studio reported noncompliant asset loads (including IDs `118068658940906` and `82237784671515`) and `RoundedCorner8` style warnings; these require provenance/permissions and UI review. Real low-end phone profiling, human room traversal, and private DataStore rejoin testing remain unverified.
