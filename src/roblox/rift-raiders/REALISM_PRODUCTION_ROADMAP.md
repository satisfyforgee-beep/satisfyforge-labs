# Visual realism, behavior and performance production roadmap

## Current (v0.7): real code, not concept art
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
