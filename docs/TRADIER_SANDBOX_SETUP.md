# Tradier paper-trading API: safe connection check

Status: prepared, **not connected**. Requires the owner to supply a sandbox token **outside source control**.

This GitHub repository is **public**. Never put API tokens, account IDs, financial details or personal data in code, commits, PRs, issues, screenshots or CI logs. Never use a **production/live** token for this script.

Tradier docs: https://docs.tradier.com/docs/endpoints. Sandbox base URL is `https://sandbox.tradier.com/v1/`. Market data is delayed about 15 minutes; **not suitable for live orders**.

## Local smoke test

1. Retrieve your **Sandbox** token from https://web.tradier.com/user/api (not the live token).
2. Store it securely as local environment variable `TRADIER_SANDBOX_TOKEN`; don't paste it into ChatGPT or commit a tracked `.env`.
3. Run: `python3 scripts/tradier_sandbox_check.py --symbol SPY`.
4. Success prints `Tradier SANDBOX authentication: OK`, the paper-account count and optional **delayed** price. No personal identifiers are printed.
5. Run offline tests: `python3 -m unittest discover -s tests -p 'test_tradier_sandbox_check.py'`.

The script hardcodes the sandbox hostname and GET-only allowlisted paths (`/user/profile`, `/markets/quotes`). It **cannot** place paper or live orders; it never connects to a production API. No background scheduler, secret or GitHub workflow has been created.

For later GitHub Actions testing, store the key only in a repository **Actions secret** under Settings > Secrets and variables > Actions. Do **not** insert it in workflow YAML or logs. Because the repo is public, do not expose secrets to untrusted pull request workflows.

This smoke test is entirely separate from any live brokerage account, cash-conversion request or options approvals. Do not describe the API as connected until an authenticated sandbox request actually succeeds.
