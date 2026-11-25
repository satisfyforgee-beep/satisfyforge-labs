# Rift Raiders v0.3 — Seven-world open-world expansion

This version extends the original four island districts with **seven separate destinations** connected to the central hub. These are working original Roblox Studio models, not screenshots or purchased maps.

## What the game actually contains

| Destination | Terrain / original prefabs | Working interaction |
| --- | --- | --- |
| Castle Kingdom | Grass hills, royal stone castle, four towers, walls and stained glass | Find a relic for earned coins and XP |
| Harvest Valley | Terrain grass, red barn, hay, 12 carrot/wheat crop plots, cow | Harvest each crop and feed the cow |
| Sakura Japan | Grass, torii gate, five-level pagoda, lamps, trees | Light a lantern |
| Snowbound North | Terrain snow, pine trees, rocks, four snowmobiles, jetpack station | Spawn an arcade snowmobile; activate 3-second server-powered jetpack lift |
| Ocean Marina | Terrain water, sandy island, dock, two motorboats | Fish from the pier |
| Wildlife Safari | Grass, trees, pond, six total animals across farm/safari | Feed a deer |
| International Airport | Ground terrain, terminal, runway, static passenger jet, luggage cart | Deliver luggage |
| Existing Neon Metropolis | City island, existing cars, new bank building and ATM | Collect bank payout |
| Central Hub | Seven physical portal gates | Enter any new world; each world has a return portal |

In addition, the **WORLD** menu now includes all eleven districts plus the hub. The travel destinations are hard-coded on the server and validated; clients cannot teleport to arbitrary positions. The existing islands, weapons, pets, quests, multiplayer and currency remain in place. A central **Courier Dispatch Terminal** assigns one of the seven new destinations; completing a delivery there grants 40 earned coins, 45 XP and 2 shards, with a 25-second job cooldown. The HUD displays the active delivery destination.

## Reusable world-building toolkit

The new `WorldExpansion.lua` module exports `Expansion.Prefabs`:
`Castle`, `Barn`, `Crop`, `Torii`, `Pagoda`, `Airport`, `Plane`, `Snowmobile`, `Boat`, `Bank`, `Animal`, `Jetpack`, `Portal`.

It also exports `Expansion.Worlds` with the seven destination names, IDs, positions, materials and colors. `WorldExpansion.Build(world, WorldKit, reward, tell, spawnVehicle)` generates terrain, portals, prefabs and interactions. The existing `WorldKit.lua` continues to provide trees, grass, rocks, lights, roads, cars, houses, flowers, bushes, crates, benches, fences and ponds. These modules can be copied into another original Roblox experience with the relevant game-service callbacks.

### Performance and asset quality

- Real Roblox `Terrain:FillBlock` / `Terrain:FillBall` land and `Enum.Material.Water` water are used for the seven new regions. Sculpt and paint the result further in Roblox Studio's Terrain Editor for organic realism.
- All prefabs are original, simple procedural Roblox Parts, with no third-party free models or remote code execution. The marketplace references are design inspiration, not purchased or copied files.
- A flying car is available through the `FLYING CAR` button. It lifts to a limited altitude while occupied; it is **not** a full flight simulator.
- Snowmobiles use the same simplified server-controlled VehicleSeat arcade movement as cars. Boats and airplanes are **static models**, not operable vehicles yet.
- Animals are **stationary models** with a feeding interaction; they do not yet have AI wandering, animations, or breeding.
- Jetpack activation at the arctic station uses server-created `VectorForce` for a limited three-second boost, with a cooldown; it is not unlimited controlled flight.
- A bank ATM is an in-game reward interaction. It has **no connection to real money, real banking, or Robux**.
- Large worlds need StreamingEnabled/LOD, occlusion, lower part counts, collision review, better meshes, terrain blending, NPC navigation, mobile controls, audio, animations and real-device QA before a public release.

## Next steps, prioritized by gameplay value

1. **One flagship city loop:** street-level missions, working doors/interiors, a garage, vehicles, shops, simple NPCs and a replayable delivery/chase loop.
2. **World activity depth:** farming growth timers and inventory, fishing minigame, safari wildlife AI, castle dungeon, Japanese collectibles, airport flight challenges, arctic snowmobile races.
3. **Actual vehicle physics:** collision-aware cars, boats that float and steer, aircraft with takeoff/landing, touch steering and safe speed limits.
4. **Art/optimization:** terrain sculpting, cliffs and coastlines, custom meshes, texture variety, mobile streaming, lighting, ambient audio and accessibility.
5. **Economy and launch:** safe persistence, quest progression, player feedback, retention analytics, balanced optional cosmetic monetization after testing.

We should use GTA's **open-world design principles** (exploration, travel, jobs, vehicles, activities and social play), not copy GTA's map, trademarks, characters or assets.

## Sources supplied by user

- https://create.roblox.com/docs/tutorials/curriculums/core/building/create-an-environment-with-terrain
- https://builtbybit.com/resources/roblox/maps/
- https://devforum.roblox.com/t/map-making-tips-tricks/590771

Roblox's Terrain Editor tutorial emphasizes terrain shapes, water, material painting and playtesting. BuiltByBit is a third-party commercial marketplace; do not assume its listed maps are free or safe to import. Never import an unreviewed model with scripts.
