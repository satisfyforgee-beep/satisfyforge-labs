# Roblox Growth Blueprint — 2026-10-13

## Why this exists
This is the current evidence-based direction for SatisfyForge Roblox work. It is based on live Roblox Charts, current experience listings, and current creator/discovery guidance. The goal is to reproduce the *successful structure* of top experiences without copying protected maps, characters, UI art, names, or code.

## Current market signal
Roblox Charts on 2026-10-13 puts **Adopt Me!**, **Dandy's World**, **Blox Fruits**, **Steal An Egg**, **RIVALS**, **Fisch**, **Pet Simulator 99**, and other long-running live-service games in the Top Earning group. **Steal An Egg** is also among the highest-playing experiences, with an unusually large live audience relative to most games.

Important measurement note: Roblox changed discovery analytics measurement on 2026-10-12. Impressions/clicks/plays may read higher and PTR may read slightly lower after that date even with unchanged performance. Do not compare pre/post October 12 raw discovery numbers without accounting for that change.

## What the winners share
The strongest current games repeatedly combine these mechanics:

1. **A loop understood in seconds** — steal/rescue/collect/fight/survive -> return/deposit/win -> get currency or an item -> upgrade -> do it again.
2. **Visible permanent progression** — pets, creatures, bases, gear, unlocks, mutations, ranks, collections, mastery or upgraded production.
3. **A flex layer** — other players can see what you own, how rare it is, how strong you are, or what your base looks like.
4. **Rarity chase** — common-to-extreme rarity ladders, size/mutation/variant systems, collection indexes and rare event drops.
5. **Multiple linked economies** — one action feeds another system instead of rewards being dead-end points.
6. **Social tension or cooperation** — stealing, contested resources, group survival, trading, roles, team events or server-wide events.
7. **Live events** — seasonal content, limited creatures, update banners, event currencies and rotating goals.
8. **Fast early reward + long-term goals** — something satisfying happens in the first few minutes, but there are also hours/days of collection and upgrading.
9. **Mobile-first clarity** — large interaction targets, short routes, obvious landmarks and minimal explanation.
10. **Optional paid acceleration/cosmetics** — the base game remains playable while spending can shorten waits, improve convenience, or add status/cosmetics.

## Strongest reference pattern right now: Steal An Egg
The official experience description exposes an unusually clean loop:

**steal egg -> return to base -> hatch rare pet -> pet earns money -> upgrade base/treadmill -> gain speed -> enter harder areas -> steal from other players -> chase rarer sizes/mutations**.

This is powerful because every action feeds another action. A rare item is not just collectible; it generates money. Money is not just a score; it upgrades the player's ability to reach harder content. Speed is not just a stat; it changes route access and theft/escape viability. The collection index creates another goal on top of all of it.

### What Snackquake should borrow structurally
Not eggs, pets, exact maps, UI, names, art or prices. Borrow the dependency graph:

**rescue creature -> bring it home -> creature becomes productive/displayable -> generates Fizz over time -> spend Fizz on camp and movement upgrades -> access harder disaster zones -> find rarer mutations -> risk carrying them back through contested/hazard routes -> complete collection sets -> prestige into stronger rescue tiers.**

That is the single most important rebuild.

## Snackquake v0.3 target loop
### 0-30 seconds
- Spawn facing the Rescue Camp and central Disaster Zone.
- One giant readable objective: **RESCUE A SNACK -> BRING IT HOME**.
- First rescue should be close, obvious and nearly impossible to misunderstand.
- First successful deposit gives a creature, Fizz, collection progress and a visible camp improvement.

### 1-5 minutes
- Player fills several visible rescue slots at their camp.
- Rescued snacks generate passive Fizz while displayed.
- Player buys one movement or carry upgrade.
- Player sees at least one rarer creature they cannot safely reach yet.
- Index shows the next near-term collection reward.

### 5-20 minutes
- Unlock next disaster biome/zone.
- Introduce mutation/size variants.
- Introduce a meaningful duplicate decision: fuse/evolve, sell/recycle, or keep for passive income.
- Server event temporarily increases a rarity, mutation or disaster type.
- Player earns first prestige/rebirth preview even if they cannot afford it yet.

### Long-term
- Multiple zones with escalating risk/reward.
- Collection index with visible milestone rewards.
- Mutation families and ultra-rare visual variants.
- Upgradeable personal Rescue Camp.
- Prestige/rebirth layer that resets some progression for permanent rescue bonuses.
- Seasonal/event collections.
- Leaderboards for rescues, rarest discovery, camp value and event contribution.

## Map rebuild direction
The present rescue loop works, but the world should become much more legible and status-oriented.

### Layout
- **Central shared Disaster Zone**: visually loud, dangerous, event-driven.
- **Player Rescue Camps around the perimeter**: personal territory, visible collection, passive income and upgrade stations.
- **Biome gates radiating outward**: each gate visually communicates the movement/carry requirement before entry.
- **Return routes with choices**: shortest route = dangerous; longer route = safer.
- **Event tower / global timer**: everyone can see the next server-wide event countdown.

### Player camp
Each camp should visibly display:
- rescued snack creatures;
- rarity/mutation aura;
- Fizz-per-second;
- camp level;
- best discovery;
- collection completion percentage;
- prestige badge.

This is the flex/status layer Snackquake currently lacks.

## Creature economy rebuild
Every rescued creature needs at least four values:
- rarity;
- passive Fizz generation;
- mutation/size modifier;
- collection/index identity.

Optional future dimensions: carry weight, disaster affinity, evolution family and event tag.

A legendary rescue should create a dramatic, shareable moment: server callout, strong VFX/SFX, visible camp display, collection update and a materially better production rate.

## Social mechanics
Add social systems in this priority order:
1. server-wide disaster/event meter;
2. cooperative frenzy bonus;
3. visible camps and rare discoveries;
4. shared boss/mega-rescue event;
5. optional contested rare-rescue mechanic where players race to claim a public spawn;
6. trading only after duplication/exploit risks and moderation needs are solved.

A contested rescue can reproduce the tension of stealing games without cloning their exact premise: a rare snack appears publicly, multiple players race to secure it, the carrier is visible and vulnerable to hazards, and the reward is only banked after reaching camp.

## Monetization design — build first, activate only after testing
Do not turn purchases live until the free loop, persistence and analytics are verified.

Candidate catalog:
- cosmetic camp themes;
- creature aura/trail cosmetic packs;
- extra display slots that do not block free progression;
- permanent convenience multiplier such as +50% Fizz or faster hatch/evolution timer only after economy tests;
- optional event cosmetic bundle;
- private-server/social options where appropriate;
- paid acceleration only where a complete free route exists.

Avoid selling the actual rarest creatures directly as the primary loop. The chase is the product.

## Discovery/thumbnail implications
The game thumbnail and title should show the **single highest-emotion action**, not a generic map shot. Examples of concepts to test:
- player sprinting with a glowing ultra-rare snack while disaster debris closes in;
- giant mutated snack in the distance with a clear rarity label;
- camp filled with progressively rarer creatures vs an empty beginner camp.

Every thumbnail must be original. We can match the readability and emotional structure of winning Roblox thumbnails without reproducing their characters/composition one-for-one.

## Analytics gates for v0.3
Instrument at minimum:
- first-rescue completion;
- time to first deposit;
- first upgrade;
- first zone unlock;
- first duplicate action;
- first mutation discovery;
- first event participation;
- round/session completion;
- D1 return when available;
- purchase funnel only after products are active.

Primary optimization sequence:
1. first 5-minute completion;
2. session length;
3. return rate;
4. social/event participation;
5. monetization conversion.

Do not optimize Robux extraction ahead of retention. Top earning only matters if people keep choosing to play.

## Immediate implementation order when the Mac reconnects
1. Finish production leave/rejoin persistence test already in progress.
2. Preserve current verified v0.2.1 build as rollback target.
3. Branch v0.3.
4. Build personal Rescue Camps + visible creature display slots.
5. Convert rescued creatures into passive Fizz producers.
6. Add collection index milestone rewards.
7. Add rarity/mutation/size presentation.
8. Add gated disaster biomes and movement/carry progression.
9. Add server event timer + one contested rare-rescue event.
10. Run Studio smoke, production private client, two-client and mobile tests before publishing any wider release.

## Sources used for this blueprint
- Roblox Charts, live US Computer rankings, 2026-10-13: https://www.roblox.com/charts
- Roblox Developer Forum, discovery measurement change, 2026-10-12: https://devforum.roblox.com/t/improved-discovery-measurement-in-creator-analytics/4930122
- Steal An Egg official Roblox experience description: https://www.roblox.com/games/107778070777162/Steal-An-Egg
- Current community gameplay/shop documentation was used only to cross-check mechanics; live Roblox product prompts remain authoritative for prices.
