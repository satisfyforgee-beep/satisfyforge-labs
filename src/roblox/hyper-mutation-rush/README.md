# Hyper Mutation Rush — v0.3 private-development world

**Status:** Roblox Studio prototype, NOT uploaded to a playable Roblox experience. No monetization, no paid assets, no public launch, no guaranteed revenue.

## What actually works in the current source

- Shared bright-neon world with a 12-checkpoint speed race, 18 speed orbs, six jump lasers, two mutation gates, and a finish reward.
- Six themed districts with connecting paths: Mutation City, Crystal Caves, Sky Parkour, Battle Dome, Treasure Island, Festival Grounds.
- Seven server-authorized fast-travel destinations in the phone HUD. Unknown destinations are rejected; player teleport does not move other players.
- Activities: timed city delivery, four cave crystals, five ascending parkour platforms and summit, 12-second dome survival with failure on laser touch, three-color festival sequence, secret treasures and timed chest.
- Server-validated coin rewards and speed purchases. Free in-game pet for 120 earned coins, with a floating companion that follows its owner.
- Three timed mutation abilities: BOUNCE increases jump height, SHIELD blocks hazards, TURBO temporarily increases speed; each expires after 18 seconds and is granted by server-verified gates.
- Repeatable quest: three distinct verified activities earn 150 coins. Player leaderboard shows Wins and Coins.
- Rotating short color-storm lighting event every 85 seconds; mobile world map and clear objective.
- All coins, upgrades, pets, quests and wins are **session-only**. DataStore persistence is NOT implemented; no Robux transactions or game passes.
- Not yet proven: 15-minute device playtest, mobile touch/legibility on physical Samsung, longer multiplayer load, race completion under normal play, cloud persistence, world art polish, public release or user retention.

## Verification

- Rojo place built successfully with `~/SatisfyForge/tools/rojo/rojo`.
- Roblox Studio `RunService:Run()` runtime smoke passed with world, districts, and activity checks; **SF_MUTATION_SMOKE_PASS**.
- Roblox Studio real two-client multiplayer test passed: separate characters, allowlisted teleport, invalid destination rejection, insufficient funds rejection, cave crystal, chest, festival and 3-activity quest rewards, no cross-player wallet changes; **SF_MUTATION_MP_PASS**.
- Current source version: `0.3.0`.
- Build artifacts are generated locally and are not published.

## Run

```sh
~/SatisfyForge/tools/rojo/rojo build src/roblox/hyper-mutation-rush/default.project.json -o /tmp/hyper-mutation-rush.rbxlx
python3 tools/roblox-studio/run_mutation_multiplayer.py
```

Before inviting external players, verify persistence, onboarding, 20-minute fun/retention test, accessibility, performance on low-end Android, creator dashboard content questionnaire, private owner access, and permission to publish. Do not change any existing Snackquake/Brainrot Rush place or monetize the game before owner review.
