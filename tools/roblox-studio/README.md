# SatisfyForge Roblox Studio Test Runner

This folder turns a connected Mac with Roblox Studio into a zero-cost local Roblox engine test node.

It uses Roblox Studio's documented command-line `RunScript` task plus Rojo-built `.rbxlx` files. That means smoke checks execute inside Roblox Studio rather than pretending a generic Lua interpreter is the Roblox engine.

## Current games

- Brainrot Rush
- Tile Panic
- Snackquake v0.2.1

All three now have canonical repository source/build mappings and Roblox Studio runtime smoke coverage. Snackquake's original recovered archive/playtest place remain preserved separately as provenance artifacts.

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

## Multiplayer regression gates

```bash
python3 tools/roblox-studio/run_multiplayer.py
python3 tools/roblox-studio/run_tile_multiplayer.py
python3 tools/roblox-studio/run_snack_multiplayer.py
python3 tools/roblox-studio/release_preflight.py
```

The Snackquake two-client Studio test checks independent player profiles, upgrades for each client, denial of unowned creature equip/fusion, and rejection of an upgrade without enough Fizz. It also confirms that Studio sessions do not write live DataStore data. These are **simulated Studio clients**, not a substitute for live save/rejoin, full rescue-loop playtesting, or physical mobile-device testing.

## Existing-place publishing helper

`publish_place.py` prepares the final Open Cloud upload step without storing credentials. It is a dry run unless `--confirm-publish` is supplied.

```bash
python3 tools/roblox-studio/publish_place.py \
  --file /absolute/path/game.rbxlx \
  --universe-id 123 \
  --place-id 456
```

For a real update to an **existing** Roblox place, create an Open Cloud API key with `universe-places:write` for that experience. The script reads `ROBLOX_OPEN_CLOUD_KEY` if present or asks for the key with a hidden prompt; it never prints or writes the key. Add `--confirm-publish` only after the target IDs and tested file are verified. First-time creation of a new experience remains a separate Studio/Creator Dashboard step.

## What this proves

A passing runtime smoke proves that Roblox Studio can load the generated place, start simulation, execute the server scripts, and satisfy the game's explicit structural/runtime assertions.

It does **not** prove full release readiness. Multiplayer, actual player controls, phone/gamepad UX, live DataStore behavior, purchases, moderation/public metadata, retention and real-player evidence remain separate release gates.

## Safety / truth rules

- Do not claim a game is published merely because a local `.rbxlx` passed.
- Do not claim DataStore is verified from an unpublished local file.
- Do not turn on paid purchases until the exact purchase and fulfillment path is tested.
- Keep public release separate from automated runtime testing.
