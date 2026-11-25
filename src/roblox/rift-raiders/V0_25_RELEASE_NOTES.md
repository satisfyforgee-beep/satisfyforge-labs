# Rift Raiders v0.25 — City Repair Pass / Shop Entrances / Grounded Cars

This release responds to actual owner play-test feedback: inaccessible buildings, cars facing the wrong way, and floating or misplaced scenery.

## Changes
- **Reversed traffic fixed:** The official white sedan has headlights at local -Z. A previous forced 180-degree rotation drove those cars backwards. Traffic now faces forward and visually rests with the wheel bounds at the Modern City road surface (about world Y 1.1).
- **Personal sedan visuals corrected:** The white, red and racing bodies no longer rely on guessed 180/90-degree rotations. The game measures each imported model's actual front and rear bumper positions, aligns that direction to the vehicle's server driving heading, and grounds the visible tires against the existing collision chassis. Ownership, throttle and driving controls remain unchanged.
- **Two physically walk-in shops:** The Corner Market and Bean & Brew now have actual collidable indoor floors, enclosing walls, an open central pedestrian entrance, windows, illuminated storefront labels, roof, internal lighting, and a graded entrance ramp. The prior retail scanning/shelving and espresso preparation/register workflows sit inside. Unlike decorative imported skyscrapers, **these shop doors are physically traversable with no teleport**.
- **Connected shopping arcade:** Both tactile job businesses, their physical worksite signs, and the café venue sign moved just beyond the dense imported high-rise collider area to the near-downtown pedestrian arcade around Z 2120, with continuous public paving and lighting. Studio confirmed **zero collidable external objects across both entry-door volumes**.
- **Floating prefabs fixed:** Six official suburban prefabs are newly bottom-aligned near the grass surface at world Y 0.60 instead of hovering at Y 2.05. Downtown NPC sedan wheel bounds align with their road, and player official sedan visuals align with the collision chassis.
- **Misplaced tree row corrected:** A row of seven Life City facade trees was being positioned at world Z 3138 instead of Z 1538 due to mixing relative and absolute coordinates. It is now in the right neighborhood.

## Test evidence
- Roblox Studio v0.25 smoke suite checks normalized traffic bumper heading, traffic ground clearance, actual two-shop geometry and clear entrances, and suburban prefab world bounding-box bottoms.
- Two-player multiplayer regression validates cars, imported meshes, hiring/worksite interaction, retail, cafe, courier, economy and player-isolation rules. Refer to V0_25_QA.md for exact final result.

## Important limits
Not every imported downtown skyscraper, suburban house, or original prop now has an accessible interior; these still need a systematic bespoke collision and gameplay rebuild. The two newly physical shops are a beginning, **not** a claim that the whole city is fully walkable. True physical driving suspension, steering wheel animation, realistic traffic intersection behavior, human mobility accessibility validation, asset permission checks, mobile FPS and diverse playtester feedback remain outstanding. No public publish, Robux purchase or profile migration.
