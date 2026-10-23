# Rift Raiders v0.29 — Make Suburban Streets and House Interiors Actually Passable

**Date:** October 18, 2026 (America/New_York). Private, no-cost development build.

## Confirmed root cause, not just an appearance tweak

A v0.28 engine audit of player-height interior positions revealed that even though the official detailed homes were moved so their actual first-floor surfaces sat at Y=1.8, the surrounding voxel-generated **grass collision surface** was Y=2.515625. The Roblox Terrain `FillBlock` requested a Y=.5 upper surface geometrically, but terrain voxelization created an actual higher walking surface. The ground was therefore **covering building floors and masking/partly burying roads**. The previous check used theoretical volume/bounding minima rather than a physics raycast, so it had missed this.

## Source changes

- Adjusted only the **local Suburban Town grass Terrain FillBlock**, leaving other worlds unchanged. The Grass FillBlock is now centered at Y=-8 rather than -6 while preserving area/size/material.
- The actual Roblox physics result at a verified open-grass sample is **Y=.5**. The asphalt road's real upper face remains **Y=1.375** and the furnished houses' original real ground floors **Y=1.8**, so visible streets and interiors are no longer under the grass.
- Added physics-raycast regression assertions in the canonical Studio smoke test, so this cannot silently regress to buried/impassable roads.
- Added a separate Studio `PathfindingService` and collision/navmesh test for both original imported houses. The audit temporarily simulates already-opened original source door panels inside its disposable test world, then checks grounded destinations and computes actual valid humanoid navigation paths from outside toward the original furnished living areas, rejecting a missing route. The real game still uses its previously tested server-authorized nearby open-door prompt and animation—not an untrusted imported door script or teleporter.
- Kept the original v0.28 floor alignment and walkways, v0.27 forward-driving traffic, v0.26 imported interactive doors and courier security, previous jobs, money checks and saves.

## Limits

- Studio navmesh availability does **not** prove a human's real camera, keyboard, touch or gamepad navigation through every room/staircase is comfortable. Live-human, physical phone and multi-server persistence acceptance remain open.
- No changes to save schema, live production DataStores, Robux, public release, monetization or connected account identity.
- The source asset permission warnings and Roblox UI style warnings remain separate known issues.

See [V0_29_QA.md](V0_29_QA.md) for verified final results rather than interpreting a successful build as a finished public game.
