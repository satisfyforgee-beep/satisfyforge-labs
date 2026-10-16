# SatisfyForge Cloud Browser

A zero-cost cloud browser runner owned by SatisfyForge. It uses Playwright + Chromium on GitHub Actions so browser tasks do not depend on TinyFish, Replit, or the owner's physical computer.

## What it does

- Runs Chromium in a GitHub-hosted Linux runner.
- Supports named, reviewed browser tasks in `src/tasks.mjs`.
- Uses `job.json` as the non-secret task queue entry.
- Separates read-only tasks from mutation tasks with per-job `allowMutations` plus repository-level `SF_BROWSER_MUTATIONS_ARMED`.
- Supports authenticated sessions through an encrypted GitHub Actions secret named `SF_BROWSER_STATE_GZIP_B64`.
- Never stores passwords, cookies, access tokens, or browser storage state in this public repository.
- Prints only task-approved, sanitized result fields to workflow logs.

## Current tasks

- `smoke` — verifies the cloud browser itself works against a public page.
- `payhip-audit-tool-vault` — reads the Tool Vault product state after an authenticated session is installed.
- `payhip-fix-tool-vault-49` — sets the Tool Vault price to 49 only when authentication is present, the job allows mutations, and the repository mutation arm has been enabled after account verification.

## How ChatGPT triggers work

ChatGPT can update `browser-runner/job.json`. That commit triggers `.github/workflows/satisfyforge-cloud-browser.yml`. The workflow reads the job, runs Chromium, and writes a sanitized JSON result to the Actions log. ChatGPT can then inspect the workflow run and continue iterating.

Example queue entry:

```json
{
  "task": "payhip-audit-tool-vault",
  "allowMutations": false
}
```

## Authentication design

Authenticated browser state is intentionally not committed to GitHub. The runner reads a gzip-compressed Playwright storage-state JSON document from the encrypted repository secret `SF_BROWSER_STATE_GZIP_B64` and deletes the temporary decoded file after the run.

This is the only secure persistence layer still needed for account-only browser tasks. Public/unauthed tasks work without it.

## Safety boundaries

- No CAPTCHA bypassing.
- No MFA bypassing.
- No password collection in job files or logs.
- No secret state in commits, caches, screenshots, artifacts, or public logs.
- Mutating tasks require authenticated state, `allowMutations: true`, and repository variable `SF_BROWSER_MUTATIONS_ARMED=true`. Leave that variable unset/false until target account identity is verified.
- Each site-specific mutation is implemented as a reviewed named task rather than arbitrary remote JavaScript.

Run `python3 browser-runner/validate_safety.py` before changing browser-worker wiring; GitHub CI enforces the same contract.

## Cost model

The repository is public. Standard GitHub-hosted Actions runners are free for public repositories under GitHub's current Actions billing rules. The workflow uses only standard `ubuntu-latest` runners and does not enable paid larger runners.
