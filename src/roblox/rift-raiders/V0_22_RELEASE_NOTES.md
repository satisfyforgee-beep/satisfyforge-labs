# Rift Raiders v0.22 — Playable Downtown Retail Checkout

## Added this release
- Built **The Corner Market**, a physical three-department retail scene near the Modern Downtown retail workplace, with product checkout counters, barcode scanners, shelf displays, packaged goods and readable signs.
- Downtown Retail Associate shifts now give each worker a **server-selected checkout item and restock item** drawn from groceries, electronics and toys. The customer order is shown in the Life task HUD. Players scan the right item, move to the correct restock shelf, then return to the original retail workplace for wages.
- A completed restock yields one earned 8-coin tip and 4 XP in addition to ordinary Retail wages. Wrong products, skipping tasks, interacting from far away, trying to repeat paid actions and acting without a valid shift are rejected server-side.
- Earlier **Life City and Suburban Retail** jobs retain their existing entry-level two-task flow. Their tutorials and day-goal progress are not removed or overwritten.
- Does not alter persistent DataStore schema (still v10), paid products, user accounts or publication status. No additional continuous render or physics loop.
- Existing mechanic bay, cafe, imported city, starter achievements, car/boat ownership and housing remain in the project.

## What is and isn't validated
- Rojo source-place compile and Roblox Studio runtime smoke check validate the new physical retail area and server-selected orders.
- The two-client Studio test specifically exercises unauthorized/remote retail calls, incorrect checkout and shelves, correct task order, duplicate tip prevention, independent HUD state and wage collection. Results must be recorded from the executed test rather than assumed.
- The stylized checkout displays are low-part-count procedural props, not a licensed high-end imported supermarket or a polished AAA retail experience. Store customers, hand-held item animations, sounds and NPC shopping queues still need work.
- Full phone frame-time/memory profiling and live cross-server DataStore verification remain unperformed. Public publishing and monetization remain disabled.

## How to play
Open `RiftRaiders-ChaosIslands-v0.22.rbxlx` in Roblox Studio. From the starting downtown district, visit the city employment center and accept **Retail Associate**. Start a shift at **Downtown Worksite RETAIL**. Move to **The Corner Market**, scan the HUD-matched product at its checkout counter, then restock the HUD-matched category at the shelf. Return to the Retail worksite for wages.

## Reference and design approach
The retail roleplay category and easily understood store location were benchmarked against public Berry Avenue RP gameplay and the official Roblox experience listing, without copying proprietary scripts or artwork. The useful pattern is **clear, recognizable venues plus meaningful actions**, not multiplying inert props.
