# SatisfyForge Mail Bridge

## Goal

Own the business-mail workflow instead of paying for a $40/month multi-mail client.

Approved business sender: `satisfyforgee@gmail.com`

Hard rules:
- Spend $0.
- Never store a Gmail password in ChatGPT, GitHub, or app source.
- Never store Google refresh tokens manually.
- Only Google/Floot brokered OAuth may authorize Gmail.
- Sender lock: outbound business mail must refuse to send unless the connected Google account is exactly `satisfyforgee@gmail.com`.
- Do not silently fall back to `cougarboy1999@gmail.com`.
- Duplicate protection: queue rows already marked `sent` must never be resent by a connection callback or repeated request.

## Current state — 2026-10-14

The owned Gmail Mail Bridge is implemented and published in the SatisfyForge Control Center Floot project (`5bbe7cf5-3bb1-4a38-9af4-baf977118763`) at `https://satisfyforge-control.floot.app`.

Verified implementation:
- Floot's brokered Google OAuth is admin-only.
- The callback records only connection metadata in `mail_connections`; credentials and refresh tokens are not stored in project source or tables.
- Only the normalized address `satisfyforgee@gmail.com` receives `is_approved_sender=true`.
- Wrong-account connections return an explicit refusal and cannot send.
- The admin-only `mail-send-pending` endpoint selects only `queued` rows, claims them atomically as `sending`, and never selects `sent` rows.
- Before every Gmail API request the endpoint calls `getGoogleAccessToken(db, 'satisfyforgee@gmail.com')`.
- Messages are sent through the Gmail API as RFC822/base64url payloads.
- Successful rows record the Gmail message ID and sent timestamp; failures store only a sanitized error.
- The Control Center now shows business-Gmail connection state, queue counts, the connect control, and a guarded send-queued action.
- Floot typecheck is clean, the existing test suite passes, and unauthenticated production requests to Control Center status, Google authorization, and send-pending endpoints all return `401`.
- The Control Center remains on the free Floot plan; no paid build actions or mail service were purchased.

Current database state after deployment:
- No Google account is connected in `mail_connections`.
- `sbdc-cleaning-startup` remains `queued` with no Gmail message ID or sent timestamp.
- `ecdi-cleaning-startup` remains `queued` with no Gmail message ID or sent timestamp.
- No advisor email was sent during deployment or verification.

Remaining owner-only step:
1. Sign in to the Control Center as the owner/admin.
2. Use the Business Gmail card to connect exactly `satisfyforgee@gmail.com` through Google's OAuth screen.
3. After the card shows the approved sender, review the queue count and use **Send queued** once.

Do not connect or use `cougarboy1999@gmail.com`. Do not send through the ChatGPT Gmail connector while it resolves to that personal account.

## Temporary zero-cost outbound path

Hunter already has `satisfyforgee@gmail.com` connected and active as email account ID `182135` with a 15/day limit.

Two one-recipient draft sequences were staged on 2026-10-13 so the advisor requests can be sent from the correct business identity without Superhuman:
- `904857` — SBDC Cleaning Business Advisor Request → `SBDC@miamioh.edu`
- `904858` — ECDI Cleaning Business Advisor Request → `clentz@ecdi.org`

Both drafts:
- use sender account `182135` (`satisfyforgee@gmail.com`)
- have one introduction step and no follow-ups
- have open tracking off
- have link tracking off
- have no unsubscribe footer because they are individual requested-advice emails, not a marketing campaign
- contain no Cash App, Chime, or personal Gmail references
- are staged only; starting a Hunter sequence sends real mail and must follow Hunter's explicit send-confirmation contract.

Once the owned Gmail bridge is live, prefer it for one-to-one business correspondence. Keep Hunter for legitimate prospecting sequences and reply monitoring rather than using it as a permanent general mail client.
