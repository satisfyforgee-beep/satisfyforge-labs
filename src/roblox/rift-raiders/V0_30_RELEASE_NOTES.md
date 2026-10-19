# Rift Raiders v0.30 — Interactive Original House Lighting

Date: October 19, 2026 (America/New_York). **Private, zero-cost development build.** No public publishing.

## The gameplay improvement

The two original highly detailed Roblox Studio suburban house templates contained actual SpotLight fixtures in their furnished kitchens, living areas, bedrooms, baths, hallways, and offices, but their old toolbox scripts were intentionally stripped for safety and many decorative `LightSwitch` models contained **no physical parts**. Players could walk into these previously restored homes but their lighting remained an inert decoration.

A new internal server-owned `SuburbanHomeLights.lua` now detects the original fixture groups, attaches visible Roblox `ProximityPrompt` actions to the **real original light fixtures**, and switches the existing `SpotLight`, `PointLight` and `SurfaceLight` instances in each room together. The real original house geometry, animations, house floor placement, doorway geometry, and original lighting art are preserved; no scripts or model downloads from third parties were enabled.

Studio smoke inspection found **20 functional original light groups** across two furnished houses. Each toggle changes actual light `Enabled` states for all players, updates its `TURN LIGHTS ON/OFF` prompt text, and informs the player. It is a session-only shared public-showcase interaction, not a player-owned or persistent electric utility; no coins or XP awarded.

## Security

Only a living character located within 12 studs of that original light fixture can toggle it. Repeated toggles under 0.4 seconds are rejected. Unsupported keys and remote players are rejected by the server. No changes to existing profile schema, privacy, ownership, jobs or live DataStore. ProximityPrompt client hints alone are not trusted as authorization.

## Engine validation

See `V0_30_QA.md` for the final Rojo build, Roblox Studio smoke and full multiplayer test outcomes. Roblox native phone gameplay, full furnished-house interior human playtesting, and original asset permissions still require independent checks.

The game remains a private prototype under `SHIP_CRITERIA.md`.
