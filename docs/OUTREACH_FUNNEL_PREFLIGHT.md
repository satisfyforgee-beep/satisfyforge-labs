# Outreach Funnel Preflight

This record is updated by the Master Command Center when the public Wix funnel pages used by outreach are browser-checked.

Pages to verify before outreach:
- `/`
- `/lead-rescue.html`
- `/demo.html`

Pass criteria:
- HTTP navigation succeeds without a 4xx/5xx response.
- The final URL remains on the SatisfyForge Wix host rather than redirecting to an error/login page.
- The page has non-trivial visible text and a non-empty title.
- The page does not visibly contain a generic 404 / page-not-found message.

The cloud browser task `outreach-funnel-smoke` performs this read-only check and returns only sanitized page metadata.
