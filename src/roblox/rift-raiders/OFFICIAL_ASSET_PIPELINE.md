# Rift Raiders v0.8 — Official Roblox Studio Art Pipeline

## Why the game looked like blocks

Versions 0.1–0.7 generated most buildings, vehicles, trees and NPCs out of primitive Parts. Gameplay could be tested, but the result could never match the visual quality of Roblox's actual Modern City template. We changed the art pipeline rather than simply adding more Parts.

## What is now genuinely imported

Source: **Roblox Studio's built-in Modern City template**, official template place 13165709401 (Roblox Templates creator account). Documentation: https://create.roblox.com/docs/resources/templates and https://devforum.roblox.com/t/new-studio-template-endorsed-packs/2333430

We opened Modern City in Studio and saved an original local XML copy at ~/Documents/ModernCity_Official.rbxlx. It is not overwritten or committed.

A repeatable script, tools/roblox-studio/extract_official_city.py, extracts a downtown region into assets/OfficialModernCityDistrict.rbxmx. The version in this repository includes:
- **13 original modular city buildings** with imported mesh geometry.
- **59 groups of original streets, trees, lighting, decals, sidewalks and street furniture**, spatially clipped from the official example.
- Approximately **1,880 detailed MeshParts** and original SurfaceAppearance maps, not procedural blocks.
- Eight official **MaterialVariant** assets, separately stored in assets/materials/.
- One original detailed **45-MeshPart sedan** from the same template, stored as assets/OfficialSedanVisual.rbxmx.

**Every imported Script, LocalScript and ModuleScript is removed.** We also remove internal mesh cache properties and union cache objects that an older Rojo version cannot safely round-trip. This preserves official public mesh and texture asset IDs without importing unknown executable behavior.

## How the new game uses the art

- The downtown district is loaded statically into Workspace by Rojo. ModernCityIntegration.lua translates the model by Vector3.new(-720,0,2150) to center it at approximately (0,0,2350), far from the original fantasy hub and Life City job block.
- **Opening the v0.8 .rbxlx file in Studio immediately shows the detailed downtown** instead of an empty sky: tools/roblox-studio/set_editor_camera.py adds an edit-mode camera focused on the official buildings. The extracted art pack includes a static asphalt base for this preview.
- **Players now spawn in the detailed downtown** instead of on the primitive neon hub. The arrival point is on a textured asphalt road-edge plaza at (0,1.5,2215), facing the original modular buildings. A ground foundation fills gaps left by extracting only a curated portion of the template. Players can travel back to all original regions with the **WORLD** menu.
- The WORLD menu has a new **MODERN DOWNTOWN** destination. Physical signs link downtown to Life City jobs and the fantasy hub.
- Citizens start **without fantasy weapons** in downtown; traveling to adventure worlds grants them, and returning to the life-simulation zones removes them from the hotbar.
- Normal player cars and fictional getaway cars use the official detailed sedan visual model. The original server-owned VehicleSeat and collision/control shell remain in place and invisible. Flying cars still use the original fantasy model.
- VehicleService.lua now permits cars in the modern downtown region.
- Workspace streaming is enabled with 64-stud minimum and 256-stud target radii to reduce loading/rendering outside the player's current region.
- The HUD defaults to **compact mode**, with optional DETAILS and ACTIONS toggles; fantasy surge indicators are hidden in the city. Menus use a centered constrained layout, and touch navigation stays reachable.

## Reuse for future games

The entire import is modular: .rbxmx art packs, a separate ModernCityIntegration.lua server module, eight .rbxmx MaterialVariants, and a script-free sedan visual. New Roblox games can use these assets without copying the Rift Raiders economy or quests. Re-extract from an official saved template if you want to select a different city block.

To refresh the downtown pack, run:

    python3 tools/roblox-studio/extract_official_city.py ~/Documents/ModernCity_Official.rbxlx src/roblox/rift-raiders/assets/OfficialModernCityDistrict.rbxmx

Then:

    ~/SatisfyForge/tools/rojo/rojo build src/roblox/rift-raiders/default.project.json -o releases/rift-raiders/RiftRaiders-ChaosIslands-v0.8.rbxlx
    python3 tools/roblox-studio/set_editor_camera.py releases/rift-raiders/RiftRaiders-ChaosIslands-v0.8.rbxlx

## Remaining realism work

This is a **genuine visual improvement**, but not a completed GTA/Sims-scale world:
- The imported downtown is primarily a visually detailed explorable area. **The 20 career stations and the existing interactive property plots are still in the adjacent original Life City zone**, reached via the WORLD menu or wayfinding portal.
- The official sedan model improves appearance; its movement still uses our arcade, server-driven VehicleSeat logic. It does **not** use the official Racing template's full chassis physics.
- Pedestrians in the original world are procedural placeholders. Detailed rigged avatars, actual locomotion animation, NPC pathfinding, city traffic AI, polished interiors and varied voice/audio remain to be developed.
- Imported mesh/texture IDs are Roblox-hosted assets; their availability depends on Roblox's platform asset permissions. Avoid assuming they will work outside Roblox.
- The 16-region experience still needs real Android playtesting, performance profiling, collision checks, streaming validation, lighting checks, and real-user usability testing.
- No Robux transactions or public publishing were activated.

**Source is stored in GitHub** for reproducibility. Don't replace the official detailed city with generated cubes again.

## v0.9 gameplay attachment
The imported district now also serves as the life-simulation map. `Life.AttachDowntown()` adds small storefront plaques and invisible proximity anchors after `ModernCityIntegration` moves the official model to its runtime position. The original city meshes remain untouched. All 20 careers and six shopping categories can be used in this district, and the original procedural Life City is preserved as a fallback/secondary area.
