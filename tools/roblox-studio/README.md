# SatisfyForge Roblox Studio Test Runner

This folder turns a connected Mac with Roblox Studio into a zero-cost local Roblox engine test node.

It uses Roblox Studio's documented command-line `RunScript` task plus Rojo-built `.rbxlx` files. That means smoke checks execute inside Roblox Studio rather than pretending a generic Lua interpreter is the Roblox engine.

## Current games

- Brainrot Rush
- Tile Panic

Snackquake currently lives in the preserved source archive / playtest place outside the repository and is tested separately until its recovered source is canonically imported.

## Run

```bash
python3 tools/roblox-studio/run_smoke.py --game all
```

Optional overrides:

```bash
python3 tools/roblox-studio/run_smoke.py \
  --studio /Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio \
  --rojo ~/SatisfyForge/tools/rojo/rojo \
  --game brainrot-rush
```

## What this proves

A passing runtime smoke proves that Roblox Studio can load the generated place, start simulation, execute the server scripts, and satisfy the game's explicit structural/runtime assertions.

It does **not** prove full release readiness. Multiplayer, actual player controls, phone/gamepad UX, live DataStore behavior, purchases, moderation/public metadata, retention and real-player evidence remain separate release gates.

## Safety / truth rules

- Do not claim a game is published merely because a local `.rbxlx` passed.
- Do not claim DataStore is verified from an unpublished local file.
- Do not turn on paid purchases until the exact purchase and fulfillment path is tested.
- Keep public release separate from automated runtime testing.
