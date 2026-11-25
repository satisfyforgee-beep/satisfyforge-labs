# Rift Raiders v0.28 — Align Original Houses to Their Real Ground Floors

**Scope:** Private, zero-cost world-quality repair; no public release or save-schema change.

## Defect proven in the Roblox engine
The official Suburban prefab's bounding-box minimum is **not** necessarily the building's real floor. The first imported house's entrance was at about **Y 20.22 studs**, and the second house's entrance at **Y 27.68** even after earlier attempts to align each entire model's decorative lowest point to Y 0.60. Walking to those front doors from the neighborhood was therefore impractical despite the restored door animations.

## Repairs
- For both original imported furnished house templates, discover the actual named `Floor` parts (large enough to be usable interior rooms), calculate the **lowest first-floor upper surface**, then translate the complete original house model so that real ground-floor surface is **Y 1.8**. Keep the separate upper-story floors, staircase, walls, furniture, original model geometry, doors, and ornaments in correct relative positions.
- After this correction, the original first-story doorway markers sit at about **Y 6.10**, verified in a separate actual Studio navigation geometry run. These are real door control positions; the walkable surface is lower, at Y 1.8.
- Build two simple but solid nonteleporting concrete approach walkways (one per house), aligned from each front door outward toward neighborhood grass. Their upper walking surfaces descend from ~Y 1.8 to ~Y 0.5 over 12 studs; the normalized slope and correct outward orientation are regression-tested in Studio.
- Stop claiming decorative bbox bottoms measure building grounding. Record `GroundReferenceMode=ActualFirstFloor`, `WalkableGroundFloorTop` and an informational actual bbox minimum. Continue to check the prior official market/garage/gas station models separately against their own authentic model positions without relocating them.
- All six v0.26 working server-controlled suburban doors remain; the ground-contact correction is upstream of their position registration. Also retain v0.27 continuously forward-moving traffic and natural nonteleporting pedestrian route recovery.

## Validation and limits
- Rojo build, real Roblox Studio smoke and real two-client Studio regression results are recorded separately in `V0_28_QA.md`.
- This is a **targeted house grounding fix**, not proof every imported building is accessible. Manual ground-level navigation through entire rooms, actual device FPS, authentic real-life driving, four-person online testing, active creator-account asset permissions and real live DataStore rejoin remain open release gates.
- The two-house footpaths and basic geometry are not claimed to be finished professional landscaping or formally certified accessibility surfaces. The source meshes remain visually detailed but some imported decoration and source dimensions may be unsuitable for low-end mobile.
