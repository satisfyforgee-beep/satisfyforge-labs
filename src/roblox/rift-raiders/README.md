# RIFT RAIDERS: CHAOS ISLANDS

An original multiplayer Roblox game, created separately from all existing SatisfyForge games.

## Playable loop (v0.5 prototype)

Spawn at the central hub. Use the WORLD menu or one of four skybridges to reach Neon Metropolis, Prism Wilds, Magma Outpost, or Cloud Kingdom. Collect 36 scattered shards, BLAST 12 roaming drones, spend 12 shards to seal one of four rifts, level up, earn coins, and unlock upgrades. Complete repeatable missions for bonus coins. During a periodic 25-second Rift Surge, eligible coin rewards double. Cloud Kingdom includes a five-platform summit challenge. Version 0.2 added reusable scenery, arcade hovercars and two aimable sci-fi guns. Version 0.3 expanded the map with seven terrain worlds, reusable prefabs, portals, snowmobiles, jetpacks and flying cars. Version 0.4 adds a sports complex, housing neighborhood, resource gathering, crafting, fishing and wildlife minigames, fictional heists and vehicle jobs, plus player-profile schema v2.

[Public-launch finish line and measurable quality gates](SHIP_CRITERIA.md) — this project remains a private prototype until all launch criteria pass.

## Implemented

- **v0.18 Playable Cafe & Safer Data:** New in-world coffee bar with three real drink recipes and randomized, server-verified customer orders; serving the right drink gives one earned-coin tip, then the barista collects normal career wages. New DataPersistence module adds atomic session ownership, clean release, retries, sequential saves, safer server shutdown and synthetic DataStore conflict tests without writing to the owner's live Roblox account during Studio testing. **Live private-place DataStore rejoin and mobile tests remain outstanding.** See [V0_18_RELEASE_NOTES.md](V0_18_RELEASE_NOTES.md).


- **v0.17 Neighborhood Discovery Trail:** Eight physically hidden, glowing collectibles give a new server-authorized exploration loop in the official Suburban-template neighborhood. Each pays 20–34 earned coins and XP once per player per UTC day; completing all eight gives a 180-coin/45-XP bonus. Progress persists in save schema v10 (v1–v9 migration) and appears on the first-session HUD and LIFE → MY GOALS. Server validation checks proximity, alive character and duplicate claim. Roblox Studio smoke tests and two-player exploit/isolation regression tests cover this loop. [V0_17_RELEASE_NOTES.md](V0_17_RELEASE_NOTES.md) has detailed rules, art limitations and remaining launch gates.


- **v0.16 Guided First Session & Daily Life Challenges:** a compact, non-modal in-world tutorial leads players through first suburb visit, a valid purchase, first job application, and completing a career shift; each verified milestone pays a one-time earned-coin bonus and XP. Four daily goals (work, eat, visit the suburb, harvest gardening crops) reset by UTC day, pay nonrepeatable fictional coin bonuses and appear in LIFE → MY GOALS. Server validators exclusively award achievements; player data moves to saved schema v9 with v1–v8 migration. The real imported Suburban environment now strips collision and shadows from tiny decorative parts without removing its floors, walls, and usable service counters. See [V0_16_RELEASE_NOTES.md](V0_16_RELEASE_NOTES.md) for rewards, tests, researched retention principles, and important remaining limits.


- **v0.15 Interactive Official Suburbia:** The six official Roblox Suburban-template prefabs are no longer just passive scenery. Convenience Market can sell HOME/GARDEN/TECH goods and hunger-restoring earned-coin snacks, the garage and gas station allow vehicle dealer access and roadside snacks, and the playground offers free public rest. Four physical career locations (retail, mechanic, courier, security) have hire, start/finish shift and two task prompts, using the same server-validated wage/purchase rules as the main city. Two-player tests verify an actual paid Suburbia purchase, remote-purchase prevention, and unauthorized vehicle-selection rejection. Keeps saved-data schema v8, 60 careers, all earlier destinations and Robux features disabled. See [V0_15_RELEASE_NOTES.md](V0_15_RELEASE_NOTES.md). Imported assets are detailed, but not every prefab component is a MeshPart or photorealistic PBR asset.


- **v0.14 Official Racing + Suburban Visual Packs:** Opened and safely extracted reusable art from the built-in Roblox Studio Racing and Suburban templates. The new earned-coin **professional racing car uses 29 actual MeshParts**, and the new explorable **SUBURBIA** destination has six detailed official prefabs (two houses, convenience market, gas station, garage and playground). The game retains its detailed Modern City downtown. Ten purchase-gated road vehicles are selectable; six non-sedan choices now have separate original modular SUV, pickup, electric crossover and sports silhouettes, though those are not imported photorealistic meshes. Multi-story owned houses now have actual upstairs walkways, bedrooms and floor access. More purchased home items (BBQ, spa, camera, pet furnishings, pool, solar and robot vacuum) appear physically. Saved profile schema v8 migrates v1–v7. **All template scripts were removed.** The source and exact remaining limitations are in [V0_14_RELEASE_NOTES.md](V0_14_RELEASE_NOTES.md).


- **v0.13 Real Home Living & Garage:** 12 landscaped, owner-allocated estate lots with official Modern City mesh trees; functional homes for eleven residential property purchases; physical purchased furniture and household appliances; lockable doors, owner-only interactions, saved security setting, and a fourth Fun lifestyle need. Seven server-authorized sedan-based car choices now use **both the red and white official 45-mesh Roblox city sedan models** and different arcade driving speeds. New LIFE → GARAGE, MY HOME and WORLD → ESTATES destinations. The updated saved profile is v7 with v1–v6 migration. [V0_13_RELEASE_NOTES.md](V0_13_RELEASE_NOTES.md) gives tested features and important quality limitations.


- **v0.12 Careers, Gardening & Marina:** 60 real-world-inspired careers (40 newly added), 173 earnable purchases (125 newly added), and 22 owned business choices. Players can buy a garden trowel, watering can and consumable seed packets, tend one of 16 personal raised garden beds with 14 crop varieties, water crops, harvest produce, and sell it at the Farm Market. Equipment can be held as tools. Nine owned watercraft (kayaks through superyachts) can be launched, boarded, steered and driven in the new WATERFRONT zone, with tier-specific arcade speed limits. Gardens and seed inventory are persisted in profile schema v6, migrated from v1–v5. All are server-validated and use earned coins. **Boats and crops are stylized gameplay prototypes, not photorealistic meshes**; many new catalog items are ownership records rather than equipped, usable products. The v0.11 Social Citizens conversation/hair work is preserved. See [V0_12_RELEASE_NOTES.md](V0_12_RELEASE_NOTES.md).


- **v0.11 Social Citizens:** downtown R15 citizens now use verified classic hair accessories and can be approached with a TALK prompt. Each citizen has a name and contextual city dialogue about jobs, stores, needs, business ownership, police and travel. Conversations are informational and do not grant free currency or bypass progression.
- **v0.10 Living Downtown:** eight server-created R15 citizens now walk real sidewalk routes through Modern Downtown, and four detailed traffic sedans made from the official Modern City car art circulate around the district. The pedestrians use actual Humanoids/R15 rigs and MoveTo walking rather than the old block-person placeholders. Traffic remains server-driven visual AI, not full chassis simulation.
- **v0.9 Downtown Life Integration:** the imported Modern Downtown is now a real gameplay district, not just scenery. Six street-facing shops, one clean employment center, all 20 careers, 19 two-step work loops, creator recording, business revenue collection, court payments, public food/rest services and two police patrols are wired directly into the detailed city. The Life catalog now contains 48 in-game purchases, including more clothing, technology, home goods, properties and nine business ownership options. The LIFE menu is split into Careers and Shopping with category filters so it stays usable on desktop and mobile. All purchases still use earned in-game coins; no Robux products were activated.
- **v0.8 Official Modern Downtown:** imported 13 actual Roblox Modern City template buildings, 59 street/prop groups, 1,880 detailed MeshParts, original PBR materials, and a 45-mesh sedan. Players now **spawn in the imported downtown**, with a new WORLD destination and physical wayfinding signs to Life City jobs and the original hub. Cars use the detailed official sedan as the visual shell, keeping the tested server-owned VehicleSeat controls. Mobile-friendly Workspace streaming is enabled. The file opens with an actual city view in Studio edit mode (not a blank sky), and the HUD starts compact, with DETAILS and ACTIONS drawers. Citizens start without sci-fi weapons in the city; those tools are available in the fantasy worlds. See [OFFICIAL_ASSET_PIPELINE.md](OFFICIAL_ASSET_PIPELINE.md) for source, safe extraction, reuse, limitations and future plans. This is a real improvement to visual quality, but still not a complete photorealistic simulation.


- **v0.7 Life City:** new detailed destination with storefronts, 20 careers, two-stage workplace tasks, a 28-item in-game catalog (apparel, phones/cameras, cars, boats, homes, businesses), creator videos and follower growth, business collection, furnished owned home ground floors, hunger/energy/hygiene, ambient city traffic/citizens, police pursuit, in-game jail and fines. Player profile schema v5. See [LIFE_SIMULATION_DESIGN.md](LIFE_SIMULATION_DESIGN.md). Boat purchases are inventory-only, not drivable. No real-money transactions.



- **v0.5:** natural lighting/atmosphere/clouds and cycling day/night/weather, decorative walking pedestrians and moving city traffic, LOW/MED/HIGH graphics settings with local rain effects.
- **Earned prestige economy:** eight permanent cosmetics/upgrades and advanced vehicle licenses with level and resource requirements, server-validated purchases, car wraps, upgraded roof lighting, luxury garage and character trail.
- **Save migration:** DataStore profile v3 preserves prior v1/v2 progress and allowlists owned prestige items; no Robux payment products or purchases activated.



- Football field-goal, baseball batting and soccer penalty timing minigames with animated shot visuals.
- Marina fishing with fish inventory/market sales; non-graphic safari wildlife tracking.
- Farm wood and city scrap metal gathering; toolkit crafting at hub workshop.
- Fictional bank-vault heist (level 3), NPC car theft/delivery (level 2), cooldowns and wanted heat.
- Housing Meadows: twelve plots, craftable furnished houses at level 2, ownership persisted across sessions.
- Server-owned resources, job progress, sports wins and house ownership added to DataStore v2 with v1 migration.
- PACK inventory and mobile timing HUD, SPORTS and HOMES destinations.
- Durable reusable open-world idea library at src/roblox/OPEN_WORLD_CREATOR_TOOLKIT.md and game-specific GAME_DESIGN_BIBLE.md.



- Seven additional portal-connected worlds: Castle Kingdom, Harvest Valley, Sakura Japan, Snowbound North, Ocean Marina, Wildlife Safari and International Airport.
- Roblox terrain grass, sand, snow and ocean water; castles, barns, crops, Japan-style pagoda and torii, runway and airplane, dock and boats, animal models, jetpack station and bank.
- Server-controlled portal/World-menu travel and cooldown-protected farming, feeding, fishing, luggage, lantern, castle relic and ATM activities, plus a repeatable cross-world courier job.
- Arcade snowmobile spawns, limited 3-second jetpack lift and flying car lift; full flight physics and mobile controls still require development.
- Read WORLD_EXPANSION.md for exactly what is interactive versus decorative, and for reuse in other maps.


- Procedural asset library with grass, trees, rocks, roads, parked cars, houses, fences, bushes, flowers, benches, crates, streetlights and a decorative pond.
- Free server-controlled hovercar spawner using VehicleSeat (seat usage tested; driving feel requires Android QA).
- Pulse Rifle with server raycast hit validation and an unlockable Scatter Blaster (175 earned coins). Both are in-game items, not Robux products.
- Read WORLD_KIT.md for reuse in other Roblox maps.


- New original world, four themed islands, central hub and bridges, signs, basic custom geometry and lighting.
- Server-owned shard pickups, per-player cooldowns, three-hit drones with movement and respawn, close-range blast attacks.
- Server-validated rift sealing, coin rewards, experience/leveling, repeatable missions, and eleven-zone travel.
- Mobile buttons for BLAST, DASH, SHIELD, WORLD and SHOP; mission tracker, event timer, notifications and leaderstats.
- Earned-coin upgrades: blaster damage levels, six-second shield ability, and cosmetic following Riftling pet.
- Versioned profile saving using Roblox DataStore in a published live experience only; Studio tests do not access or modify live player data.
- Server-side allowlists, cost checks and cooldowns for actions; no client-authoritative currency.

## Not done yet

- Not published and no live Roblox game link or public players.
- Live DataStore save/rejoin testing, cross-server concurrency/session locking and rollback recovery have not been verified. Do not advertise persistence as production-safe until these are complete.
- Full real-device Samsung QA, sound, custom meshes/animation, polished art, multiplayer economy balance, mobile performance/streaming, and user-retention analytics remain.
- No Robux sales, products, passes, payments, ads or marketing campaigns are enabled.
- No claim that this game will be viral or profitable.

## Roblox Studio build

From repository root:

    ~/SatisfyForge/tools/rojo/rojo build src/roblox/rift-raiders/default.project.json -o /tmp/rift-raiders.rbxlx

Open the generated place in Roblox Studio to inspect and play. The original game scripts are under src/roblox/rift-raiders/. A separate downloadable .rbxlx build is also committed in releases/rift-raiders/ for convenient import.

## Automated testing

- tests/roblox/rift_raiders_smoke.luau: Roblox Studio runtime world, scenery and systems smoke.
- tests/roblox/rift_raiders_multiplayer.luau: Roblox Studio two-player test for isolated teleport, invalid travel rejection, free-purchase rejection, shard cooldown, vehicles and raycast damage.
- python3 tools/roblox-studio/run_rift_multiplayer.py: automated multiplayer runner.
- Real-world playtesting and live saving remain separate gates.

## Sustainable monetization plan (not activated)

Follow Roblox's current Creator Hub monetization policies and user-friendly design. Launch as free-to-play and verify that players actually return before selling anything. Proposed optional, non-random cosmetics after testing: unique Riftling skins, emotes, avatar trails and themed nameplates via one-time passes; avoid pay-to-win advantages and misleading timers. Products and pass IDs must be created and validated for the new published game, with explicit owner approval and accurate price display. Do not use any Robux purchase prompts until the receipt/ownership and save/rejoin flows are proven.

Official references:
- https://create.roblox.com/docs/reference/engine
- https://create.roblox.com/docs/cloud-services/data-stores/best-practices
- https://create.roblox.com/docs/production/monetization
- https://create.roblox.com/docs/production/monetization/passes
- https://create.roblox.com/docs/production/analytics/monetization

## Creator research incorporated

- TheDevKing: gameplay scripts, remotes, tools and data saving.
- CovertCode: scripting workflow, HUDs and testing.
- RoBuilder: original modular map geometry and readable districts.
- DitchyDevelopments: replayability and truthful gameplay-focused short-form creator updates.
- Roblox Creator Hub: current authoritative Engine API, data stores, multiplayer and monetization.

Full coverage of every YouTube video was not possible; do not imply otherwise.

## Co-op Chaos Titan event

During each 25-second Rift Surge, a giant shared Chaos Titan appears at the hub with 26 HP. Players can attack it using the BLAST control; contributors receive earned coins, experience and shards if the team defeats it before the event ends. The Titan creates short-range shockwaves, so DASH and the unlockable SHIELD are useful defensive mechanics. The boss has a shared health attribute that appears in the event HUD. This is an original early-stage co-op boss prototype; it needs additional animation, telegraphs, balancing and physical mobile QA.
