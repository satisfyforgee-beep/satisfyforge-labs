# SatisfyForge Skill Vault Kiosk

A local-first prototype for a **skill-based merchandise redemption kiosk**. It is intentionally not a gambling machine.

## Revenue model

- Venue chooses a price per play.
- Every completed play receives a guaranteed base ticket award.
- Bonus tickets are determined by the player's measured reaction performance, not chance.
- Tickets can be exchanged for non-cash merchandise, venue credit, or other permitted rewards.
- The owner dashboard models gross margin from play price minus expected prize cost and operating/payment cost.

This can be run full-screen on a low-cost touch PC/tablet attached to a cabinet. A production unit can later add a payment terminal, secure server-side ledger, QR/player accounts, inventory, prize dispensing, fraud controls, and venue revenue-share reporting.

## Non-negotiable production guardrails

1. No cash or cryptocurrency wagering/payouts.
2. No paid random chance, spinning odds, hidden outcome manipulation, or house-controlled win probability.
3. Skill must materially determine bonus rewards.
4. Prize inventory, redemption values, age/access rules, taxes, and amusement-device licensing must comply with the deployment jurisdiction and venue rules.
5. Payment authorization, score verification, ticket balances, prize redemption, and owner controls must move server-side before accepting real money.
6. Do not deploy to minors or regulated venues without counsel reviewing the exact implementation.

## Run

Open `index.html` directly, or serve this directory with any static server.

Example:

```bash
python3 -m http.server 8080 --directory products/skill-vault-kiosk
```

Then open `http://localhost:8080`.

## Current status

Prototype only. It does not process payments or award real prizes.
