# Rift Raiders v0.27 — Dynamic Traffic Heading & Natural NPC Recovery

Date: October 18, 2026. Private, free, non-published development candidate.

## Problem fixed

Owner-reported traffic appeared to drive backward even after v0.25. Root cause confirmed by source review: v0.25 corrected the initial orientation of the official detailed SedanVisual, but the `DowntownPopulation` Heartbeat update still applied a **180° yaw** every time it advanced a car. The traffic orientation tested at spawn was correct; as soon as it moved, the model drove tail-first.

## Code changes

- Traffic cars now continuously face forward at runtime; their physical heading and actual headlamp/front-bumper direction agree. Cars slow down as they approach corners rather than maintaining full speed through instant 90° turns.
- The visual car yaw blends smoothly into the next street direction. Traffic remains intentionally non-colliding and route-following, not full wheeled suspension or collision-aware navigation.
- Every traffic car records `DynamicFacingChecked`, `ForwardTravelHeadingDot`, and `SteeringMode=ProgressiveYaw`, so developer tests can detect regressions after motion begins.
- When one of the eight R15 downtown citizens is blocked at a route waypoint, its movement recovery no longer snaps/teleports it directly to the destination. The NPC tries a different waypoint without teleporting; `WaypointRecoveryCount` supports debugging.
- Preserved all v0.26 physically opening imported suburban house/store/garage doors, downtown shop interiors, purchases, careers, vehicles, courier package validation, and persistence logic.

## Verification

- Rojo v0.27 project builds to a local Roblox Studio place.
- Real Roblox Studio v0.27 smoke script passed, verifying that all four moving Sedans remain oriented toward their headlights *after recorded travel*, that their steering mode is progressive, and that R15 citizens are configured not to teleport on route recovery.
- Full two-client Studio regression: refer to `V0_27_QA.md` for actual outcome and known environment blockers. Do not claim a full pass based on a single smoke test.

## Still unverified

Manual ground-level driving/steering and actual long-term traffic-corner visuals; genuine navmesh pathfinding; original imported market/house/garage interiors throughout; mobile FPS, asset permissions, real player save/rejoin, four-player live server, player retention and moderation checks. A previous Studio run intermittently reported noncompliant external asset IDs, so all visible asset delivery is not established. No public game release or Robux enabled.
