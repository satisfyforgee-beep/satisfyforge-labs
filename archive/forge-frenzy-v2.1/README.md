# Forge Frenzy v2.1 — recovered browser-game asset

Recovered from the verified Library artifact `SatisfyForge_Forge_Frenzy_v2_1_Repair_Kit.zip` on 2026-10-13.

This is an archived browser-game project, not the current SatisfyForge social-video direction and not a replacement for the Roblox projects.

## Verified 2026-10-13

- The repair kit's **19 browser-logic tests passed** again.
- The recovered game HTML was committed under `games/forge-frenzy-v2.html`.
- The SatisfyForge GitHub/Playwright cloud browser ran the real page in Chromium and passed the interaction smoke in Actions run `38370399715`.
- Verified smoke observations: title loaded correctly, initial timer was 60, the Start button was present, clicking Start hid the tutorial, timer advanced to 59 after ~1.6 seconds, the summary remained hidden during play, the canvas rendered at 1440×1100, and Playwright captured **zero page errors**.

## Contents
- `games/forge-frenzy-v2.html` — repaired game
- `apps/experiment-dashboard.html` — recovered dashboard from the original repair kit; not yet centralized as live app
- `tests/browser-logic.test.cjs` — 19 logic tests from the repair kit
- `BUILD_MANIFEST.json` — kit manifest

## Truth boundary

The game now has both regression-test evidence and a real headless Chromium start-flow smoke pass. That still does **not** prove a complete 60-second gameplay session, every upgrade/hazard/forge interaction, mobile touch ergonomics, persistence behavior across multiple browser families, or live hosting.

Describe it as **browser-smoke-tested source**, not a live/released game, until those remaining checks and a deliberate deployment are completed.
