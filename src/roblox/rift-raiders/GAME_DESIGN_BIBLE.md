# Rift Raiders v0.5 — Sports, Jobs, Resources, Crime & Consequence

## Actual playable implementation

New World Sports Complex at (0, 0, 900) has a soccer pitch with goal posts, a football field with yard lines and uprights, a baseball diamond with bases, bleachers, floodlights and an arrival plaza. The WORLD menu includes SPORTS and HOMES as the 13th and 14th destinations.

Players interact with football, soccer and baseball stations. A visible timing meter appears; pressing when its marker reaches the green zone is validated on the server, awarding coins, XP and sports wins. Successful shots create temporary visible balls with animation. These are **timing minigames**, not yet full 11-on-11 soccer or physics-based team sports.

Fishing at the marina is now a timing minigame, awarding fish inventory and coins. Fish can be sold at the fish market. Safari has a non-graphic wildlife-tracking/hunting minigame awarding crafting hides; animals are not graphically harmed.

Housing Meadows adds twelve allocated player plots. At level 2, players can spend 8 wood and 6 metal to build an original furnished house on their allocated plot. House ownership is saved in profile v2 and the model reconstructs on reconnect; occupied plots are reserved per server session, with a capacity of 12. Interior editing, persistent furniture placement, plot upgrades and visitor permissions are not yet implemented.

Wood at the farm and metal at several city scrap stations are gatherable with server-enforced cooldowns. A hub workbench crafts a toolkit for 2 wood + 3 metal. Resources and toolkit counts display on the HUD and PACK screen.

Fictional NPC vehicle missions unlock at level 2 and consume a toolkit. A mission getaway car is spawned by the vehicle service; the player must bring it to the chop shop for a reward. A fictional bank-vault mission unlocks at level 3, consumes a toolkit, awards earned coins/XP/shards, and adds wanted heat. Both have real-time server-side cooldowns that persist in player profile data. Heat cools down over time. No real-world money or banking is involved.

Original reusable service: WorldActivities.lua. Profile DataStore migrated from v1 to v2, retaining existing coins, upgrades, pets and rift progress while adding resources and job history. DataStore is intentionally disabled in Studio; full live-store migration still needs controlled production testing.

## Testing and limitations

- Rojo build creates a local Roblox Studio place file.
- Roblox Studio smoke checks map content, world landmarks, terrain, activity stations and remotes.
- Two-player Studio test checks existing game actions and travel, snowmobile and flying car, resource isolation, toolkit crafting, invalid free purchases, sports timing isolation, and fishing/market rewards.
- Sports are timing challenges; fish/hunting are minigames, not detailed simulation.
- Criminal missions are fictional, non-graphic and require progress. No police NPC pursuit or PvP is implemented yet.
- Visuals are original modular/low-poly assets, not photorealistic; no user-facing claims of GTA-level production quality.
- Boats and airplanes remain static models; house construction is implemented, but interior editing, plot expansion and shared permissions are not.
- Monetization is **not enabled**; no Robux IDs, paid passes, purchases, subscriptions, cash-outs or live revenue.
- Not published to a live Roblox experience. Existing Roblox places untouched.
- No real Samsung device test, large-server load test or completed content maturity questionnaire yet.

## Next vertical slice
1. Housing: expand the basic owned-house system with modular wall/furniture editing, plot upgrades and friends access.
2. Real NPC simulation: cars and pedestrians with navigation, police patrols and non-graphic arrest.
3. Real physics sports and co-op: ball trajectory, goalkeeper, baseball pitch/bat, team scoring.
4. Fishing and wildlife depth: bait, rods, species, water weather, animal movement, non-graphic tracking.
5. More believable streets and interiors, lighting, audio, weather and streaming performance.
6. Once players love the free game: ethical cosmetic monetization, creator analytics, private beta and launch.


## v0.5 realistic presentation and prestige economy

- WorldPolish.lua adds global time-of-day, natural color grading, clouds, sun rays, four cycling weather conditions, animated decorative pedestrians, and NPC route-following traffic in a small city road loop.
- Mobile graphics control offers LOW / MED / HIGH client visual settings and local rain streaks. This is a graphics baseline, not photorealism.
- PrestigeCatalog.lua defines eight permanent coin-earned items with level gates: Midnight City Car Wrap (level 3, 450 coins), Modern Estate Roof (level 5, 1200), Platinum Hypercar Finish (level 10, 3800), Luxury Home Garage (level 12, 6000 coins plus 10 wood and 8 metal), and Aurora Legend Trail (level 18, 9000), Snowmobile License (level 5, 1400), Jetpack License (level 7, 2200), and Flying Car License (level 12, 6500).
- Personal car wraps affect spawned car paint. Estate roof adds new exterior lighting. Garage adds a physical structure and driveway to owned houses. Aurora Trail attaches to the player's character.
- Player profile migrates from v1/v2 to v3 without changing the existing DataStore key, preserving existing progress. Owned prestige IDs are validated against an allowlist.
- No real Robux purchases, pass IDs or products have been created. Prestige items are earned only until verified purchase integration is authorized.
- Animated ambient pedestrians and traffic are decorative finite-state behavior, not advanced obstacle-aware pathfinding or police AI.
- Realistic shadows, custom meshes, sound assets, facial animation, vehicle suspension, NPC traffic collision and device performance profiling are still backlog.


- Advanced snowmobiles, jetpack launches and flying cars now require server-validated earned licenses. Basic personal cars remain free for immediate fun. All licenses can be bought with earned in-game coins; no Robux is necessary.


## v0.6 Life City
- A playable life-simulation district connects careers, earned wages, shops, content creation, property and business ownership, and police consequences.
- See LIFE_SIMULATION_DESIGN.md for exact implementation, test coverage and limitations.
- This is an early vertical slice, not photorealism or a complete real-world simulation.


## v0.7 Career and environment expansion
- 20 careers with 19 two-task wage job loops and an equipment-gated content creator role.
- 28 virtual goods, gradual hunger/energy/hygiene, community meals and rest, furnished ground-floor homes.
- More detailed procedural storefronts, work props, landscaping, citizens and traffic.
- No real-world transactions; visuals are an upgraded original blockout, not photorealistic.


## v0.8 — First real asset-based city
- Use the **official Roblox Modern City template's detailed mesh buildings and materials** as a reusable environment kit, not handmade placeholder blocks. The extraction process is documented in OFFICIAL_ASSET_PIPELINE.md.
- Spawn in modern downtown, then explore the old Life City job stations and the 14 other regions by menu/portals.
- Realistic-looking official sedan shell replaces the player car's visible cube geometry, while retaining server-controlled arcade driving.
- Compact HUD, 16 destinations, Workspace streaming enabled for mobile.
- Imported asset scripts removed; monetization remains inactive.

## v0.9 — Detailed downtown gameplay
The official Modern City art is no longer presentation-only. The district now contains server-validated employment, shopping, 20 careers, two-step job activities, creator work, business income collection, civic services and police presence. Storefront interaction anchors are kept small or invisible so the imported architecture remains the visual layer instead of being covered by new block-built venues. The catalog expanded to 48 earnable purchases across apparel, tech, home, vehicles, property and business ownership.

## v0.10 — Living population and traffic
Modern Downtown now contains eight actual R15 Humanoid citizens walking repeated sidewalk routes and four detailed official-sedan traffic vehicles circulating around the city. The population layer is a separate reusable `DowntownPopulation.lua` module so future city maps can replace or expand it without touching the economy, careers or imported art. Movement is server-authoritative.

## v0.11 — Social citizen layer
The R15 downtown population now has named proximity conversations and verified classic hair accessories. Dialogue remains deterministic and server-owned so it cannot be used to grant client-requested rewards. This is the beginning of a reusable social-NPC layer; later releases can add memory, schedules and relationship state without replacing the underlying R15 population service.


## v0.12 — Gardening, marina, broader careers
- 60 careers (40 new) and 173 earnable item choices (125 new), organized by real-world shopping category.
- Gardening is a real farm-to-market loop: unique player plot, three usable seeds per purchased pack, trowel, watering can, time-gated organic crop growth, harvest inventory, profit through market sales and optional fertilizer.
- Marine ownership can now translate into a 9-class arcade watercraft, controlled by VehicleSeat with server checks and safe-water limits.
- Garden produce and seed stock are saved in migrated v6 profiles. The v0.11 named, talkable R15 downtown citizen functionality is retained.
- Next milestone should concentrate on realistic assets, environmental interactivity and real-device performance rather than another pile of catalog-only items.


## v0.13 — Residential Estates and purchase-reactive environments
- Purchased homes now generate player-owned, lockable houses in the 12-lot Residential Estates district. Buying compatible furnishings physically adds interiors/interactive appliances.
- Home owners control visitor access with smart locks. Ownership is verified on the server.
- A Fun lifestyle need is tracked. Entertainment/books/computers restore fun, fridge food restores hunger and a laundry appliance improves hygiene (all cooldown-gated).
- Selectable, previously purchased sedan trims now change official imported red/white 3D body and driving top speed, with a server-verified garage selector.
- No Robux purchase products or public release; the game remains in iterative development.


## v0.14 — Imported Racing and Suburban visual libraries
- Ten purchase-gated road cars now include a source-sanitized official Racing 29-MeshPart drivable race car; existing two imported official Modern City sedans remain, while SUV/pickup/hypercar/crossover etc get separate modular silhouettes.
- Six built-in Suburban template environment prefabs are now visible and explorable in a 19th region; all source scripts removed. The original local templates are not committed; reusable, reduced art packs and extraction tools are.
- The user's own homes can have accessible second/third floors, rooms, physical stairs and purchase-dependent electronics, pet gear, pool, hot tub and outdoor furnishings.
- None of this is real-world commerce; purchases use earned game coins. Suburbia's imported shops are decorative, not yet tied to the shopping economy. Mobile optimization and public Roblox save tests are next.


## v0.15 — Import professional scenery, then connect gameplay
- Real imported buildings act as in-world businesses, not merely visual exhibits. The official Suburban Convenience Market is a grocery/garden/technology store; gasoline station and auto garage provide further vehicle access; park rest and market snacks affect simulated life needs.
- Retail, mechanic, courier and security have four additional suburban work sites with real server-authoritative tasks and earned-coin wages. They are alternative worksites, not new catalog career entries.
- Interaction points are registered on the server, keeping location, ownership, currency, level, and work-step validation in one shared simulation service; no untrusted imported scripts are ever executed.
- Professional-looking environment geometry + deeper activity remains more valuable than inflating catalog counts.

## v0.16 — Keep players interested in their first five minutes
- Beginners have a compact first-session checklist tied to gameplay that already exists; players are not forced to read a wall of text before playing.
- Explore → buy → apply → work provides a clear initial progression through the premium official Suburban map; returning dailies incentivize normal gardening, work, eating and travel without real-money prompts.
- Goal completion is server-authoritative, awarded only after accepted actual actions with state persisted to v9. There's no client-callable free-coins endpoint.
- UX success measures for future live telemetry: new player 1-minute/5-minute activation, first purchase/first shift conversion, time-to-first-enjoyable interaction, repeat-session progression, test device FPS and crash counts. No user tracking or analytics integrations have been installed yet.

## v0.17 — Suburban discovery collection
- The open-world roleplay city now has a short repeatable scavenger loop anchored to eight physical spots, with readable prompts and virtual earned-coin rewards.
- Discovery progress persists per player, resets at UTC date rollover and rejects double claims/long-distance activation without requiring private-game API access.
- Future extensions: NPCs can tell natural hints; use professionally modeled prop assets if properly licensed and performant; add sound/spatial atmosphere; rotate discoveries for retention.
