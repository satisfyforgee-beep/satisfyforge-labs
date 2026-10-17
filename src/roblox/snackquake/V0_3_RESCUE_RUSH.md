# Snackquake Rescue Rush v0.3 — private gameplay redesign

Date: 2026-10-17. **Status: published to the existing PRIVATE Snackquake place as version 5; not public and not earning Robux.**

## Why this version exists
An actual 20-second Android recording showed a dim, visually empty arena, a very large top HUD, and unclear rewards. The goal is a fun first minute, not just passing source checks.

Gameplay references researched: Roblox Steal a Brainrot creator gameplay (`https://www.youtube.com/watch?v=mPptEyUCJD8`), emphasizing understandable collection goals, visible progression and social stakes. All Snackquake creatures, level layouts and mechanics remain original; no third-party video, code or game art was copied.

## Player-facing improvements
- First task displayed immediately: grab a creature, then bank it at the green chute.
- One server-authoritative golden creature near the starting path each round; +25 earned Fizz bonus on successful bank. Golden cannot be farmed repeatedly in the same round.
- Server-authoritative rescue streak: 24-second combo window, up to x5, with +4 Fizz per additional combo step. Disaster bounce breaks the streak. Both golden and combo awards respect the 10,000,000 Fizz cap and existing DataStore schema.
- 72-second rounds, disaster warning at 22 seconds and panic at 29 seconds, 7-second breaks; previous round length was 105 seconds and warning at 55 seconds.
- Daytime lighting, colorful perimeter landmarks, glowing golden starter beacon, neon rescue runway, smaller HUD, clear danger bar and mobile-sized navigation.
- Collection view switches to a single column on narrow phones. Mobile dash is hidden during inter-round voting to avoid obstructing choices.
- No paid content enabled: `FounderGlowPassId=0`. No ads, boosts, purchases, trials or new services.

## Tests actually run on authorized Mac
- Lua 5.4-compatible source parsing: 9 files; persistence regression: 20 assertions; pure rules: 9,046 assertions — PASS.
- Roblox Studio runtime smoke: 19 embedded structural assertions, 0 failures — PASS; source version 0.3.0-rescue-rush.
- Existing Studio two-client isolation test: both upgrades, unauthorized equip/fuse, insufficient funds — PASS.
- New Studio two-client real prompt test: golden pickup, bank with +25 Fizz, next rescue +4 combo bonus, other player's wallet and rescue count unaffected — PASS.
- New Studio phone-shaped viewport checks: iPhone 16 portrait/landscape and Samsung Galaxy A06 portrait/landscape — PASS after fixing a too-wide navigation row and controls overlap.
- Still **not** established: actual Android v0.3 playtest, extended real multiplayer retention/performance, production cloud save leave/rejoin on this version, public release, or earnings.

## Run tests
```sh
python3 src/roblox/snackquake/tests/run_tests.py
python3 tools/roblox-studio/run_smoke.py --game snackquake --keep-artifacts
python3 tools/roblox-studio/run_snack_multiplayer.py --keep-artifacts
python3 tools/roblox-studio/run_snack_rescue_rush.py
python3 tools/roblox-studio/run_snack_mobile.py --keep-artifacts
```

Rojo build: `~/SatisfyForge/tools/rojo/rojo build src/roblox/snackquake/default.project.json -o /tmp/snackquake-v03.rbxlx`.

## Verified private deployment
- Roblox Open Cloud returned published place version **5** on 2026-10-17.
- Universe **10769808558**, place **87195614010796**, exact Rojo place SHA-256 **604ab95105be9a6b482b846384e8540a5e03f86cdf306c64281f3c3fe4d7ba08**, 68,834 bytes.
- Existing private access and DataStore name were not changed by the place-version upload. No game pass was enabled.
- Actual owner Android join of **version 5** remains to be verified.

## Release policy
Deploy only to the already verified existing **private** Snackquake place, universe `10769808558`, place `87195614010796`, after tests pass. No public access changes, no new paid products, no DataStore schema reset. Retain the exact SHA-256 and returned Roblox place version in release notes. Owner should rejoin private experience on Android and report fun, readability, lag, controls, and whether first golden rescue works.
