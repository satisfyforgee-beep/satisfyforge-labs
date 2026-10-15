# SatisfyForge n8n Operations

This folder contains a **draft, inactive, fail-closed** n8n workflow for SatisfyForge Operations.

## Safety properties
- Manual trigger only; no schedule/webhook activation.
- Account identity defaults to `UNVERIFIED_TEST_ONLY`.
- Deterministic `Dedup Key` is checked against the Airtable **Review Queue** before any write.
- Research uses a free public HTTP fetch only; no paid AI/API service is configured.
- Writes only to Airtable **Research Runs** and **Review Queue**.
- `Live Action Allowed` is hard-coded `false`.
- There are no publishing, outreach, purchase, financial, or workflow-activation nodes.
- Workflow export is `active: false`.

## Airtable targets
- Base: `SatisfyForge Operations` (`appCOTV6T99fj1s2z`)
- Review Queue: `tblwaK5xkOjIbaeN8`
- Research Runs: `tblMEiMbaEHYgTS4B`

## Credential handling
No Airtable credential ID/token is embedded in the JSON. After the intended SatisfyForge n8n account is verified, attach the existing Airtable credential to the three Airtable nodes.

## Safe validation sequence
1. Keep workflow inactive.
2. Verify SatisfyForge n8n workspace/account identity.
3. Attach Airtable credential.
4. Run once: expect one Research Runs record and one Review Queue record with `Needs Review`, `UNVERIFIED_TEST_ONLY`, and `Live Action Allowed = false`.
5. Run a second time with the same input: expect the duplicate path to stop before new writes.
6. Delete synthetic test records.
7. Leave workflow inactive until a separate explicit activation decision is made.
