# Skill Vault Status

Last verified: 2026-10-13

## Current build
- Canonical implementation: `products/skill-vault-kiosk/` on `main`.
- PR #31 merged as `85794671e248ee649f248dffc095cdf00c0de7ff`.
- Skill-based merchandise redemption prototype; it is not a paid random-chance gambling product.
- Real-money play remains hard-disabled with `paymentsEnabled: false`.
- Local Node verifier owns challenge timing, hit validation, score, demo ticket balance, inventory and redemption records.
- Owner dashboard is token-gated.
- Runtime audit events are append-only; runtime ledger/audit files are not committed.
- Payment provider adapter exists only as a disabled boundary and rejects real-money authorization until deliberately implemented after deployment gates are cleared.

## Verified tests
- JavaScript syntax checks passed for UI, server and disabled payment adapter.
- `server/test.js` passed (`SKILL_VAULT_SERVER_TESTS_PASS`).
- Owner dashboard without token returned 401; authorized smoke token worked.
- Paid-session start returned 409 while payments are disabled (`SKILL_VAULT_AUTH_PAYMENT_GATES_PASS`).
- End-to-end local gameplay smoke accepted 3 server-timed correct hits, awarded exactly 6 tickets, and left actual collected revenue at $0.
- Safari render smoke passed.

## Commercial model under development
- Example planning configuration is a hypothetical $2 play and 70/30 owner/venue top-line split.
- Modeled revenue is kept separate from actual collected revenue and must never be reported as real earnings.
- Physical merchandise examples are capped at $10 estimated wholesale value in the Ohio-shaped prototype.
- Cabinet/anti-cheat plan: `products/skill-vault-kiosk/CABINET_SPEC.md`.
- Compliance/payment/operations checklist: `products/skill-vault-kiosk/PRODUCTION_GATES.md`.
- Placement economics: `products/skill-vault-kiosk/VENUE_MODEL.md`.

## Deployment boundary
Do not connect a real payment terminal, enable paid sessions, or award real prizes until the exact machine/software build, venue, operator structure, displayed rules and prize inventory complete any applicable Ohio licensing/approval requirements and the approved payment-provider integration is independently tested.

## Next safe engineering work
1. Hardware input verifier support for real illuminated/touch controls.
2. Remote machine health/status reporting.
3. Kiosk deployment packaging/watchdog with paid mode still disabled.
4. Stronger operator authentication and reconciliation/export tools.
5. Pilot venue package and contract template only after regulatory classification is resolved.
