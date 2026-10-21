# Rift Raiders v0.13 — Personal Homes, Furnishings and Detailed Garage

This is the next **tested development milestone**, not a claim that the entire game is complete or photo-realistic.

## Improvements actually implemented

### Residential estate neighborhood

- A new **ESTATES** travel destination and landscaped **12-lot residential district** with streets, lawn plots, signs and 12 cloned, detailed mesh trees from Roblox's official Modern City template.
- Existing purchased apartment/townhouse/mansion ownership still works. Newer residential purchases also generate physical, owner-labeled houses: starter home, condo, lake cabin, farmhouse, beach house, penthouse, villa, private-island estate, and others. **These are upgrade classes of the same house-building system, not unique exterior architecture or literal islands.**
- Homeowners can use **LIFE → MY HOME → VISIT MY HOME** to travel to their own lot. Players without a purchased home do not receive a free residence.
- Owners have a lockable, animated front door and a separate security keypad. Owners can lock/unlock guests; visitors cannot open locked doors. A visible door handle rotates with the door. The home-lock state is saved.
- Additional warm interior lighting and physically instantiated furniture that reflects specific shopping purchases, including couches, TV/console, refrigerator, dining table/chairs, bookshelf, laundry machine, upgraded mattress, baby crib, pet bed and work desk. No purchase means no corresponding premium furnishing.
- Purchased televisions/console, books, fridge, washing machine and desk have interactive owner-only prompts that restore **Fun, Hunger or Hygiene** with cooldowns. The previously functional private sink and bed continue to work.
- **Fun** is now a fourth lifestyle need, updated and saved along with Hunger/Energy/Hygiene.

### Detailed car garage

- Added the official **red 45-mesh sedan** from Roblox Studio's own Modern City template, separately imported without executable scripts. The existing official white sedan is preserved.
- **LIFE → GARAGE** offers seven selectable, previously purchased sedan-based trims: basic family sedan, sports, luxury, electric, high-performance/supercar, hyper-performance, and classic.
- Garage selection requires actually owned inventory and proximity to the vehicle dealer, verified server-side. The selected car persists.
- The normal **CAR** button spawns the selected red or white detailed sedan with a real different arcade top-speed setting (35–63 units/sec). The game reports the selected vehicle, paint variant and speed tier on the spawned model.
- **Important:** These seven variants still share the same official detailed sedan silhouette. They have different appearance colors and driving parameters, but aren't true SUV, pickup, hypercar, or bespoke sports-car meshes. Those models are still on the roadmap.
- Personal cars now verify the actual driver is the owner. Another player sitting in a privately owned car cannot control its movement.
- Removed one blocked, noncompliant texture-pack reference from an imported official car-paint material. Other original official city art assets are preserved.

### Progress protection

- Profile save schema **v7** migrates existing v1–v6 data, preserving owned items, income, jobs, homes, gardens, followers and experience.
- New saved fields: selected garage car, lockable-home setting and Fun need.
- No Roblox publishing, Robux monetization, purchases or off-platform accounts were changed.

## How to try it

1. Open the **v0.13 .rbxlx** file in Roblox Studio and press **Play**.
2. Earn coins via careers, shops, resources and existing missions.
3. At **LIFE → SHOPPING**, buy a residential property and some compatible furnishing. Open **LIFE → MY HOME** to go directly to your lot, use the door and keypad, and interact with the appliances.
4. At **MOTOR ROW / Vehicle Dealer**, buy a supported car, open **LIFE → GARAGE**, select the one you own, then use **CAR** to spawn and drive it.
5. **WORLD → ESTATES** lets everyone visit the residential neighborhood; owning a property is required to access its private owner features. **WORLD → WATERFRONT** continues supporting the owned boat classes added in v0.12.

## Verification and remaining scope

The source project builds with Rojo and runs in Roblox Studio. Release smoke and two-player multiplayer tests check real environmental models, furniture/door construction, both imported sedans, garage authorization, vehicle speed and protection against other players taking control, plus the prior careers, garden purchases and vessel handling.

**Not finished:** 12 simultaneous personally assigned lots do not yet scale to large servers; housing addresses/lot numbers can change across sessions; upper floors still need physical stairs or usable room teleport transitions; many household goods and premium vehicles are still inventory/catalog entries rather than usable unique objects; interiors use original stylized geometry rather than high-detail imported meshes; advanced cars require real chassis/suspension; boat behavior is arcade rather than physical buoyancy; NPC relationships, pathfinding, mobile-performance profiling, actual live Roblox DataStore reconnect testing, and large-scale multiplayer economy remain future work.

No one can accurately promise a complete GTA/Sims-scale photorealistic simulation from this milestone. The highest-value next releases should continue replacing placeholder interiors with properly licensed high-resolution meshes and deepen playable systems rather than just expand item counts.
