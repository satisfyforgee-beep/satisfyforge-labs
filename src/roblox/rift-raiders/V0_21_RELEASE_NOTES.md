# Rift Raiders v0.21 — Hands-on Motor Repair and Distinct Garage Gameplay

## Actual implementation

- The downtown **Pit Stop Detailed Mechanic Bay** now has a server-built vehicle-service lift and a demonstration sports car comprising **29 original Roblox Studio Racing-template MeshParts**. Imported models are script-free and the service area has diagnostic tools, a steel workbench, three specialized service stations, tire props, a replacement battery, an exposed brake rotor, shop lighting and signage.
- Mechanic career shifts use an actual job sequence rather than the old two generic prompts. The server randomly assigns a **Brake**, **Battery** or **Tire** malfunction to the player's current shift. The player first approaches the diagnostic scanner (within 11 studs), and only then is the fault revealed in the Life HUD. They must find the correct specialist workbench and perform the repair (within 10 studs). Choosing the wrong repair gives feedback, but does not advance progress or pay coins.
- Completing the real repair gives a **single earned-coin 18-coin tip plus 6 XP**. Players then return to the original Mechanic workplace to collect their ordinary career wages and reputation gains. Attempts to repair without a legitimate Mechanic shift, skip diagnosis, use the wrong workbench, call events from too far away, or repeat a repair for duplicate rewards are rejected server-side.
- The prior v0.18 Barista gameplay, 60 careers, 173 purchasable items, garden farming, boats, owned cars and estates, personal home security, suburb exploration, premium visual packs and v0.20 detailed Modern City streetscape remain intact.
- Roblox Studio smoke tests check the genuine detailed racing-art demo, three accessible repair benches, randomized fault assignment, and all prior map / data-safety systems. Two-client multiplayer regression tests the correct/incorrect repair sequence, no unauthorized tip payments, and ordinary wage collection.

## Quality and boundaries

- The detailed garage car is a **static showroom vehicle** based on permitted official Roblox template mesh art. It is not a real mechanical simulation with removable vehicle parts, torque physics, damage models or motor/oil systems. The actual interaction is the grounded diagnosis + matching-bench service loop.
- This remains a **private development prototype**, not a completed GTA/Sims-quality game. Several higher-tier cars, boats and home furnishings still use original procedural geometry instead of high-end imported meshes; mobile FPS and account-specific Roblox hosted-asset permissions still need verifying.
- No Robux purchases, paid upgrades, real-world funds, or public game publishing have been enabled. Profile save schema stays **v10**, with no new saved fields required for the mechanic minigame.
- The next two major craft priorities are physical Retail and Courier mini-games, and broader professional mesh sourcing plus on-device performance benchmarking.

## How to try the new shift

Open `RiftRaiders-ChaosIslands-v0.21.rbxlx` in Roblox Studio, press Play, visit **WORLD → MODERN DOWNTOWN**, and choose **MECHANIC** at the city employment center. Start the shift at **Downtown Worksite MECHANIC** on Motor Row. Walk to **The Pit Stop** garage next to it, use the diagnostic scanner, follow the revealed fault to the matching repair bench, then return to the mechanic workplace for wages.
