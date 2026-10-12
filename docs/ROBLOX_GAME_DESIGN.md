# Brainrot Rush — game design roadmap

## Current prototype v0.2
- Server-generated arena and spawn
- Four collectible rarity tiers: Common (70%), Rare (23%), Epic (6%), Legendary (1%)
- Currency payouts of 1, 5, 20, and 100, multiplied by (1 + upgrade level)
- Upgrade pad: proximity prompt, cost = 20 × (next level)^2; cap level 20
- Leaderboard tracks currency, total collected, and upgrade level
- Orbs expire after 45 seconds, with a maximum of 30 active

## Next development priorities
1. Playtest multiplayer touch collection and mobile proximity prompts in Roblox Studio.
2. Add original, memorable collectible characters and animated feedback.
3. Add DataStore persistence with protected reads/writes and autosave.
4. Add timed rounds, meaningful decisions, and optional cooperative challenges.
5. Add accessibility options and mobile-friendly UI.
6. Test balancing, retention, performance, and anti-exploit behavior before monetization.

## Design principles
Use original assets and names. No copied characters, deceptive monetization, or pay-to-win pressure. Keep the core game playable without purchases.

## Status
Code committed to GitHub; Roblox Studio testing and publishing have NOT been completed.
