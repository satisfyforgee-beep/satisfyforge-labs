# SatisfyForge Skill Vault Kiosk

A local-first prototype for a **skill-based merchandise redemption kiosk**. It is intentionally designed to avoid paid random-chance mechanics.

## Revenue model

- Venue chooses a price per play.
- A player's visible reaction score deterministically sets the ticket award.
- A zero score earns zero tickets; there is no guaranteed voucher unrelated to score.
- Tickets can be exchanged only for permitted merchandise prizes in a production deployment.
- The owner dashboard models gross margin from play price minus modeled merchandise cost and operating/payment cost.

This can be run full-screen on a low-cost touch PC/tablet attached to a cabinet. A production unit can later add a payment terminal, secure server-side ledger, on-site ticket/voucher dispensing, inventory, prize dispensing, fraud controls, and venue revenue-share reporting.

## Ohio deployment notes

The user is building in Ohio, so the prototype is intentionally shaped around the current Ohio skill-based amusement-machine definition. Before accepting real money, re-check the current rules and obtain any required approvals/licenses.

Official sources:

- Ohio Revised Code 2915.01: https://codes.ohio.gov/ohio-revised-code/section-2915.01
- Ohio Administrative Code Chapter 3772-50: https://codes.ohio.gov/ohio-administrative-code/chapter-3772-50
- Ohio Administrative Code Rule 3772-50-24: https://codes.ohio.gov/ohio-administrative-code/rule-3772-50-24

Design implications reflected here:

1. No cash payouts and no cash-equivalent/gift-card rewards.
2. No alcohol, tobacco, firearms, lottery tickets, bingo, or games-of-chance rewards.
3. Ticket/voucher awards are based solely on the player's score; there is no hidden payout percentage or prior-win/prior-loss adjustment.
4. The random placement of a reaction target changes what the player must react to, but the player can see and act on the target; it does not independently choose a winning payout.
5. Every merchandise item shown in the prototype has an estimated wholesale value of $10 or less.
6. Production rules, price, prizes, and scoring must be clearly displayed.
7. Type-B/type-C machines and operators can require Ohio Casino Control Commission licensing/approval; this prototype itself is not an approved machine.
8. Production voucher/prize handling must occur on-site and match the applicable Ohio rules.

This is a product-engineering checklist, not legal advice. A real paid deployment should be reviewed against the exact hardware, prize inventory, venue, and business structure.

## Non-negotiable production guardrails

1. No cash or cryptocurrency wagering/payouts.
2. No paid random chance, spinning odds, hidden outcome manipulation, or house-controlled win probability.
3. Skill/score must determine the reward.
4. Prize inventory, redemption values, age/access rules, taxes, licensing, machine approval, and venue rules must comply with the deployment jurisdiction.
5. Payment authorization, score verification, ticket balances, prize redemption, and owner controls must move server-side before accepting real money.
6. Do not market this as gambling or deploy it as a gambling device.

## Run

Open `index.html` directly, or serve this directory with any static server.

Example:

```bash
python3 -m http.server 8080 --directory products/skill-vault-kiosk
```

Then open `http://localhost:8080`.

## Current status

Prototype only. It does not process payments, issue real vouchers, or award real prizes.
