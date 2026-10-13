# Skill Vault operator runbook

## Before opening a demo/pilot cabinet
1. Confirm the exact approved software/configuration hash when approval applies.
2. Start the local verifier with owner credentials supplied through environment variables, never source code.
3. Run `node server/watchdog.js`; it must print `SKILL_VAULT_HEALTH_OK`.
4. Confirm `/api/health` reports `paymentsEnabled:false` unless the regulatory/payment gates have explicitly been cleared for that exact machine.
5. Test touch/physical controls, clock, prize inventory and the rules display.

## During operation
- Player-facing controls never receive the owner token.
- Physical input controllers use `SKILL_VAULT_INPUT_SECRET` and signed timestamped nonces; replayed/stale events are rejected.
- Operator completes a prize handoff only after matching the pending redemption record to the physical item.
- Never modify score, tickets or outcomes to compensate for a complaint. Follow the documented refund/incident procedure once a payment provider is live.

## Close/reconcile
- Export `/api/operator/reconciliation.csv` using authenticated operator access.
- Actual money is `actual_collected_cents` only. Modeled values are planning data, not revenue.
- Compare provider totals, ledger totals and prize counts once real approved payment operation exists.
- Preserve the append-only audit log and release manifest with the day’s operating records.
