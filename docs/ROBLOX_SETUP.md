# SatisfyForge Brainrot Rush — Roblox Studio setup

This is an original playable prototype, not a published Roblox experience yet.

## Install v0.3
1. Open Roblox Studio on Windows or macOS and create or open the SatisfyForge experience.
2. In **ServerScriptService**, add a Script and paste `src/roblox/BrainrotRush.server.lua`.
3. In **StarterPlayer > StarterPlayerScripts**, add a LocalScript and paste `src/roblox/BrainrotRush.client.lua`.
4. Press **Play**. The server script builds the arena automatically.

## Current gameplay
- Collect glowing Brainrot orbs.
- Common / Rare / Epic / Legendary rarity tiers.
- Green upgrade pad increases earnings up to level 20.
- Purple rebirth pad unlocks at level 20 + 2500 Brainrot and gives a permanent +50% earnings bonus per rebirth.
- Fast collection builds a combo up to x5.
- A Snackquake event starts every 90 seconds for 20 seconds with 2x rewards and faster spawns.
- Mobile-friendly HUD shows Brainrot, level, collected count, rebirths and combo.
- Player progress uses DataStore persistence and autosaves every 60 seconds.

## Required Studio checks before public launch
1. Enable **Game Settings > Security > Enable Studio Access to API Services** only in a safe test copy if you want DataStore persistence to work in Studio.
2. Test solo collection, upgrade costs, rebirth requirements, combo reset and Snackquake timing.
3. Use **Test > Start** with at least 2 players and confirm Legendary announcements and simultaneous orb collection behave correctly.
4. Use Studio device emulation for common phone screen sizes and verify the HUD does not cover Roblox controls.
5. Rejoin the test experience and verify saved Brainrot/level/rebirth data restores correctly.
6. Check Output for DataStore or script errors.
7. Only after those checks, configure the experience name, icon, thumbnail, description, age guidance and public permissions in Roblox Creator Dashboard.

## Still intentionally unverified
- Real-device mobile performance.
- Multiplayer load at scale.
- Public-server DataStore behavior.
- Roblox moderation/launch approval.
- Retention and monetization performance.

No paid assets or external packages are required.
