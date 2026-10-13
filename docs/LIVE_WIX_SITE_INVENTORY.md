# Live Wix Site Inventory

Last checked: 2026-10-13

Canonical live site: `https://headless-hjorlnsaplw-satisfyforgee-140d.wix-site-host.com`
Wix metaSiteId: `b237555c-446a-4958-a2df-6c7b186e7d80`

## Important deployment rule

The live Wix Headless deployment contains more files than the historical `satisfyforge-site/` GitHub folder. A Wix Headless drop replaces the entire served file set. Therefore, **never build a full Wix replacement upload only from `satisfyforge-site/` unless the complete production file set has first been synchronized.**

For small live edits, download the existing Wix deployment, modify only the intended files in memory, preserve every other production entry, omit only `wix.config.json` from the replacement drop, and release the full preserved set back to the same metaSiteId.

## Current live file set

- `_wix/pages.json`
- `404.html`
- `appointments.html`
- `audit.html`
- `auto.html`
- `demo.html`
- `home-services.html`
- `index.html`
- `lead-rescue.html`
- `lead-tracker.html`
- `message-builder.html`
- `pricing.html`
- `privacy.html`
- `robots.txt`
- `roi-calculator.html`
- `satisfyforge-icon.png`
- `services.html`
- `sitemap.xml`
- `styles.css`
- `tools.html`
- `wix.config.json` (deployment metadata; do not include it in a replacement drop)

## Production characteristics that must be preserved

- SEO/canonical/Open Graph/Twitter metadata on live pages
- `satisfyforge-icon.png`
- Wix Forms links for lead/sample requests
- `privacy.html`
- `robots.txt` and `sitemap.xml`
- `demo.html` and `roi-calculator.html`
- Wix Headless site script/client ID already present in production HTML

## 2026-10-13 full production smoke test — PASS

The SatisfyForge-owned Playwright/Chromium runner checked all customer-facing HTML pages in the inventory:
`/`, `appointments.html`, `audit.html`, `auto.html`, `demo.html`, `home-services.html`, `lead-rescue.html`, `lead-tracker.html`, `message-builder.html`, `pricing.html`, `privacy.html`, `roi-calculator.html`, `services.html`, and `tools.html`.

Pass criteria required each page to load without a 4xx/5xx response, remain on the expected Wix host, contain a non-empty page title and meaningful visible text, and avoid a generic 404/page-not-found result. The same run also required **zero direct Payhip product links** on the homepage and pricing page while the checkout safety hold is active.

GitHub Actions run `38364908982` completed successfully, so all page checks and the payment-link safety checks passed at that time.

## Current monetization safe state

On 2026-10-12 a Payhip audit showed a mismatch: the Tool Vault was shown in Payhip at `$0.00` while the live Wix site advertised `$49 one time`.

To prevent an unintended free checkout, the production deployment was downloaded, all production files were preserved, and only `index.html` and `pricing.html` were changed. The direct Tool Vault Payhip links were replaced with the existing Wix request form and checkout was marked temporarily paused. The replacement drop preserved 20 served files (all production entries except `wix.config.json`) and completed successfully with Wix upload ID `77c3938a-df24-44d9-b869-3b807eb41068`.

Do not restore direct Tool Vault checkout links until the actual Payhip price and configuration are independently verified. Preserve the existing Lead Rescue, free-tool, and Wix Forms funnels while payment verification is pending.
