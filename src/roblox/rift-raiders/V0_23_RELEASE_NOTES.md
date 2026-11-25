# Rift Raiders v0.23 — Physical Courier Dispatch and Three-Stop Delivery

## Implemented
- Added a walkable downtown **Rift Express** dispatch depot with three labeled pickup bins (Documents, Groceries, Electronics) and three separate customer drop-off addresses (Apartments, Offices, Waterfront).
- Downtown Courier shifts assign both a random parcel category and a random destination on the server. Players pick the exact package, carry the job state to the assigned location, deliver it, then return to the Courier workplace for their standard pay.
- A correct delivery grants one earned 10-coin tip and 4 XP; wrong parcel, wrong destination, distant requests, mismatched stations, out-of-sequence actions and repeated payouts are rejected by server code.
- Existing simpler courier work sites in other worlds and the separate interworld delivery feature remain functional.
- The new depot includes loading-platform geometry, shipping cartons, route-labeled doorsteps and proximity prompts. No imported or paid third-party assets or perpetual scene animation loops were added.
- The save schema remains v10. No Robux transactions, account changes or public experience publishing.

## Limits and further work
- Parcel carrying is tracked as an in-session job state; an actual held/package Tool model and animated handoff are future art/gameplay improvements.
- The delivery destinations are distinct play locations, but this is **not yet a physically drivable delivery van route** or NPC logistics simulation.
- Actual touch-controller readability, live-server profile rejoin, moderated asset provenance, real device FPS/memory profiling and human first-time playtest observation still block public release.

## Try it in Studio
Open `RiftRaiders-ChaosIslands-v0.23.rbxlx`, enter Modern Downtown, apply for **Courier / Delivery Driver**, and start a downtown Courier shift at the main workplace. Visit **Rift Express** nearby to collect the package indicated in your task HUD, follow the destination label to the correct physical customer doorstep, and return to the Courier workplace for wages.

## Testing
Rojo build and Studio runtime smoke check are required for this release. The multiplayer regression also covers the v0.22 retail shift, v0.21 mechanic job, old world systems, wrong-parcel/destination denial, proximity validation, payout replay protection and separate player state. Only report these as passed when the test prints the corresponding explicit markers.

Roblox Creator Hub explains why server logic must validate both RemoteEvents and proximity interactions:
https://create.roblox.com/docs/scripting/security/client-server-boundary
