# SatisfyForge Skill Vault Kiosk

A local-first **skill-based merchandise redemption kiosk** prototype. It is intentionally designed to avoid paid random-chance mechanics.

## What is working now
- Touch-friendly 4x4 reaction game.
- Local verification server generates the challenge schedule and validates hits against server time.
- Score deterministically controls ticket awards; zero score = zero tickets.
- Server-side demo ticket balance, inventory-aware redemption records, and owner/venue modeled revenue split.
- Real payments are hard-disabled in `server/config.json`.
- Browser falls back to an unverified static demo if the verifier is unavailable.
- Physical prize examples are kept at $10 or less estimated wholesale value in this Ohio-shaped prototype.

## Run the verified demo

```bash
cd products/skill-vault-kiosk
node server/server.js
```

Open `http://localhost:8080`.

Run checks:

```bash
node --check app.js
node --check server/server.js
node server/test.js
```

## Revenue model
- Venue chooses a play price only after regulatory/payment gates are cleared.
- Player skill creates the score; score creates tickets.
- Tickets redeem for permitted physical merchandise.
- The ledger separates **actual collected revenue** from **modeled revenue** so demo activity can never be reported as money earned.
- `ownerSharePct` and `venueSharePct` in server configuration model a placement/revenue-share business.

## Ohio deployment notes
The user is building in Ohio, so this prototype is shaped around current Ohio skill-based amusement-machine concepts. Before accepting real money, re-check the current rules and obtain any required approvals/licenses.

Official sources:
- Ohio Revised Code 2915.01: https://codes.ohio.gov/ohio-revised-code/section-2915.01
- Ohio Administrative Code Chapter 3772-50: https://codes.ohio.gov/ohio-administrative-code/chapter-3772-50
- Ohio Administrative Code Rule 3772-50-24: https://codes.ohio.gov/ohio-administrative-code/rule-3772-50-24

Design implications reflected here:
1. No cash payouts or cash-equivalent/gift-card rewards.
2. No alcohol, tobacco, firearms, lottery tickets, bingo, or games-of-chance rewards.
3. Ticket awards are based solely on player score; no hidden payout percentage or prior-win/prior-loss adjustment.
4. Random target placement changes the visible challenge, not the payout odds.
5. Prototype merchandise examples are at or below $10 estimated wholesale value.
6. Production rules, price, prizes and scoring must be clearly displayed.
7. Type-B/type-C machines/operators can require Ohio Casino Control Commission licensing/approval; this prototype is not an approved machine.
8. Production prize/voucher handling must match the applicable on-site rules.

This is a product-engineering checklist, not legal advice.

## Files
- `index.html`, `styles.css`, `app.js` — kiosk UI.
- `server/server.js` — local verifier, ledger and static server.
- `server/config.json` — non-secret prototype configuration; payments default OFF.
- `server/test.js` — integrity/guardrail tests.
- `CABINET_SPEC.md` — hardware and anti-cheat roadmap.
- `PRODUCTION_GATES.md` — compliance, payment and operating gates.
- `VENUE_MODEL.md` — hypothetical placement/revenue-share economics and scale checkpoints.

## Non-negotiable production guardrails
1. No cash or cryptocurrency wagering/payouts.
2. No paid random chance, spinning odds, hidden outcome manipulation, or house-controlled win probability.
3. Skill/score determines the reward.
4. Payment authorization, score verification, ticket balances, prize inventory, redemption and owner controls are server-side.
5. No real-money operation until the exact machine/software/venue/operator setup is reviewed and approved as required.

## Current status
Prototype/demo only. It processes **no real payments**, issues no real vouchers, and awards no real prizes.
