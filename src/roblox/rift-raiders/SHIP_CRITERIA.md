# Rift Raiders — Finish Line / Public Launch Quality Gates

**Status as of v0.29 (2026-10-18): PROTOTYPE / PRIVATE.** Do not report the game as fully completed until all gates below have objective evidence. No public publishing, paid imports, licensing violations, or Robux activation without owner authorization.

## 1. Player fun — core experience
- [x] Clear first-time objective in under 30 seconds, with one-tap access to first interesting region.
- [x] Earned-coin job shifts, valid in-game purchases, responsive completion feedback, daily activities, real-world gardening, cars/boats, and a repeatable Suburban collectible loop.
- [ ] Have at least five independent first-time players play 15 minutes without guidance; record first confusion, completion time, and moments of fun/frustration. This requires people, not AI simulation.
- [ ] Make at least three popular careers truly tactile with suitable tools/animations, NPCs, meaningful timing/skill challenges and their own interiors rather than 2 generic task prompts. (v0.25 adds physically enterable downtown market/cafe rooms, grounded traffic, and earlier static venue assistants and courier package handling; the rest of the imported building interiors, animations, NPC depth, sound and observed playtesting are still incomplete.)
- [ ] Add natural social roleplay with invitations/permissions, emotes, readable names, meaningful two-player activities and explicit controls against griefing.
- [ ] Test route to enjoying the game in <5 min for fresh accounts without artificially gifting money during tests.

## 2. Art and physical world
- [x] Safely imported genuine official Modern City, Racing and Suburban template art with foreign executable scripts removed.
- [x] Two detailed official sedans, official Racing mesh, distinct original SUV/pickup/sports silhouettes.
- [ ] Replace each premium car class with a recognizable unique, properly licensed, verified and platform-permitted 3D mesh (including wheels/interior). Do not label placeholder 3D part assemblies photorealistic.
- [ ] Replace yachts, speedboats, jet skis with materially different 3D mesh hulls/details and driving/occupancy appropriate to each size.
- [ ] Verify human walk-through and gameplay in at least two original furnished, imported Suburban interiors. v0.26 restored six doors, and v0.28 relocates both furnished house interiors to their actual first floor surface with real sloped footpaths. Automated geometry now proves door heights/ground contact, v0.29 corrects voxel grass that buried roads/floors, and a Studio test computes humanoid navmesh routes through opened original front doors into both homes. Human walk-through of full rooms/stairs and mobile phone play remain required.
- [ ] Verify all developer-owned or officially reusable audio/material/mesh permissions on the actual owner account; eliminate noncompliant third-party asset loads.
- [ ] Improve lighting, sound effects, scenery transitions and visible/interactable NPCs; verify readability under LOW graphics. (v0.27 corrects reverse-facing *moving* traffic and removes emergency NPC position snapping; cinematic/realistic street behavior, light/audio and mobile rendering remain unverified.)

## 3. Economy and gameplay correctness
- [x] Server validates earned-currency shopping, valid career actions/wages, personal car ownership, boat ownership, gardening and collectible claim radius/replay.
- [x] Profile schema through v10 migrates earlier progression records in source; Studio unit/smoke tests exist.
- [ ] Run actual private test-game DataStore leave/rejoin checks and two-server simulations using a separate test place (never grant Studio write access to the owner's live production store).
- [x] Implement atomic session ownership/locking, retries, serialized in-server saves, and mock cross-server conflict tests. Live private-server acceptance tests remain required.
- [ ] Verify moderation and exploit rate limits for every RemoteEvent, server-side jobs and player-to-player action.
- [ ] Balance starter job pay, home ownership, starter vehicles, expensive vehicle unlocks and long-term progression through human playtests.

## 4. Performance and accessibility
- [x] StreamingEnabled and reduced tiny imported Suburban decorative collider/shadow expense.
- [ ] Measure CPU frame time, draw calls, unstreamed/streamed instance count and memory using Roblox Studio profiler.
- [ ] Actual Android/iOS lower-end-device tests, including driving, dense Suburbia, NPC traffic, water effects and user interface.
- [ ] Record device FPS distribution and performance targets before claiming 30/60 FPS. Do not fabricate performance benchmarks.
- [ ] Long-session (>30 minutes) leak/resource stress test; check client memory and network reliability on reconnect.
- [ ] Test gamepad, touch layout and accessibility/readability including compact aspect ratios.

## 5. Release control
- [x] Private GitHub repo branch, reusable source import scripts, reproducible Rojo place files, Studio smoke and 2-client scripted regression.
- [ ] Content age-rating and moderation review; creator experience identity and permission check.
- [ ] 4-player private live playtest + fresh account profile saves and no duplication between servers.
- [ ] Repeat tests after changing assets, collisions, rewards or transactions.
- [ ] Explicit owner approval for public release and any real Robux monetization.
- [ ] Monitor actual error/performance/retention metrics only after release access is approved; no invented engagement claims.

## Development order and next recommended focused releases

1. **v0.18 Visual fidelity:** source and test legally suitable high-detail cars/interiors; use local Roblox templates/approved Creator Store/open-license models. Build a visual comparison in Studio to confirm real improvement, not just file counts.
2. **v0.19 Social and job depth:** one excellent cafe/retail mini-game and one vehicle/garage job plus NPC interaction/animation, with proper teammate/co-op.
3. **v0.20 Save reliability & performance:** private-place DataStore rejoin and server concurrency, remote rate limits, mobile profiling and scene optimizations.
4. **v0.21 Human-playtest polish:** tune tutorial and first-ten-minute content based on *real* playtester observations.
5. **Candidate release:** only after all gates above are verified and owner approves.

**Reference patterns** from publicly available Roblox Developer documentation and open-source architecture:
https://create.roblox.com/docs/production/game-design/onboarding
https://create.roblox.com/docs/production/analytics/retention
https://create.roblox.com/docs/performance-optimization/improve
https://github.com/matter-ecs/matter
https://github.com/Quenty/NevermoreEngine

A large, appealing social-life game cannot be judged finished from a catalog item count or Studio smoke test alone.
