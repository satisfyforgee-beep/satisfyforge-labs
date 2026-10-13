# Outreach Funnel Preflight

## Latest result — PASS

Checked 2026-10-13 before the Hunter sending window using the SatisfyForge-owned Playwright/Chromium GitHub Actions runner.

Pages checked:
- `/`
- `/lead-rescue.html`
- `/demo.html`

The `outreach-funnel-smoke` job completed successfully in GitHub Actions run `38364239306`.

A pass requires every page to:
- navigate without a 4xx/5xx response;
- remain on the expected SatisfyForge Wix host rather than an error/login redirect;
- have a non-empty title and at least 80 characters of visible body text; and
- avoid a visible generic 404 / page-not-found message.

Because the runner returns a non-zero exit when any page fails these rules, the successful workflow result verifies all three outreach-facing pages passed the preflight at that time.

## Ongoing rule

Run this read-only preflight again after material funnel/site changes or when outreach traffic reports a broken link. Do not create a second browser service for the same check.
