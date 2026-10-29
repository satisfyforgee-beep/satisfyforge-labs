# TheDevKing — Roblox scripting research and application

Source channel: https://www.youtube.com/c/TheDevKing

**Coverage statement (2026-10-17):** I located the two original tutorial playlists and independently verified descriptions and public discussion of several lessons. I have **not watched every video** or accessed full transcripts for the whole channel. The older 2018–2019 lessons are learning references, not substitutes for current Roblox documentation.

## Playlists

- [Beginner's Roblox Scripting Tutorials (Beginner to Pro 2018)](https://www.youtube.com/playlist?list=PLhieaQmOk7nIfMZ1UmvKGPrwuwQVwAvFa) — fundamentals, functions, objects, events, script placement and basic UI.
- [Advanced Roblox Scripting Tutorials](https://www.youtube.com/playlist?list=PLhieaQmOk7nIoGnFoACf33M3o0BOqB38a) — tools, remotes, server/client security, CFrame, data stores, more complex mechanics.
- [Advanced #1 — Tools](https://www.youtube.com/watch?v=UoVYIZYKPOI) — video and description confirmed.
- [Advanced #13 — Data Store / Saving Player Data](https://www.youtube.com/watch?v=n1UpT2csAzo) — video and description confirmed.

## Cross-checks with current Roblox documentation

- [Roblox RemoteEvents](https://create.roblox.com/docs/scripting/events/remote): ReplicatedStorage remotes, server authorization, validation of client-supplied data. **Current implementation:** MutationRushAction and MutationRushEvent, server-side allowlisted travel and coin transactions, two-client automated test.
- [Roblox ModuleScripts](https://create.roblox.com/docs/scripting/module): break large scripts into reusable tested modules. **Current gap:** server game logic is monolithic; extract quest, rewards, race and mutation services after playtesting.
- [Roblox DataStores](https://create.roblox.com/docs/cloud-services/data-stores): server-only persistent profiles, separate test experience, robust error handling and safe testing. **Current gap:** coins, pets, wins and records are session-only. Implement before public release, test in an isolated published experience, never enable live production Studio API access.

## Prioritized actionable lessons for Hyper Mutation Rush

1. **Distinctive abilities, not just neon scenery:** visibly different mutations with timed effects, server validation and clear HUD feedback. Build and test incrementally.
2. **Strong replay loop:** timed race, personal-best record, rewards, progression, friends' times, clean reset.
3. **Proper architecture:** independent client UI, server authoritative rewards, remotes, small reusable modules.
4. **Saving progress:** versioned profile, safe load failures, save on exit/autosave, test in separate experience.
5. **Mobile first:** test responsive UI and controls on real Android devices, not just Studio.
6. **Visual feedback:** animations, particles, audio, differentiated environment geometry.
7. **Release quality:** small external playtest, retention measurement, original thumbnail, no guaranteed virality.

**Not claimed:** every channel video watched, paid tools purchased, game published, live DataStore verified, real players acquired.
