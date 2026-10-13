# Skill Vault cabinet specification (prototype)

## Goal
A durable touch-first amusement kiosk that runs the verified skill game locally, keeps gameplay responsive without internet dependency, and separates play hardware from payment/prize systems.

## Prototype hardware
- 15–24 inch capacitive touchscreen or protected monitor + touch overlay.
- Small fanless PC or compact desktop capable of Chromium/Safari-class browser rendering.
- Wired Ethernet preferred; Wi-Fi as backup.
- Lockable cabinet with service door, surge protection, ventilated electronics shelf, and physically separate prize storage.
- Optional illuminated physical reaction buttons can replace touch input later; each button should map to a unique input ID and be read by the local verifier rather than trusting browser DOM events.
- No bill acceptor, card terminal, prize dispenser, or cash handling is wired into this prototype.

## Production architecture
1. Kiosk UI displays the target and score.
2. Local verifier generates the challenge schedule and timestamps hits.
3. Server-side ledger owns sessions, score, tickets, inventory, redemptions and revenue-share records.
4. Payment adapter is a separate gate. A paid round cannot start until an approved provider returns a valid authorization.
5. Redemption creates an operator-verifiable record before any physical prize is released.
6. Owner functions require authenticated operator access and should not be reachable from the public game surface.

## Anti-cheat roadmap
- Current prototype: local server owns target schedule and validates hits against server time.
- Next hardware step: physical input controller sends signed/serialized button events directly to the verifier.
- Production: kiosk identity key, append-only event log, per-session nonce, monotonic clock checks, replay protection, watchdog restart, locked-down OS/browser account, and tamper-evident service access.
- Never use hidden payout percentages or alter difficulty/rewards based on prior wins/losses.

## Maintenance
- Daily: verify touchscreen/input, prize inventory, network, and clock.
- Weekly: export ledger backup and inspect error/tamper logs.
- Per software release: checksum approved build, regression-test scoring, and preserve the exact approved configuration.

## Commercial deployment gate
Do not connect a real payment terminal or award real prizes until the exact machine, software build, venue, operator structure, displayed rules and prize inventory have passed the applicable licensing/approval review.
