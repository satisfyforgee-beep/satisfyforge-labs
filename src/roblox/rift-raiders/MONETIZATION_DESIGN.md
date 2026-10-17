# Rift Raiders Creator Revenue Plan (not activated)

Goal: make a free, high-quality Roblox game people voluntarily support. In-game coins are NOT cash and cannot be cashed out. This document does not create or activate any purchases, advertisements, subscriptions or financial transfers.

## Free core
All main worlds, sports, resource collection, starter housing, fishing, jobs, basic vehicles, and progression should remain accessible without Robux. Let players earn upgrades and have fun for free.

## Ethical paid additions to consider AFTER player testing
1. Vehicle cosmetic paint packs, rims, exhaust glow and garage decorations (one-time pass or fixed-price item).
2. House wallpaper, furniture styles, landscaping, signs and lighting themes (cosmetic).
3. Noncompetitive avatar emotes, dances, photo poses, pet appearances and nameplate themes.
4. Private servers for friends and clubs where Roblox permits.
5. Seasonal cosmetic collections with clearly stated prices and no artificial scarcity.
6. Optional supporter pass that grants visual flair but no essential progression or unfair competitive advantage.
7. Subscription only if there is a genuine, maintained monthly cosmetic benefit and clear cancellation expectations.

## Technical launch gate
- Publish a private/new test experience and complete content maturity questionnaire first.
- Obtain genuine Roblox pass/product IDs from the correct creator-owned experience.
- Validate one-time ownership on the server; for repeatable developer products implement idempotent ProcessReceipt and durable grants.
- Do not accept client-reported payment completion. Never grant items from a spoofed remote event.
- Never use paid random lootboxes without policy eligibility checks, odds disclosure and all required restrictions; the preferred plan is no paid random items.
- Show clear pricing and avoid deceptive pressure. Test on mobile and low bandwidth.
- Measure first-session experience, D1/D7 retention, user sentiment, device crashes and voluntary purchase conversion before scaling.

## Real revenue mechanics
Roblox provides creator earnings through eligible passes, developer products, subscriptions, Creator Rewards and other supported options. The platform retains fees, and cash-outs through DevEx require eligibility, a minimum earned Robux balance and Roblox approval. No income is guaranteed.

Official docs:
https://create.roblox.com/docs/get-started/monetization
https://create.roblox.com/docs/production/monetization
https://create.roblox.com/docs/production/monetization/developer-exchange
https://create.roblox.com/docs/production/monetization/developer-products

## v0.5 progression implementation (earned coins only)

The prestige shop now has eight **permanent, server-validated, earnable** unlocks:

| Unlock | Level | Coins | Extra materials | Visual or functional result |
|---|---:|---:|---|---|
| Midnight City Car Wrap | 3 | 450 | — | Midnight paint on personal cars |
| Modern Estate Roof | 5 | 1,200 | — | Slate roof and warm exterior lights |
| Snowmobile Driver License | 5 | 1,400 | — | Unlock snowmobile use |
| Jetpack Pilot License | 7 | 2,200 | — | Unlock Arctic jetpack station |
| Platinum Hypercar Finish | 10 | 3,800 | — | Platinum paint on personal cars |
| Luxury Home Garage | 12 | 6,000 | 10 wood, 8 metal | Physical garage and driveway |
| Flying Car Pilot License | 12 | 6,500 | — | Unlock flying car |
| Aurora Legend Trail | 18 | 9,000 | — | Glowing avatar trail |

This is **not** a Robux store. The in-game shop explicitly says no Robux cosmetics are on sale. Basic personal cars, sports, fishing, exploration and the main quest are free. Advanced mobility requires earning licenses.

## Recommended OPTIONAL Robux store (concept, not live)

- 49 Robux: one original cosmetic wrap or decor theme.
- 99 Robux: a 3-pack of vehicle colorways or house furniture designs.
- 199 Robux: permanent visual supporter pack (nameplate, trail, emotes).
- 399 Robux: a larger aesthetic bundle (garage decorations, house styles, pet skins).

These are **draft price points only**. No passes/products are created, and no user has been charged. Verify product IDs, asset rights, pricing and entitlement logic in a new published test experience before activation. Use Roblox MarketplaceService passes for permanent one-time purchases and idempotent ProcessReceipt for developer products; do not grant purchases based on client claims. Keep paid cosmetics distinctive but do not sell a competitive advantage.

**Retention and pacing goals, to validate with actual playtest data:** first fun action in 30 seconds; first reward within 2 minutes; first meaningful unlock within 5–10 minutes; early prestige within 30–60 minutes; advanced vehicle license after a few hours of engaging activities; legendary cosmetics over multiple sessions. Adjust rewards based on measured median earning rates. Avoid deliberately frustrating free users, coercive timers, and paid randomized items.

**Financial truth:** A game can earn Robux through eligible Roblox purchases and other creator programs, but the platform keeps its share and DevEx eligibility applies. Player coins are not creator cash. No guaranteed revenue.

## Before enabling real-money purchases
1. Complete a polished, tested and fun free gameplay loop.
2. Obtain explicit user approval for which items and prices to publish.
3. Publish only to a new private test experience under the intended creator.
4. Create actual Roblox pass/developer product IDs and read back ownership.
5. Implement server-side pass verification and secure idempotent developer product receipt handling.
6. Run multiplayer, reconnection, failed DataStore load and receipt replay tests.
7. Complete Roblox maturity/content and policy checks.
8. Review retention, device performance, user complaints and conversion before launching.
