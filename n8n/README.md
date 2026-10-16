# SatisfyForge n8n Operations

This folder contains a **draft, inactive, fail-closed** n8n workflow for SatisfyForge Operations.

## Safety properties
- Manual trigger only; no schedule/webhook activation.
- Account identity defaults to `UNVERIFIED_TEST_ONLY`.
- Deterministic keys are checked against both Airtable **Review Queue** and **Research Runs** before any write.
- Research uses a free public HTTP fetch only; no paid AI/API service is configured.
- Research source URLs must be public HTTPS URLs; credential-bearing, local/private-network, and link-local targets are rejected before fetch.
- Writes only to Airtable **Review Queue** and **Research Runs**, in that order, so the human-review gate is durable first.
- `Live Action Allowed` is hard-coded `false`.
- There are no publishing, outreach, purchase, financial, or workflow-activation nodes.
- Workflow export is `active: false`.

## Airtable targets
- Base: `SatisfyForge Operations` (`appCOTV6T99fj1s2z`)
- Review Queue: `tblwaK5xkOjIbaeN8`
- Research Runs: `tblMEiMbaEHYgTS4B`

## Credential handling
No Airtable credential ID/token is embedded in the JSON. After the intended SatisfyForge n8n account is verified, attach the existing Airtable credential to the four Airtable nodes (two duplicate lookups and two guarded writes).

## Safe validation sequence
1. Keep workflow inactive.
2. Verify SatisfyForge n8n workspace/account identity.
3. Run `python3 n8n/validate_safe_research_workflow.py` and require `SAFE_N8N_WORKFLOW=PASS`.
4. Attach Airtable credential.
5. Run once: expect one Research Runs record and one Review Queue record with `Needs Review`, `UNVERIFIED_TEST_ONLY`, and `Live Action Allowed = false`.
6. Run a second time with the same input: expect the duplicate path to stop before new writes.
7. Delete synthetic test records.
8. Leave workflow inactive until a separate explicit activation decision is made.
