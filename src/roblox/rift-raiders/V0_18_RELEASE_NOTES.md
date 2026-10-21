# Rift Raiders v0.18 — Cafe Career & Safer Progress

**Status: private development build.** This release focuses on tactile activity and data safety instead of adding dozens more menu-only purchases.

## New real gameplay: The Bean & Brew

- A new physical **Downtown Interactive Coffee Bar** near the Modern Downtown barista workplace (near x=-36, z=2281), with wood counter, marble worktop, coffee machines, menu signage, cups, pastries, service register, an awning and lighting materials.
- Players can work a barista shift, and the server assigns one of **three randomized customer orders**: Espresso, Latte, or Mocha.
- At the matching coffee machine, the player must correctly brew that order; wrong recipe, fake recipe ID, premature service and too-distant requests are rejected server-side.
- After preparation, the customer register accepts the completed drink. Players receive a **12 earned-coin tip and 5 XP once**, then return to the existing barista career station for normal wage collection.
- The shift HUD displays the correct recipe and next step. Existing generic Task prompts do not bypass the new recipe workflow.
- No external model scripts, paid game passes or Robux purchases are needed.

## Data reliability improvement

- Introduced a dedicated **DataPersistence.lua** module for atomic profile acquisition with a 300-second renewable session lease and conservative rejection if the account is in use on another server.
- Uses Roblox UpdateAsync operations which confirm the current owner before writes; a stale server cannot overwrite coins and inventory after the profile is transferred to another server. Preserves the existing data store key (RiftRaidersProfiles_v1) and profile save schema **v10**, maintaining migrations from earlier builds.
- Saves are now serialized per player so overlapping old retries cannot overwrite newer in-memory changes; failed transient requests receive bounded exponential retry and jitter. All transforms are non-yielding.
- Periodic saves refresh the lease approximately every 84–96 seconds; session ownership is released on successfully committed departure. Shut-down waits for completion up to 25 seconds instead of sleeping an unconditional three seconds.
- Disconnect during atomic profile acquisition now releases the newly acquired lease without changing saved game progression.
- Studio tests are isolated from the owner's live data store, and a synthetic DataStore verifies first-server acquisition, second-server conflict, valid writes, unauthorized writes rejected, clean leave, rejoin recovery, orphan session release, stale lease takeover and future-schema safety.
- **Important caveat:** Production DataStore permissions, live server leave/rejoin, storage throttling under load, concurrent server migration, and failure recovery still require private-place live QA. The simulated test cannot prove a production save will never fail.

## Verification and limitations

- Roblox Studio automated smoke test verifies 3 coffee machines, customer register, order selection and synthetic persistence rules, alongside the complete existing map.
- Two-client Studio test exercises actual barista recipe/wage/tip behavior and previous multiplayer regressions (owned cars, boats, garden plot isolation, shopping, daily progress, private homes).
- Another noncompliant Roblox-hosted texture warning was observed during testing and is **not yet fully traced**. Most original template scenery remains suitable, but some imported material assets can be blocked by Roblox account/asset permissions.
- Still **not** a finished GTA/Sims-level release. Professional meshes for many vehicles and furnishings, proper cafe staff and customer character animations, private-live saves, multiplayer roleplay QA, real-device performance and human first-10-minute tests are all outstanding.

## How to try the new activity

1. Open the v0.18 game file in Roblox Studio and press Play. Use **WORLD → MODERN DOWNTOWN** if necessary.
2. Apply for the **BARISTA** career at Downtown Employment Center.
3. Walk to the barista workplace and start your shift. Read the customer’s requested coffee in the LIFE job objective or on the notification.
4. Walk to **The Bean & Brew**, choose the matching named espresso machine (E interaction), and return to the Cafe Customer Service Register to serve.
5. Return to the downtown BARISTA worksite to collect wages.

Next priorities should include genuine visual asset upgrades, tactile mechanic/retail mini-games, a more useful map/wayfinding, accessible interiors, real save tests and mobile profiling. No public publishing or monetization occurred.
