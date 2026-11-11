# Rift Raiders v0.24 — Visible Workplace Characters and Carried Parcels

## What was implemented
- Added **six procedural, server-created workplace guide characters**: two named employees at the Corner Market, one dispatcher at Rift Express, and three named delivery receivers at the existing customer dropoff addresses. Each has a uniform, head, hair, hands, shoes, a name tag and a physically accessible **ASK FOR HELP** prompt.
- Retail and Courier help gives the player relevant next-step directions for their actual current shift; other visitors get an explanation of how to apply. Speaking does not award coins, reveal another player's private job assignment, or modify progress. Server code checks actual nearby character state.
- Correct Courier parcel pickup now spawns a **visible, labeled, non-colliding package welded to the player's hand**. The package is server-created, is not a paid asset, has an owner attribute and parcel type, and is not granted by client-side requests without the proper shift and pickup radius.
- A delivered package disappears upon verified handoff. If the package is lost or removed, delivery does not pay a tip; the courier can return to the original dispatch bin and recollect the same assigned package. On character respawn, a partially picked-up courier route resets to pickup; changing jobs clears carried packages.
- No paid purchases, public publishing, externally sourced NPC models, uncontrolled loop-based animation or DataStore schema migration. Original v0.23 retail and courier wage/tip accounting is preserved.

## Correct description and limitations
- These are **static stylized personnel**, not natural-language AI, full R15 animated customers, or a crowd scheduler; adding them makes venues recognizable and offers useful physical conversation, but does not prove a AAA-quality NPC system.
- The parcel is a visual prop attached to the character's hand and tracked by server shift state; this is not a rigid-body carrying simulator, an item inventory feature or a delivery-van mechanic.
- Validate on real lower-end Android/iOS for FPS, lighting legibility and controller collisions before public release. Avatar and asset permission provenance, multi-server live DataStore saves/rejoins, third-party moderation, live human testing and graphical quality evaluation remain outstanding.

## Automated test coverage
- Rojo compilation and Roblox Studio smoke test verify the NPC model count, talk prompts, script-free procedural bodies, server-chosen orders and all prior workplace systems.
- Multiplayer regression checks staff proximity and non-paying dialogue, the correct visible welded package, other-player isolation, deletion and recovery without free wages, valid delivery and one-time payout, and the legacy car/boat/cafe/retail/mechanic/security features. **Only mark multiplayer green after the actual final test run passes.**

## How to try
Open `RiftRaiders-ChaosIslands-v0.24.rbxlx` in Roblox Studio, press Play, apply for **Courier** at City Jobs, start a shift at the Downtown Courier worksite, ask the Rift Express dispatcher for directions, then collect the correct package. You should **see the labeled carton attached to your avatar's hand** until the package is successfully delivered. Return to the original courier worksite for normal wages.
