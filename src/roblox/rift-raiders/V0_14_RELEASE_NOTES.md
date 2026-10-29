# Rift Raiders v0.14 — Detailed Roblox Template Asset Integration

## Why this release matters

The user wanted detailed, reusable environments and vehicles rather than another round of primitive block-generated placeholders. This release imports real assets from the **official Roblox Studio Racing and Suburban templates**, preserving their visual models, textures and detailed assemblies while removing all source scripts. New original procedural geometry is also used for specific distinct vehicle bodies and functional upstairs rooms. No expensive plugins, outside subscriptions, or paid assets were used.

## High-detail official assets successfully imported

- **Racing template car:** 29 original MeshParts with SurfaceAppearance assets, from the template's Car model. All gameplay scripts, audio, remotes, constraints, and executable content were removed. Saved as `assets/OfficialRacingCarVisual.rbxmx`. Available in the vehicle dealer as **Professional Racing Car**, an earned-coin purchase gated at level 28, then selectable in the garage and drivable through the existing server-verified car seat. The official art is a racing/buggy-style car, not a street hypercar.
- **Suburban template architecture:** 6 complete detailed building/scene prefabs saved as `assets/OfficialSuburbanArchitecture.rbxmx`. These include a single-story house (896 visible/collidable pieces), two-story home (1,771), convenience market (1,208), gas station (932), garage (245), and playground (525). They are largely assemblies of detailed Parts, **not** dense MeshParts or PBR imported meshes. All scripts were stripped and two inaccessible legacy textures removed.
- **New SUBURBIA region:** the six source prefabs are now placed in a dedicated neighborhood, away from the 18 existing regions, with roads and signs. WORLD → SUBURBIA allows exploration. Prefab appearance is retained but their original demo functionality/scripts were not imported; Suburbia shops are currently environmental rather than economic storefronts.
- Existing official Modern City 13-building environment and official red/white detailed sedans remain in the game.

**Reproducible source imports** (local official template originals are saved only on the authorized MacBook and are not committed):

```shell
python3 tools/roblox-studio/extract_official_racing.py ~/Documents/RACING_OFFICIAL.rbxlx src/roblox/rift-raiders/assets/OfficialRacingCarVisual.rbxmx
python3 tools/roblox-studio/extract_official_suburban.py ~/Documents/SUBURBAN_OFFICIAL.rbxlx src/roblox/rift-raiders/assets/OfficialSuburbanArchitecture.rbxmx
```

## Interactive systems completed in this release

- Ten earnable selectable personal driving options. Six previously identical-looking vehicle choices now have new, original detailed modular SUV, pickup, electric crossover, supercar, hypercar and classic-coupe body silhouettes, separate wheel geometry and different top-speed settings. These models are **not** equivalent to premium photorealistic purchased meshes.
- Multi-story homes have an open stairwell, physical stair steps, split-level walkable upper floors, upstairs bedrooms and owner-validated floor-access lifts. The expensive house tiers receive visibly different architectural details, but they are not yet unique, hand-designed interiors.
- More house purchases now produce visible functional equipment: installed security camera, robot vacuum, BBQ grill, hot tub, patio dining, cat tree, dog house, solar panels, and optional swimming pool. Interactive appliances recover needs on cooldowns.
- The saved-profile schema increments to v8 while preserving v1–v7 player progress and owned goods. All transactions remain in **earned fictional game coins**.

## Quality, validation and security

- Rojo build completed, Roblox Studio smoke test passed, and isolated two-player multiplayer test passed. Checks cover the genuine 29-MeshPart racing body, all six imported Suburban prefabs, script stripping, individual vehicle types, player authority over cars and gardens, and the new SUBURBIA travel destination.
- Source templates were opened from Studio's built-in official templates. External unknown Toolbox or Creator Store scripts are not executed.
- A curated import approach avoids copying the entire 85MB Suburban or Racing demo experiences. However, the resulting v0.14 place is larger (approximately 47MB) and the suburb has thousands of separate detail parts.
- Streaming is enabled, but **real Android/iOS performance, network-loading speed, phone frame rate and memory use have not yet been verified**.
- The Roblox Studio smoke tests **do not verify live DataStore persistence**; that requires testing within a connected published Roblox experience with API access. No public game was published as part of this update.
- The Racing art and imported Suburban buildings depend on Roblox-hosted asset availability and permissions. A visual comparison in the target experience is still necessary to find unavailable textures/materials.
- No actual Robux purchases, monetization, live publishing or paid plugin installation.

## Still to build to approach GTA/Sims quality

Realistic deformable vehicle chassis and suspension; collision-aware street traffic; animation blending and facial rigs; photorealish PBR for each vehicle and home; connected interactive Suburbia shops and schools; persistent addresses for larger player populations; multiplayer housing permissions with persistent access logs; dynamic house furniture layout; complete gardening tools and produce delivery animations; actual mobile QA; save/rejoin stress tests; content moderation review; and substantial ongoing balancing and art direction.

This release makes tangible progress toward imported higher-detail art, but it **does not** finish every system or make the entire game high-end. For the next milestone, target verified asset permissions, car physics, performance budgets and converting decorated suburban shops into real playable businesses before adding more catalog entries.
