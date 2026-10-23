# Rift Raiders v0.17 — Suburban Discovery Trail

## Play it instead of browsing a catalog

Rift Raiders now rewards **exploration in the actual detailed Suburban environment**, not only shopping, jobs and teleporting between maps.

Eight hidden, visually glowing keepsakes are scattered near the imported Suburban homes, convenience market, gas station, detailed garage, playground, and streets. Players must walk/drive to each object's physical location and trigger its **COLLECT KEEPSAKE** ProximityPrompt. A clearly visible in-game tracker reports how many items are found, including a LIFE → MY GOALS description.

Found objects:
1. Lost Camera Lens
2. Family Heirloom Key
3. Market Shopping Token
4. Vintage Fuel Badge
5. Collector Gear
6. Playground Lucky Charm
7. Bridge Map Fragment
8. Suburban Explorer Star

Each object earns an earned-coin reward (20 to 34 coins) and 10 XP, plus a **180-coin and 45-XP completion bonus** after all eight are collected. The eight-item trail resets at the UTC calendar-day boundary so the neighborhood remains worth revisiting. Objects can be claimed only once per player per day; two people can collect the same physical token without taking it away from one another.

**Exploit protection:** There is no new remote event for claiming coins. All requests go through real Roblox ProximityPrompts and server-owned `SuburbanDiscovery.Collect` validation. A claim is rejected if the character is missing/dead, if the player is more than 13.5 studs from its actual location, if the ID is invalid, or if the collectible has already been redeemed. Rewards are server-calculated. Saved profile schema **v10** adds only a small, strictly sanitized 8-item daily collection ledger while migrating existing v1–v9 progress.

## Tests

- Roblox Studio smoke test validates eight physical prompt locations, module availability, repeatable reset behavior and invalid state sanitization.
- Multiplayer tests verify rejected long-range collection, a legitimate nearby collection, earned coin and progress, prevention of a second claim and player-isolated progress.
- Realistic imported Modern City, Suburban architecture and Racing assets remain, alongside the new-player tutorial and daily career/garden goals from v0.16.

## Design references

We use Roblox Creator Hub retention/engagement patterns (short-term goals, exploration and earned achievements), Matter's separation of gameplay systems, Nevermore-style modularity, and the existing server-authoritative gameplay project. No code or branding was copied from private Roblox games or any other creator's place.

## Remaining work

The actual high-detail level is still uneven. The main city has imported professional-looking art, but many vehicles/homes and the hidden keepsake models are stylized Roblox geometry, not licensed AAA meshes. There's no polished narrative questline, advanced vehicle suspension, fully animated shopkeepers, or verified live production DataStore session persistence. Real iOS/Android performance and long-session memory must be tested before publishing. Some hosted art still raises Roblox platform asset-compliance warnings, which requires a rights/permissions review.

No real money, Robux, subscriptions, external accounts or public publishing were used.
