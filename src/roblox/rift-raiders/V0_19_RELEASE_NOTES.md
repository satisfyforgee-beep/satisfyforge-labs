# Rift Raiders v0.19 — Downtown First Impression & Visitor Plaza

**Private development milestone.** This release addresses the user's real 16.6-second Roblox Studio gameplay video, in which the avatar initially faced bare gray asphalt and the imported Modern City shops became apparent only after the camera turned.

## Actually implemented

- Spawn remains at the same safe Modern Downtown position, but the avatar now faces **toward the detailed imported storefronts**, instead of staring across a wide blank street.
- Added a compact physical first-minute plaza: **40 sandstone sidewalk pavers**, **5 cloned official Roblox Modern City mesh trees** (script-free), flowering brick planters, two wood-and-metal benches, a low decorative reflective fountain with subtle particles, modest warm streetlamps and welcome signage. These supplement rather than replace or rebrand licensed Roblox Studio template geometry.
- Added an **interactive Suburbia Visitor Center** kiosk near spawn. Walking up to it and using the proximity prompt moves the player to the official Suburban map. The same server-authoritative first-session "Travel to Suburbia" objective progresses if the kiosk is used; no free earned-coin rewards from a spoofed client call.
- Relocated the first-session guide and daily progress widgets below the default Roblox top-left menu buttons. Maintains the existing compact four-button navigation. No new third-party HUD dependencies.
- Existing careers (60), catalog items (173), boats, owned cars, estate houses, gardening, daily objectives, collectibles, bean-and-brew mini-game, and session-locked data stores remain unmodified.

## Verification

- Roblox Studio smoke test validates the new version, the 5 real imported mesh trees, 40 pavers, fountain, benches, graphic, kiosk interaction and the opening character heading toward actual city buildings.
- Full 2-player Roblox Studio regression verifies the previous career/commerce, saving-safe on-device game logic, and multiplayer gameplay remain functional.
- This release does **not** prove camera composition will look good on every screen resolution or mobile device. Human screenshot review, device testing, streaming performance, and Roblox-hosted asset permissions remain release gates.
- There may still be warnings for some template textures that Roblox reports as noncompliant; don't mistake testing with a correct build for proof every asset will show for every user.
- The game is not publicly published. Robux monetization remains disabled. No money was spent.

## Next major goal

Use a human first-play review of v0.19 to choose more exact storefront-scale landscaping and key sights; if mobile frame rate suffers, reduce tiny noninteractive parts and shadow casters, adjust streaming budgets, and prioritize validated reusable high-detail imported meshes over unlicensed asset imports. The persistent "Rift Raiders Development" scheduled task independently revisits a concrete, tested game improvement every hour when tool access is available; no extra "continue" requests are required.
