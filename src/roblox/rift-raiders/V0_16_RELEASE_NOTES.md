# Rift Raiders v0.16 — Playable First Session + Daily Life Goals

## Goal

This release addresses the biggest player-retention weakness in v0.15: 60 careers, 173+ purchasable goods and 19 destinations existed, but a new player could have no idea what to do or why. Instead of expanding the item count, v0.16 introduces **a guided first five minutes with real paid-in-game achievements** and renewable tasks.

## New features

- A compact, always-visible first-session objective card with a one-tap **GO TO SUBURBIA** action. Progressively points the player to the real template-based suburban market, first purchase, career hiring, and first honest paycheck. It is non-modal and can collapse after finishing.
- Four first steps, complete **in order**, only by server-confirmed real game actions:
  1. Explore Suburbia — 40 earned coins, 8 XP.
  2. Purchase a real item at a server-authorized market — 85 coins, 12 XP.
  3. Apply for a career at an authorized employment station — 45 coins, 15 XP.
  4. Finish a real shift by performing both timed tasks and returning for wages — 155 coins, 22 XP.
- Daily goals reset by a **UTC calendar day** and award non-repeatable daily earned-coin bonuses for one career shift, a market snack, visiting Suburbia, and harvesting one garden crop. Goals are displayed under **LIFE → MY GOALS** with completion status. The daily tracker updates without opening menus.
- A completion flourish briefly lights up the tutorial panel, and progress and rewards are described in ordinary text.
- Quest progression and daily ledger are saved in **schema v9**, migrating all prior data from v1–v8 without losing coins, cars, homes, gardening, owned goods, or life stats.
- Reward eligibility is determined on the server by successful travel, legitimate purchases, application, and work; users cannot claim free money by sending a forged client 'quest complete' event.
- Small ornamental pieces in the six imported Suburban prefabs no longer need physics collision, raycast targets, or individual shadows. Walkable floors, stairs, walls, and other substantial structures retain collision. Workspace instance streaming remains enabled.

## Research applied

Design study consulted publicly accessible Roblox Creator Hub and open-source frameworks, rather than attempting to copy private Brookhaven/Bloxburg source code:

- Roblox Creator Hub Onboarding: https://create.roblox.com/docs/production/game-design/onboarding — first minute clarity; learn controls/core loop, get to fun quickly, progression, reward feedback.
- Roblox Creator Hub Retention: https://create.roblox.com/docs/production/analytics/retention — short, medium and long-term player goals; daily challenges, broad progression.
- Roblox Creator Hub Performance: https://create.roblox.com/docs/performance-optimization/improve — minimize render overhead, expensive Heartbeat work, collisions/dense detail and track actual performance.
- Roblox Nevermore: https://github.com/Quenty/NevermoreEngine — modular services and testable interfaces.
- Matter ECS: https://github.com/matter-ecs/matter — data-driven component systems for larger worlds.
- ProfileService patterns: https://github.com/MonzterDev/Roblox-Game-Template — useful future reference for robust session-locked player state. No outside package was installed; existing code stays self-contained.

## Validation

- New Studio smoke tests check intro-state initialization, sanitization, day rollover, resuming a legitimate completed day, imported art and the newly optimized micro-decor settings.
- Two-player regression exercises the **real** onboarding travel, first purchase with exact real currency accounting and one-time reward, legal hiring, completing each physical shift task, legitimate wages, and per-player isolation. Prior car/boat security, garden purchases, suburban market, downtown careers and original rift quests remain regression-covered.
- *Actual Android/iOS quality, live Roblox DataStore leave-and-rejoin testing, online asset entitlement and device performance remain unverified.* These must pass before a public launch.

## What is **not** finished

The full GTA/Sims-style game still needs years-level content scope: unique high-resolution car meshes/chassis, animated actors, accessible real building interiors and shop displays, phone profiling across devices, production data session-locking, quests tailored to different player tastes, player-to-player roleplay economics and future live retention metrics. v0.16 is another concrete playable quality improvement—not a declaration of final completion.

No Robux charging, public publishing, paid assets, plugins or subscriptions were activated.
