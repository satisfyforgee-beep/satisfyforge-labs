# Skill Vault production gates

The prototype may be developed and demonstrated for free without crossing into live-money operation. These gates must stay separate.

## Gate A — game integrity
- Score is determined by player action, not a random payout table.
- Server/local verifier owns target timing and score validation.
- Zero score produces zero tickets.
- Same score and configuration always produce the same ticket award.
- No adaptive payout percentage, prior-win/loss logic, or operator button that changes a player's outcome.

## Gate B — prize catalog
- Physical merchandise only for the Ohio-shaped prototype.
- No cash, cryptocurrency, gift cards/cash equivalents, alcohol, tobacco, firearms, lottery tickets, bingo, or games-of-chance rewards.
- Each deployment validates current prize-value limits and documents wholesale value.
- Inventory and redemption are server-side and auditable.

## Gate C — regulatory review
- Re-check current Ohio Revised Code and Ohio Casino Control Commission rules before deployment.
- Determine machine type and whether operator/location licensing applies.
- Obtain machine/software approval when required.
- Freeze the exact approved software/configuration and keep release hashes.
- Display required rules, price, score-to-ticket formula and prize information at the machine.

## Gate D — payment
- `paymentsEnabled` remains false until Gates A–C are signed off.
- Use an approved payment provider; never store raw card data.
- Paid session creation requires a valid provider authorization ID and idempotency key.
- Refund/cancel behavior must be defined for aborted or malfunctioning rounds.
- Actual collected revenue and modeled revenue must remain separate fields.

## Gate E — operations
- Authenticated owner/operator accounts.
- Locked kiosk OS/browser account and service access.
- Append-only audit logs for session start, score, ticket award, redemption, operator action and payment reference.
- Daily reconciliation of provider totals, machine ledger and prize inventory.
- Incident process for device tampering, network loss, power loss and dispute review.

## Gate F — venue economics
- Written venue agreement defines revenue share, prize stocking, tax responsibility, maintenance, damage, uptime and removal rights.
- Pilot economics are measured from real approved operation; do not treat demo plays as collected revenue.
- Expand only after the pilot demonstrates positive unit economics and compliance stability.
