# Rift Raiders v0.15 — Playable Official Suburban Buildings

This release converts the six safely imported prefabs from Roblox Studio's **official Suburban template** into a district that supports actual, server-validated gameplay. It preserves the Modern City, Racing vehicle, ownership systems, houses, gardening, boats and earlier destinations from v0.14.

## New things players can really do

- **Convenience Market:** the detailed Suburban market scene has a usable shopping kiosk. It accepts purchases from the existing HOME, GARDEN and TECH catalog categories, checking currency, level, existing ownership, and player-to-kiosk proximity on the server.
- **Market Snacks:** players can buy a 15-coin snack near the convenience market or roadside gas-station kiosk, recovering 35 hunger points with a 25-second cooldown. The server rejects remote purchases and purchases without enough earned coins.
- **Auto Garage and Gas Station:** both detailed structures now have actual points for buying vehicles and accessing a previously purchased car at the dealer. Existing vehicle ownership and garage security rules continue to apply. **Gas consumption and filling fuel tanks are not yet implemented.**
- **Suburban Playground:** a rest point is connected to the established public park service and increases player energy.
- **Four additional career workplaces:** retail associate, vehicle mechanic, delivery courier and security guard can be hired and work at physical markers located beside the appropriate detailed suburban buildings. Each offers two named task markers, using the same server-enforced order, work time and wage payout as the existing career system. These are **additional sites for existing careers**, not four new career types.
- WORLD → SUBURBIA and the six official detailed prefab buildings remain. The storefronts and job markers are subtle metal signs and prompt anchors integrated into the prefab neighborhood; the buildings' original look is not replaced with procedural cube buildings.

## Visual and asset quality

The Suburban assets are **real, reusable Roblox Studio template art**, not new images pretending to be 3D assets. They include complete buildings with thousands of detailed pieces; they're mostly Roblox part assemblies rather than photorealistic MeshParts. The Racing car remains a 29-MeshPart official template model, alongside two official detailed Modern City sedans. Additional owned vehicles have original, more differentiated geometric silhouettes, but they are not yet professional high-poly imported meshes.

The full build uses Workspace streaming, and players can manually change graphics detail using the in-game **GRAPHICS** button. There are remaining asset-availability warnings in Studio for Roblox-hosted IDs marked noncompliant by the platform; some minor materials may be missing. We will not substitute arbitrary third-party Toolbox scripts or distribute unlicensed meshes just to cover that up.

## Safety, development and remaining work

- **No Robux charges, purchases, or public publishing.** All new transactions use fictional coins and server-side validation.
- **Save schema stays v8**; this update introduces no saved-data migration.
- Roblox Studio smoke test checks official prefabs, four workplaces and validated service anchors. Two-client multiplayer regression adds tests for remote-purchase prevention and ownership-gated car selection and, when the account has sufficient earned coins, actual market item purchase.
- Real mobile performance, live Roblox DataStore save/rejoin, mesh permission/account ownership, accessible prefab shop interiors, advanced chassis physics, AI pedestrians and highly detailed unique boat/car/home assets still need verification or development.

### What to do in Studio

1. Open `RiftRaiders-ChaosIslands-v0.15.rbxlx` in Roblox Studio; click **Play**.
2. Use **WORLD → SUBURBIA** to travel to the imported district.
3. Approach the **Convenience Market** sign. Open **LIFE → SHOPPING** to buy home, garden or tech goods.
4. Use **BUY SNACK** at the shop or gas-station kiosk to recover hunger.
5. At the auto garage, use **LIFE → GARAGE** to select cars you already purchased.
6. Apply for RETAIL, MECHANIC, COURIER or SECURITY GUARD at the corresponding suburban workplace; start the shift and complete both tasks nearby to earn wages.

The next priority is a curated library of truly suitable mesh assets, checking licensing, render quality, originality and Roblox import/permission restrictions; then replace the biggest remaining geometric vehicles and residential interiors and benchmark actual mobile framerate.
