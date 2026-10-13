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
- Signed physical-input verification now supports HMAC-authenticated, timestamped, nonce-protected button events; it stays disabled unless a local hardware secret is configured.
- Health/watchdog probe, reconciliation CSV export, operator redemption completion, and release-hash manifest generation are implemented.
- Payment provider adapter exists only as a disabled boundary and rejects real-money authorization until deliberately implemented after deployment gates are cleared.

## Verified tests
- JavaScript syntax checks passed for UI, server and disabled payment adapter.
- `server/test.js` passed (`SKILL_VAULT_SERVER_TESTS_PASS` + `SKILL_VAULT_SECURITY_ACCOUNTING_TESTS_PASS`).
- `server/integration-smoke.js` passed (`SKILL_VAULT_INTEGRATION_SMOKE_PASS`), including owner auth, paid-mode rejection, signed hardware input, replay rejection and reconciliation export.
- `server/watchdog.js` passed against a real local server (`SKILL_VAULT_HEALTH_OK`).
- Release manifest generation passed with SHA-256 hashes and confirmed `paymentsEnabled:false`.
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
- Operator procedure: `products/skill-vault-kiosk/OPERATOR_RUNBOOK.md`.
- Honest venue-pilot scope: `products/skill-vault-kiosk/PILOT_VENUE_PACK.md`.

## Deployment boundary
Do not connect a real payment terminal, enable paid sessions, or award real prizes until the exact machine/software build, venue, operator structure, displayed rules and prize inventory complete any applicable Ohio licensing/approval requirements and the approved payment-provider integration is independently tested.

## Next safe engineering work
1. Connect an actual low-cost physical button/controller prototype to the signed hardware-input boundary.
2. Package the verifier/watchdog for automatic local startup and crash recovery with paid mode still disabled.
3. Add machine identity, encrypted local secret storage and remote read-only health reporting.
4. Draft a venue contract only after the exact Ohio machine/operator/location classification is resolved.
5. Run a free/demo cabinet pilot before any live-money or real-prize operation.
