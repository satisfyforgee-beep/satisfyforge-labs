# RIFT RAIDERS: CHAOS ISLANDS

An original multiplayer Roblox game, created separately from all existing SatisfyForge games.

## Playable loop (v0.5 prototype)

Spawn at the central hub. Use the WORLD menu or one of four skybridges to reach Neon Metropolis, Prism Wilds, Magma Outpost, or Cloud Kingdom. Collect 36 scattered shards, BLAST 12 roaming drones, spend 12 shards to seal one of four rifts, level up, earn coins, and unlock upgrades. Complete repeatable missions for bonus coins. During a periodic 25-second Rift Surge, eligible coin rewards double. Cloud Kingdom includes a five-platform summit challenge. Version 0.2 added reusable scenery, arcade hovercars and two aimable sci-fi guns. Version 0.3 expanded the map with seven terrain worlds, reusable prefabs, portals, snowmobiles, jetpacks and flying cars. Version 0.4 adds a sports complex, housing neighborhood, resource gathering, crafting, fishing and wildlife minigames, fictional heists and vehicle jobs, plus player-profile schema v2.

## Implemented

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
