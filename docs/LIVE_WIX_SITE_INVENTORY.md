# Live Wix Site Inventory

Last checked: 2026-10-12

Canonical live site: `https://headless-hjorlnsaplw-satisfyforgee-140d.wix-site-host.com`
Wix metaSiteId: `b237555c-446a-4958-a2df-6c7b186e7d80`

## Important deployment rule

The live Wix Headless deployment currently contains more files than the historical `satisfyforge-site/` GitHub folder. A Wix Headless drop replaces the entire served file set. Therefore, **never build a full Wix replacement upload only from `satisfyforge-site/` unless the complete production file set has first been synchronized.**

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

## Current monetization path

The homepage and pricing page now include direct links to the live SatisfyForge Tool Vault at `https://payhip.com/b/KLjBb`, priced at $49 one-time Founding Lifetime Access. Preserve the existing Lead Rescue and Wix Forms funnels alongside that paid digital offer.
