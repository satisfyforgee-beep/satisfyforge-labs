# Rift Raiders v0.20 — Streetscape, Readable City & Three Free Transit Routes

This development release is based on a public-reference comparison of roleplay experiences and publicly documented Roblox best practices, **not** on copying another game's private models, mechanics scripts, names, or artwork.

## Public reference review
- **Brookhaven 🏡 RP (official Roblox description):** https://www.roblox.com/games/4924922222/Brookhaven-RP — immediate social roleplay, recognizable homes, vehicles, city and events. Our lesson: give easy choices, visually understandable locations, and free transportation from the opening minutes.
- **Berry Avenue RP (public gameplay video and Roblox listing):** https://www.youtube.com/watch?v=wL31YZjFP18 and https://www.roblox.com/games/9059288453/Berry-Avenue-RP — social town roleplay organized around visually distinct vehicles, houses, stores, hospital and roleplay items. Our lesson: labels/wayfinding should point at real opportunities, not hundreds of abstract menu entries.
- **Bloxburg street-detailing (public YouTube video, PeetahBread, March 2025):** https://www.youtube.com/watch?v=yxTUP2c_zZI — adds streetlamps, traffic lights, road markings, and signs to an otherwise bare-looking city. Our lesson: a small number of legible street details makes a large empty paved area look inhabited.
- **Roblox Creator Hub Onboarding:** https://create.roblox.com/docs/production/game-design/onboarding — get users into the core gameplay quickly and show clear next actions.
- **Roblox Creator Hub Performance:** https://create.roblox.com/docs/production/analytics/performance — profile performance and audit expensive initial asset loads, especially on mobile.

These are references for broad mechanics and quality goals. No one else's private game code or unlicensed content was obtained or reused.

## Changes actually included

**Visuals / street-level quality**
- Built a new server-owned **Detailed Downtown Streetscape** scene around the Modern City starting district, with source art from the official built-in Roblox Studio Modern City template. The imported material is sanitized and contains no executable scripts.
- Added **18 reused official street-prop models** from the included Modern City pack: real existing MeshPart streetlamps, rhododendron plants, mailboxes, waste bins, newspaper display and hanging planters. These supplement the first-minute plaza trees, benches and fountain from v0.19.
- Added detailed intersections with crossing stripes, pedestrian signal casings, illuminated green/red crossing indicators, bike-parking spaces, nearby venue signage and eight low-cost warm shop sconces.
- Wayfinding signs in front of the community-life employment area, Bean & Brew cafe, Motor Row and the Downtown Nursery make destinations visually identifiable instead of forcing unfamiliar visitors to read the entire LIFE catalog.

**Accessible activities / transport**
- Added a walkable, street-level **RiftLife Transit** shelter with a tinted-glass roof, station bench, timetable board, and three actual public bus stop prompts.
- Players can ride for free from the downtown stop to **City Jobs**, **Community Garden**, or **Residential Estates**. The server checks that they are near the physical button and alive, and transports only that player. A fake route or a remote request is rejected.
- This is a **fast-travel bus shelter**, not a physically animated bus route; realism still needs a modeled driving route, scheduling, and passenger boarding.

**Mobile and HUD**
- Tagged purely decorative street details with \`RROptionalStreetscape\`. The existing **GRAPHICS: LOW** setting hides these optional parts locally while preserving public routes, server prompts, and important signs. MED/HIGH display them.
- Moved the graphics quality button into the expanded ACTIONS panel by default, reducing always-visible HUD clutter. No new server per-frame animation loop was introduced for the decorative scene.
- This is a rendering-detail toggle, **not** proof of actual mobile FPS or memory optimization.

## Safety and testing
- No Robux charges, no paid or unlicensed assets, no account access changes, no public publishing, and no changes to persistent save schema (v10 remains).
- Rojo build and Roblox Studio automated smoke checks verify official prop count, safe imported assets, physical transit buttons, no extra continuous animation loop, optional graphics tags, and important venue signs.
- The multiplayer regression checks actual free ride from transit button, denies remote/fake routes and protects other players against being teleported, in addition to all previous garden/home/car/cafe/shopping checks.
- The game remains a **private prototype**. First 10-minute user testing, Android and iPhone FPS benchmarks, live DataStore leave/rejoin tests, environmental asset permission checks and real high-end car/boat/interior mesh replacement still need work.

## Next priority after this release
Make additional venues tactile with physical job minigames (mechanic, retail), progress towards truly high-quality permitted vehicle/interior assets, and test live private save/rejoin plus mid-range Android performance. The wider GTA/Sims-size world is **not yet complete**.
