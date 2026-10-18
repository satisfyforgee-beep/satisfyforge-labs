## v0.20 — Public roleplay video benchmarking and actual first-neighborhood polish
- Public Brookhaven/Berry Avenue/Bloxburg footage and Creator Hub onboarding/performance documentation informed stronger street-level visual cues and faster access to activities.
- Imported and placed 18 permitted, official high-detail Modern City StreetLights/Street_SetDressing model instances at street corners and around storefronts, rather than more cheap-looking block props.
- Added real physical road details, traffic signals, readable business signage, bike parking and a public transit station with three server-checked free destinations.
- Tagged optional details for low-graphics hiding, without adding any extra server animations or loops.
- Still open: fully modeled new cars and business interiors, physically driving passenger buses, native mobile frame-rate benchmarks, live save/rejoin, deeper collaborative roleplay/social systems.

## v0.19 — First 30 seconds should look like a real place
- Feedback video identified that the camera mainly saw blank asphalt and important buildings only entered the frame after moving. Player first spawn now faces existing imported storefronts.
- Live-rendered, script-free official Modern City trees, paving, planters, fountain spray, welcome sign, benches, and a one-press visitor center break up the bare road.
- Important note: Imported source material can still occasionally be rejected by Roblox. This changes presentation, not the license/permission limitations or actual-device/mobile FPS requirements.
- Highest next priority: a real human 10-minute first-play session and live-phone mobile detail benchmarking, then replace the remaining low-quality vehicle interiors with verified allowed high-quality models.

## v0.18 — A tactile barista shift and atomic DataStore leases
- Three espresso machines and a serve counter near the imported modern downtown barista site now carry physical, correct-order shift gameplay, rewards and anti-replay checks.
- DataPersistence handles atomic active-server session locks, serialized saves and bounded retries; Studio mock tests cover stale/mismatched/future-schema saves without touching production records.
- Still needed before public launch: real private-live account migration and save/rejoin, more tactile careers, human first-play study, mobile FPS profiling and permitted high-detail mesh replacements for remaining placeholders.

## v0.17 — Reward exploration of high-quality official scenery
- Eight collectible secrets now make players explore the actual imported Suburban buildings and streets, with once-per-day server-backed progress.
- Added a route completion reward and HUD goal progress to supplement the initial job/shopping tutorial; no additional menus are needed to interact with real objects.
- Continue prioritizing genuinely playable 3D interactions rather than another catalog increase. Art of pickups remains stylized; placement is grounded in imported neighborhood landmarks.
- Preserve migration path v1–v10; validate live save/rejoin only after a separate private test experience is available.

## v0.16 — First five minutes, repeatable daily goals and mobile-detail groundwork
- Tutorial objectives are real, server-verified game actions, with one-time bonuses and a visible UI chip.
- Four daily missions create meaningful short-term goals and are persisted safely, with UTC rollover and one-claim-per-goal.
- Official Suburban small decor now has reduced physics and shadow overhead; walkable geometry remains intact and instance streaming stays enabled.
- Consulted Roblox Creator Hub onboarding/retention/performance and Matter/Nevermore patterns. No private game source or unlicensed assets copied.
- Remaining must-pass launch gates: real iOS/Android FPS/load benchmark, production session-locked profile save tests and rejoin stress, account-specific asset permission review, positive player feedback/retention evidence, content and moderation review.

## v0.15 — Make official prefabs earn their place in the game
- Connected actual imported Suburban market, auto garage, gas-station and playground art to server-validated economic interactions rather than merely displaying scenery.
- Four Suburban career workstations with application, work-shift and two proximity/time-gated activities use the existing job system.
- Market/roadside snacks cost earned coins and refill Hunger. Retail shopping and garage selection work at the original detailed building sites.
- Tests prove real purchases and reject remote unauthorized interactions. Original source scripts remain excluded.
- Still open: premium art sourcing and permissions, connected interior doors/service counters, store NPC animations, live save/rejoin tests, device-specific performance and real car physics.

## v0.14 — Actual high-detail imported Roblox Studio templates
- Saved official Studio Racing and Suburban templates locally and wrote reproducible, script-removing art extraction tools.
- Added real 29-MeshPart racing buggy as an earnable, drivable racing car; expanded to 10 selectable road cars.
- Added new SUBURBIA destination with six detailed official suburban building/playground prefabs. Existing Modern City mesh-based downtown and the official two sedan meshes remain.
- Original modular SUV, pickup, crossover, coupe, supercar and hypercar shapes now look different instead of sharing the sedan body, though those are not high-end imported PBR assets.
- Walkable upstairs rooms, accessible stairwells and household upgrades based on owned inventory.
- Immediate visual priorities remain fully PBR individual car/boat meshes, animations, real interiors, working Suburbia shops, trustworthy physics and collision, actual iOS/Android QA, asset permission checks and live DataStore rejoin verification.
- v0.14 Studio smoke and two-client multiplayer checks passed. The 47MB studio place and thousands of extra suburban parts could cause mobile performance problems; no real-phone benchmarks yet.

## v0.13 — Homes that react to purchases and selectable detailed cars
- A genuine, new residential neighborhood offers 12 assigned owner-home plots and 12 real official mesh trees.
- Owner-only keypad / physical opening doors, custom furniture and usable home entertainment, cooking, laundry and bedroom basics tied to purchases.
- Selected car appearance now reuses both official red and white detailed sedan mesh templates, with 7 earned trim choices and actual server-driven speed differences.
- Profile v7 migration adds home security, current car selection and Fun.
- High priorities still open: replace stylized housing and boat placeholders with high-quality models; add authentic car bodies and chassis physics; make more purchased goods usable; build believable interactions/relationships; test actual phones and public save/rejoin stability.

## v0.12 — New careers, actually usable gardens and drivable watercraft
- Expanded to 60 careers and 173 in-game shop choices, including realistic-life-inspired wages and ownership.
- Raised beds, organic-looking crop stages, consumable seeds, equippable trowel and watering can, watering, harvest and market sales.
- Expanded marina water/dock and nine steerable owned boat classes with different size/speed.
- Server-validated ownership, planting, proximity, jobs, boats and costs. v6 profile migration retains previous progress.
- This moves more catalog items into actual play, but boats/vegetation still need PBR mesh art and high-quality humanoid use animations.
- Next realism priority is less catalog volume and more meaningful systems: in-building activities, proper 3D clothing changes, vehicle garage selections, better boat collision/buoyancy, and phone quality control.

## v0.11 — Social citizens
- Added verified classic hair accessories to all 8 generated R15 downtown citizens so they no longer share the same bald placeholder silhouette.
- Added named TALK interactions with contextual city dialogue.
- Conversations point players toward jobs, shopping, homes, creator gear, business ownership and law/consequence systems without giving unearned rewards.
- Added server-side conversation counting for testing/telemetry inside the prototype.
- Still missing: relationship memory, branching conversations, schedules, interior routines and reactions to nearby incidents.

## v0.10 — Living Downtown
- Replaced the empty-city feel with 8 actual R15 Humanoid citizens generated by Roblox and moved along downtown sidewalk routes.
- Added 4 moving traffic cars using the detailed official Modern City sedan visual instead of primitive traffic blocks.
- Two citizens cross the welcome block immediately; six circulate around the district perimeter.
- Server tracks downtown traffic distance and owns movement.
- This is still waypoint/MoveTo AI, not full crowd intelligence, navmesh traffic, conversations or advanced pedestrian reactions.
- Next: richer NPC appearance/clothing, crossing logic, pathfinding, reactions, storefront interiors and improved vehicle chassis physics.


## v0.9 — Make the detailed city actually work
- Modern Downtown is now the main life-simulation district instead of a decorative imported block.
- Six storefronts are attached to the detailed buildings: apparel, technology, home goods, vehicle/marine, real estate and business licensing.
- One downtown employment office validates applications for all 20 careers; each career has a real-world shift location and nearby task prompts distributed around the city block.
- 19 non-creator careers use two-step work tasks; Content Creator keeps the camera/phone recording loop.
- Added downtown court payments, food pantry/rest services and two additional law-enforcement patrols.
- Expanded the life catalog to 48 in-game items and nine business types.
- Split the LIFE UI into Careers and Shopping, with category filters.
- Server proximity, level, ownership, cooldown and currency validation remain authoritative.
- Next realism priorities: replace procedural people with rigged NPCs and animations, integrate richer interiors, add realistic traffic/pathfinding and improve vehicle handling.

# Visual realism, behavior and performance production roadmap

## Current (v0.8): official mesh-based city art, real code
- **Major visual upgrade:** imported Roblox's own Modern City template art as a separate downtown region, with 13 buildings, 59 street groups, about 1,880 MeshParts, and official MaterialVariants. The spawn is in the new district. The official 45-mesh sedan now visually replaces the player's blocky car.
- We can now access Studio's GUI using authorized Mac accessibility and Swift Quartz mouse events, and saved the official template to the user's Documents folder. The reusable extraction pipeline and provenance are documented in OFFICIAL_ASSET_PIPELINE.md.
- Streaming enabled, compact HUD, 16 destinations, textured asphalt street foundation and no fantasy weapon hotbar in realistic zones. The v0.8 release has an edit-mode camera pointing at the detailed city, so the first Studio screen is no longer empty sky. Existing jobs, resources, sports and original world preserved.
- **Not finished:** downtown storefronts still need real job hooks; realistic car physics, rigged NPCs, AI pathfinding, animations, sound, detailed interiors and Android performance testing remain.

## Previous v0.7 foundation
- Life City has 20 professions, each of 19 wage jobs with two required workplace tasks; camera-based creator career; 28 virtual products; business income; hunger, energy and hygiene; walkable furnished home ground floors; city pedestrians, moving cars, police patrol and pursuit.
- New original procedural architecture: painted storefront signs, awnings, window trim, roof cornices, display merchandise, sidewalks, crosswalks, trees, park benches, fountain, street lighting, job-specific work props, home gables, porches and gardens.
- **Still not photoreal**: visual geometry remains mostly basic Roblox Parts, cylinders, wedges and spheres; high-quality custom imported meshes, PBR texture maps, proper humanoid rigs and motion-captured animations are still needed.
- Real boats, real flight jobs, vehicle physics, advanced police pathfinding, live persistent property plots and player-to-player trade remain future milestones.

## Previous v0.5 foundation
- Dynamic day/night, cloud cover, CLEAR/CLOUDY/RAIN/MIST weather states, atmospheric haze, natural color grade, sun rays, global shadows.
- Client-selectable LOW/MED/HIGH graphics, rain streak visuals.
- 10 decorative route-following pedestrian NPCs with alternating walk and pause behavior; 2 moving traffic cars and a city ring road.
- Earnable prestige cosmetics and advanced vehicle licenses, visible house roof and garage upgrades.
- Important limitations: Roblox default blocky geometry, no PBR textures, no professional meshes or sound, no full NPC obstacle avoidance, no true wheel/suspension physics, no collision-aware traffic, no real phone GPU benchmark.

## Stage 1: original high-fidelity asset pipeline (free)
- Blender: create modular roads, buildings, vehicles, windows, trees, foliage, sports gear, house interiors and NPC props with optimized polygon counts.
- UV unwrap and create physically based materials: base color, normal, roughness and metalness; use Roblox SurfaceAppearance where supported.
- Use Roblox Terrain and MaterialService to blend roads, mud, gravel, snow, sand, grass, water and rock; add roadside signs, wear, curbs, crosswalks, trash cans, fences and realistic scale.
- Give each region a distinctive architecture, color temperature, fog range, ambient soundscape and landmarks.
- Source only original or clearly licensed audio/meshes; do not copy other Roblox games or use unreviewed Toolbox scripts.
- Use MeshPart LOD, occlusion, texture atlases, streaming and client graphics tiers to maintain mobile performance.

## Stage 2: believable behaviors and interaction
- Replace decorative NPC routes with PathfindingService-based pedestrian schedules: walk to job, shop, wait at crossing, avoid obstacles, react to rain, greet or talk to players.
- Add NPC road navigation, traffic lights, safe intersections, lane-following, braking, parking, collision and honking.
- Improve vehicles with realistic acceleration, braking, suspension, tires, steering, turn signals, dashboard, headlights, engine audio and camera.
- Add weather-reactive foliage, puddles, raindrops, wet road roughness, day/night lighting and interior lamps.
- Add believable animation for fishing, sports, crafting, working, carrying resources, sitting, doors and climbing.
- Add NPC police and non-graphic consequence system, avoid encouraging real-world crime.
- Sports: real physics ball, possession, goalie, field boundaries, scoring and multiplayer leagues.

## Stage 3: life simulation and progression
- Expand starter house into modular room/furniture placement, garage upgrades, saved permissions and customization.
- Jobs: reputation, skill leveling, career equipment, role outfits, player businesses and collectibles.
- Vehicles: entry-level free car, progressively unlocked snowmobiles/jetpacks/flying cars, earned customization and optional cosmetics.
- Introduce quest chains, discoverable areas, cooperative challenges, social goals, daily events and replayability.
- Every upgrade must visibly improve experience and have a meaningful free path.

## Quality gates
- Run Roblox Studio 2-player test and mobile-device tests after each feature.
- Benchmark low-end Android at target framerate; verify streaming, part count, dynamic lights, network events and loading times.
- Conduct blind first-time playtests for comprehension, excitement, controls and fairness.
- Test persistence and reconnection without live-data corruption; include save migration and concurrent-session protections.
- No public publishing, paid product activation, or existing-place modifications without authorization.
