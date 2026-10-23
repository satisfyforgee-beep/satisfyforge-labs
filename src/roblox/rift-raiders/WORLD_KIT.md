# Reusable Roblox World Kit — Version 0.2

The procedural library in WorldKit.lua builds actual editable Roblox Models and Parts, **not** pictures, stock imagery or third-party free-model downloads. Each generated model is tagged RiftWorldAsset and has an AssetType attribute, so it can be found, copied, adjusted and reused in another map.

## Prefabs available

| API | Contents | Current map usage |
| --- | --- | --- |
| WorldKit.Tree(parent, pos, variant, scale) | Trunk + oak/pine/crystal canopy | Crystal and Sky islands |
| WorldKit.Grass(parent, pos, color) | Three angled blades of grass | Natural island ground |
| WorldKit.Rock(parent, pos, color, scale) | 3D boulder cluster | Magma |
| WorldKit.Lamp(parent, pos, color) | Lit metal streetlight | Neon Metropolis |
| WorldKit.Crate(parent, pos, color) | Wooden/metal supply crate | Every island |
| WorldKit.Road(parent, pos, size) | Asphalt and painted lines | Neon Metropolis |
| WorldKit.Car(parent, cframe, color, drivable) | Car body, wheels, lights, VehicleSeat | Three parked cars; player vehicle |
| WorldKit.Bush(parent, pos, color) | Decorative 3D shrub | Every island |
| WorldKit.Flower(parent, pos, color) | Flower stem and bloom | Natural islands |
| WorldKit.Bench(parent, pos, color) | Park bench | Every island |
| WorldKit.Fence(parent, pos, length, color) | Fence posts and rails | Every island |
| WorldKit.House(parent, pos, color) | House with roof, windows, door | Neon Metropolis |
| WorldKit.Pond(parent, pos) | Decorative water-look pond (not swimmable) | Prism Wilds |
| WorldKit.Populate(parent, biomes) | Deterministic scene layout | All four islands |

The kit has no Roblox asset IDs, external dependencies or licensed character assets. To reuse in another Rojo game, copy WorldKit.lua into ServerScriptService, map it as a ModuleScript, and call its constructors from a server script. Placement positions are Roblox Vector3 coordinates; car orientation uses CFrame.

## Playable additions

- Press SPAWN CAR at the top right to create one free arcade hovercar near the player in a safe map area. Sit in the DriverSeat and use standard Roblox VehicleSeat driving controls. The server owns movement and limits travel to supported islands and bridges. A new spawn replaces your old car, and an 8-second spawn cooldown limits spam.
- Each player gets a Pulse Rifle tool. Equip it from the backpack or tap FIRE to shoot along the center of the camera. A visible neon tracer appears. Server checks range, weapon ownership, cooldown and raycast hit; enemies and the boss can take damage. Players cannot shoot other players in this prototype.
- Earn 175 in-game coins to unlock the Scatter Blaster. It fires four short-range pellets and is saved with the profile in live experiences. The game does not charge Robux for these weapons.
- Existing BLAST, DASH and SHIELD buttons still work.

## Limits and next improvements

- The vehicles use an intentionally simple anchored-model arcade controller rather than suspension, tire simulation or collision-resolved vehicle physics. **Physical driving on Android must be playtested before calling it production-ready.**
- Trees, grass, water, buildings and cars are stylized procedural Roblox parts. These are usable 3D objects, not realistic photogrammetry.
- No asset placement editor exists yet. Assets are reusable from Lua/Studio, not player-spawnable from an in-game editor.
- Before public release, profile persistence, UI overlap on narrow phones, vehicle handling, gun aim, performance and collision require manual QA.

Roblox documentation consulted:
- https://create.roblox.com/docs/reference/engine/classes/VehicleSeat
- https://create.roblox.com/docs/reference/engine/classes/Tool
- https://create.roblox.com/docs/workspace/raycasting
