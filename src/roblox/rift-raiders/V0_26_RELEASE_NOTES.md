# Rift Raiders v0.26 — Recover Real Suburban Interiors

## Why this release exists
The user reported a major practical problem: the city looked detailed from outside but many buildings could not be entered. The imported, legally reusable Roblox Suburban template actually already includes furnished houses, a convenience market and a fully modeled garage. Its old scripts had been removed for safety, leaving the entrances as static parts without working door controls.

## Implemented
- Retained the original detailed interiors and source house/store/garage meshes. Added **six independently usable original imported entrances**: single-story house, two-story house, convenience market, garage pedestrian entry and two overhead garage bay doors.
- Each is a server-owned `ProximityPrompt` attached to the source entrance. The controller validates a living character within 12 studs of that exact door, then eases the imported actual door panel(s) sideways or upward with a short built-in TweenService animation. Door colliders and ray queries are disabled as they move out of the opening. No client trust, teleport doorway, per-frame server heartbeat or free premium asset needed.
- A door remains open for the current server session after activation so automatic close cannot trap visitors or cause accidental obstruction. Repeated use does not duplicate door animation, game currency or ownership actions; visitors can explore buildings without buying them.
- Disabled obsolete imported `ClickDetector` interactions that would otherwise appear clickable but do nothing after source script sanitation.
- Reused the **existing detailed convenience market checkout**: the original register is now a legal entry point for HOME/GARDEN/TECH shopping and 15-earned-coin snack purchase, using the preexisting server-validated economy, hunger and cooldown checks.
- Added a reachable interior vehicle dealer contact point in the original detailed garage without bypassing purchased-car ownership rules. Existing external suburban job points remain intact.
- Kept all current worlds, NPCs, cars, inventory, houses, prior saves, quests, earnings, and the v0.25 newly walk-in downtown shops.

## Verification
- Rojo build, Studio smoke, and two-client multiplayer regression. See `V0_26_QA.md` for actual results. No public release or payments.

## Scope limitation
This is not a complete AAA-style city with all buildings furnished and accessible. The two new physical downtown shop shells and restored suburban house/market/garage entries are first-pass walk-in destinations. Interior navigation, appearance, crowd interactions, device performance, all imported tower doors, collisions, animation, mobile/gamepad control, copyrighted asset/permission audit and production persistent-player tests remain work for further iterations.
