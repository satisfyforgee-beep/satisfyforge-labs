# Rift Raiders v0.10 — Living Downtown

Modern Downtown now has visible population and moving traffic instead of functioning like an empty stage set.

## Added
- 8 R15 Humanoid downtown citizens with varied body colors/scales and sidewalk walking routes.
- Roblox R15 walk animation playback when available.
- 4 moving detailed traffic sedans using the script-free official Modern City sedan visual.
- Server-owned traffic distance tracking for runtime/test verification.
- Two pedestrian routes deliberately cross the welcome block so the city feels populated immediately.

## Validation
- Smoke testing verifies all 8 citizens are R15 rigs.
- Smoke testing verifies all 4 detailed traffic sedans exist and actually move.
- Multiplayer testing verifies both a citizen and traffic continue moving during a two-player session.

## Current limits
Pedestrians currently use repeated Humanoid MoveTo routes, not full pathfinding/crowd intelligence. Traffic uses anchored server-moved visual vehicles, not a full suspension/chassis AI. No Robux products or public publishing are activated.
