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
