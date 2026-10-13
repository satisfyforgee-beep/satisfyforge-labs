# SatisfyForge Scalable Acquisition — zero-cost design (2026-10-13)

## Goal and reality
Scale beyond Hunter's current 15/day sender setting without pretending email delivery is unlimited. No sender has unlimited free, unrestricted deliverability. Never rotate identities/accounts to evade quotas, scrape private addresses, or send unsolicited mass blasts.

## Verified baseline
Hunter campaigns 904604, 904608, 904610: 15 sent, 14 delivered, 1 bounced (Snow Roofing Restoration), 0 replies at latest check. Business sender satisfyforgee@gmail.com, active. Existing hourly Outreach Watch owns monitoring; do not duplicate. Website intake, lead tracker, audit and service pages already live.

## Architecture
1. **Inbound first (unmetered visitors, not unlimited sends):** Publish useful original free audit/calculator/lead-rescue content and calls to action on the live Wix website and social accounts. All opt-in forms must clearly state how contact information will be used.
2. **One canonical lead ledger:** Track source, business, consent/legal basis, channel, offer, status, last contact, next follow-up, suppression/unsubscribe and outcome. De-duplicate by normalized address/domain; keep PII in a private authenticated datastore, NEVER public GitHub.
3. **Channel router:** For each prospect choose one appropriate channel: opt-in business email via authorized Gmail Mail Bridge; low-volume relevant B2B cold outreach via Hunter within provider caps; public original social content; referral/partner introductions; or inbound search. Do not automate platform DMs contrary to rules.
4. **Queue + rate limits:** Per-provider daily and rolling quotas, per-recipient frequency caps, exponential retry only for transient failures, idempotency keys, bounce and unsubscribe suppression, global kill switch. A queue can contain unlimited *records* in principle, but dispatch remains bounded by actual provider capacity and applicable laws.
5. **Compliant outreach:** Accurate sender identity, truthful subject and claims, clear opt-out, valid postal address where required, honor opt-outs promptly, applicable CAN-SPAM/platform requirements. Never buy lists or contact unverified prospects indiscriminately.
6. **Revenue loop:** Qualify interested responses, provide free audit, quote only services that can be fulfilled, verify Payhip payment/fulfillment before enabling quarantined Tool Vault checkout, and record actual collected revenue.

## Immediate execution
- Keep current Hunter campaigns active; do not restart or duplicate.
- Suppress bounced Snow Roofing Restoration address; verify any replacement before use.
- Use existing hourly Outreach Watch for replies and sends.
- When Floot build capacity returns, finish the already-tested business Gmail Mail Bridge with business-account OAuth, sender allowlist, idempotent outbound and private suppression ledger. This is NOT a loophole to Gmail's sending caps.
- Inspect Wix form intake and existing social publishing; improve the call-to-action and free-audit conversion path before generating more campaigns.
- Reassess volume only after delivery, bounce, reply and conversion measurements. Scale through opt-in audience and provider-approved capacity, not evasive workarounds.

## Acceptance checks
- Test an opted-in business-email send and inbound reply.
- Verify unsubscribe and bounced addresses are suppressed.
- Verify lead de-duplication and no double-send across Hunter/Mail Bridge.
- Verify one genuine inquiry reaches owner and gets an appropriate response.
- Verify paid checkout/fulfillment before advertising Tool Vault.
- Report actual sends, replies, leads, sales and cost, never queued volume as delivered.
