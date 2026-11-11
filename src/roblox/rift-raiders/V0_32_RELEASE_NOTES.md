# Rift Raiders v0.32 — Phone Guide Clearance

## Player-visible change

The first-session guide and daily-goal panel no longer keep a fixed 265–270 px width on narrow touch screens. Their shared width now derives from the active camera viewport and leaves a measured 15 px minimum gap before the existing right-side action controls at common 320–414 px portrait widths.

The layout recomputes when the camera viewport changes, so rotation or window resizing does not restore the overlap. Desktop keeps the existing 325 px guide width, and wider touch displays remain capped at 265 px.

## Implementation

- Added `MobileLayout.lua`, a pure layout helper shared by the client and Studio QA.
- Wired `Client.client.lua` to resize both guide panels from current `ViewportSize.X`.
- Added viewport-change rebinding without creating another HUD or input system.
- Added deterministic checks for 320, 360, 375, 390 and 414 px touch widths plus desktop/wide-touch regressions.
- Version marker advanced to `0.32.0`.

## Boundaries

This change has no Robux flow, rewards, persistence, public publishing, or production account mutation. Automated layout math and Studio smoke do not prove comfort on an actual low-end phone; real-device portrait/landscape play remains a release gate.
