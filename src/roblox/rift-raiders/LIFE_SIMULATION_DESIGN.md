# Rift Raiders v0.6 — Life City simulation foundation

## Product vision

A player can begin with basic equipment, choose a career, work timed shifts, purchase personal belongings, save for transport or property, open businesses, produce creator videos and encounter in-world consequences for fictional crime. All prices in this prototype are **in-game coins**, not USD or Robux. A player does not purchase real-world property or goods.

This is a deliberately limited **first playable vertical slice**, not a complete life simulator or photorealistic world.

## Playable first slice

- A new **Life City** world destination, terrain, boulevard, lane markings, six detailed storefronts, an employment center, seven workstations, a recording studio, a courthouse fine counter, a jail, and two patrolling/chasing police models.
- Seven careers: retail associate, courier, barista, mechanic, construction worker, police officer and content creator. Careers have level gates; employment is selected at the Career Center. Wage work is a timed two-step shift at the corresponding workplace, with cooldown and XP.
- A **21-item** server-owned catalog with apparel, electronics, groceries, cars, boats, real estate and four business types. Items have level and earned-coin requirements. Purchases require standing inside the appropriate physical store.
- Creator progression: purchase smartphone + camera, equip the actual Camera Tool, take the creator career, record at the media studio, gain followers and earn coins. Microphone and editing workstation improve results. There is no actual uploading, social network connection or real sponsorship income.
- Business progression: buy a café, auto shop, media studio or realty office, then collect simulated business income from the business office at most once every 90 seconds. This is not passive/offline income or a real player-to-player marketplace.
- Owned property: apartment, townhouse and mansion purchases generate distinct owner-labeled building exteriors on allocated Life City plots. Interiors, mortgage, rent, construction and persistent plot placement remain future work.
- Owned car tiers change the player's spawned car paint. The generic drivable hovercar still uses arcade physics. Boat purchases are ownership entries only; they are **not yet drivable**.
- Police NPCs detect high heat, pursue nearby suspects and arrest after sustained pursuit. Arrests impose a 20-second in-game jail stay, a coin penalty and outstanding fine. Officers return to patrol after the encounter. Players can take the police career but cannot arrest other players yet; this prevents harassment until moderation and safeguards exist.
- A dedicated LIFE panel displays catalog, owned items, creator and career stats. Player progress saves through a version 4 profile schema, migrated from v1-v3 without resetting existing coins, levels, house ownership or prestige.
- No Robux checkout, external purchases, or public publishing has been activated.

## Reality gap and roadmap

1. **Interactivity:** task-specific job minigames (barista recipes, deliveries with real parcels, repairs with parts, construction, police dispatch and incident evidence); interiors, furniture placement, apartment renting, real boats and multiple vehicle handling classes.
2. **Police and justice:** better pathfinding, actual evidence and witness checks, clearly marked in-game laws, traffic stops, non-abusive player police roles, appeal process and no paid-item confiscation.
3. **Creator career:** first-person camera preview, filming/clip editing, in-game channel page, simulated audience interests, meaningful content quality rather than repeated button pressing, live events and creator collaborations.
4. **Economy:** balanced salary tiers, taxes and bills if genuinely fun, business staffing, storefront customization, player-to-player trade protections, anti-inflation sinks, auctions and optional property rentals.
5. **Visual realism:** Blender-made optimized vehicles, architecture, PBR materials, animations, sound design, ambient crowds, road signals, rain, and mobile profiling. Current buildings and officers are hand-built Roblox primitives, not photoreal.
6. **Production:** secure DataStore session locking, versioned migrations and rollback tests, job/purchase rate-limit tests, mobile UI, anti-cheat, accessibility, player safety and moderation, retention testing.
7. **Monetization:** keep the entire core economy earnable; offer optional distinctive cosmetics only after real Roblox pass/product IDs are configured, ownership and receipt handling are verified, and the creator approves prices.

## Important limits

This is a fictional simulation. No physical goods, real cars, actual homes, actual money, real-world arrest, or real social media publication is created by playing it. Players cannot exchange coins for real money. The code should never suggest otherwise.
