# Rift Raiders v0.12 — Careers, Gardens, Shopping and Marina

## Actual implementation

This version preserves the earlier **v0.11 Social Citizens** work (8 named R15 citizens, hair accessories, contextual conversations) and extends v0.10 with:

- **60 career choices**: 40 added real-world-inspired jobs on top of the existing 20. Each new non-creator role has a physical workplace and two named, proximity-checked work tasks. Examples include gardener, landscaper, arborist, tree grower, boat captain, yacht crew, marine mechanic, truck driver, software engineer, journalist, baker, pharmacist, dentist, architect, judge and accountant. All still require qualifying levels and completed work for in-game wages.
- **173 in-game shop products**: 125 newly added items on top of 48 earlier items, with prices and progression gates. Categories include technology, apparel, home goods, gardening, vehicles, properties and businesses. The UI supports filtering by category.
- **14 plantable crop varieties**: tomato, carrot, strawberry, potato, lettuce, pepper, cucumber, corn, pumpkin, sunflower, blueberry, rose, apple and watermelon.
- **16 individual raised beds** in Modern Downtown. The server assigns one plot per player (up to 16 simultaneous occupied plots). Planting requires a purchased trowel and seed stock. Each purchased seed packet supplies **three plantings**, which are consumed when sowing. A watering can is required to water crops. Crops mature over 38–105 seconds of actual clock time; players harvest produce into a persistent inventory and sell it for earned in-game coins at an outdoor farm market. Fertilizer increases the yield by one per harvest. Garden status, seed quantities, planted timestamps, harvest counts and inventory are saved.
- **Visible harvest growth**: plants emerge, increase size, develop leaves and show recognizable fruit and vegetables when grown. These are original stylized procedural objects, not photorealistic botanical meshes.
- **Equippable trowel and watering can** for players who own them, plus a garden market with canopy and produce displays.
- **9 navigable watercraft types**: kayak, fishing boat, jet ski, pontoon, sailboat, speedboat, cabin cruiser, yacht and luxury superyacht. Players buy them at the vehicle dealer and launch owned vessels at the **WATERFRONT** destination, using a VehicleSeat for throttle and steering. Different types have different sizes and speed limits; unauthorized spawns are denied. The expanded Ocean Marina has a launch dock and open water.
- **13 added businesses** (22 total) and **10 added property purchase choices**, alongside premium cars and more everyday household goods.

## Gameplay instructions

1. Start in Modern Downtown. Work shifts to earn coins, or visit the **LIFE → CAREERS** tab to apply at the employment office.
2. Visit the **Garden Nursery** near downtown's community beds. Open **LIFE → SHOPPING → GARDEN** to buy a trowel, watering can and seeds.
3. Walk to the community garden at the edge of downtown. Find your numbered bed under **LIFE → GARDEN**. Select a crop, plant it, water it, wait for it to ripen, harvest, then sell at the nearby produce market.
4. Earn more coins to buy a watercraft. Choose **WORLD → WATERFRONT**, then **LIFE → MARINA** to launch your own vessel at the Ocean Marina. Sit in the driver's seat to steer.

## Validation & constraints

- Roblox Studio smoke checks cover 60 careers, 173 catalog entries, 14 crop types, plot models, permit gates and 9 boat models.
- Multiplayer tests cover 2 players and verify career wages, city navigation, other-player garden separation, rejecting unpurchased seeds, denial of unauthorized vessel launches, and the actual speedboat seat movement.
- The in-game currency is fictional, not real money. All paid Robux products remain **disabled**; the game has not been publicly published.
- **Visual scope is still prototype quality**. The Modern Downtown environment and sedan are sourced from the official Roblox Studio Modern City template. Garden crops and boats use original procedural geometric models, not photorealistic imported models. Many new shop purchases are ownership/catalog entries rather than yet-functional gadgets, clothing changes or vehicle models; larger car/yacht interior systems still need work.
- New career tasks are two-step gameplay loops, not full professional simulations. Boats have anchored, server-steered arcade motion with steering/seating and speed classes, not physical buoyancy, wake simulation or collision-aware marine navigation.
- Player gardens are available for the first 16 simultaneous users. More players need additional beds/instancing. Crops grow between sessions using clamped wall-clock timestamps, but live DataStore and production rejoin/save reliability remain unverified.
- Proper phone QA, performance profiling, adaptive navigation, in-world shop presentation, real vehicle suspensions, fully animated NPCs, accessible housing interiors and expanded player-to-player economy remain future milestones.
- **Profile schema v6** migrates v1–v5 without resetting earned progression, preserving prior owned products and adding garden state.
- All imported third-party scripts remain excluded; work is on private GitHub branch feature/rift-raiders only.

**Future highest-value improvements:** polish gardener interactions with real hand animations, integrate rigged shopping/working NPCs and detailed vehicle/housing meshes, improve the detailed city's pedestrian pathfinding, and create truly interactive homes/garages. Avoid adding hundreds more catalog-only items before making the current ones useful.
