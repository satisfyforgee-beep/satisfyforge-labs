# Rift Raiders v0.7 — Life City simulation and career expansion

## Product vision

A player can begin with basic equipment, choose a career, work timed shifts, purchase personal belongings, save for transport or property, open businesses, produce creator videos and encounter in-world consequences for fictional crime. All prices in this prototype are **in-game coins**, not USD or Robux. A player does not purchase real-world property or goods.

This is a deliberately limited **playable vertical slice**, not a complete life simulator or photorealistic world. The new architecture and workplace props use Roblox primitive geometry, textures from built-in materials and original procedural detailing; **they are not imported high-poly models or cinematic-quality assets**.

## Playable first slice

- A new **Life City** world destination, terrain, boulevard, lane markings, six decorated storefronts with physical merchandise displays, awnings, signs, window trim, lighting and sidewalks, a career center, 20 workplaces, recording studio, court counter, jail and two pursuing police models. City streets include crosswalks, landscaping, a fountain, streetlamps, benches, **eight walking citizens and two moving traffic cars**.
- **20 careers**: retail, courier, barista, mechanic, construction, police, creator, paramedic, firefighter, chef, farmer, teacher, sanitation, electrician, plumber, veterinarian, real estate agent, photographer, pilot and musician. Level-gated employment is selected at the Career Center. For 19 wage careers, each shift requires **two distinct job-specific interactions in order**, at the actual workplace, before returning to collect wages; tasks are server-validated for proximity, timing and career. Photography requires a camera; musicians need a guitar.
- A **28-item** server-owned catalog with apparel, electronics, groceries, cars, boats, real estate and four business types. Items have level and earned-coin requirements. Purchases require standing inside the appropriate physical store.
- Creator progression: purchase smartphone + camera, equip the actual Camera Tool, take the creator career, record at the media studio, gain followers and earn coins. Microphone and editing workstation improve results. There is no actual uploading, social network connection or real sponsorship income.
- Business progression: buy a café, auto shop, media studio or realty office, then collect simulated business income from the business office at most once every 90 seconds. This is not passive/offline income or a real player-to-player marketplace.
- Owned property: apartment, townhouse and mansion purchases generate owner-labeled houses on allocated Life City plots, with sloped roofs, porches, chimneys, landscaping, and walkable **ground-floor** rooms containing sofa, bed, kitchen, and interactive rest/wash prompts. Multi-floor access, advanced interiors, mortgage, rent and persistent plot placement remain future work.
- Owned car tiers change the player's spawned car paint. The generic drivable hovercar still uses arcade physics. Boat purchases are ownership entries only; they are **not yet drivable**.
- Police NPCs patrol defined routes, detect high heat, pursue nearby suspects and arrest after sustained pursuit. Arrests impose a 20-second in-game jail stay, a coin penalty and outstanding fine. Officers return to patrol after the encounter. Players can take the police career but cannot arrest other players yet; this prevents harassment until moderation and safeguards exist.
- A dedicated LIFE panel displays catalog, 20 career options, owned items, active job objectives, creator and career stats, and **hunger, energy and hygiene**. Needs decline gradually and after work; the free community kitchen and public park offer recovery without pay-to-play traps. Player progress saves through a version **5** profile schema, migrated from v1-v4 without resetting existing coins, levels, house ownership or prestige.
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
