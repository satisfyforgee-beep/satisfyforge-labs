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

## Current state — 2026-10-13

The existing SatisfyForge Control Center Floot project (`5bbe7cf5-3bb1-4a38-9af4-baf977118763`) has the free `google-integration` resource provisioned. Floot supplies the Google OAuth broker, so no Google Cloud client ID/secret and no paid mail app are required.

Seeded Floot integration files now exist:
- `components/ConnectGoogleButton.tsx`
- `endpoints/auth/google_integrations_authorize_GET.ts`
- `endpoints/auth/google_integrations_callback_GET.ts`

A fresh connector check on 2026-10-13 at 08:26 UTC confirmed the free Floot build cap is still active and resets at `2026-10-14T06:00:00Z` (02:00 America/New_York). The Control Center remains published at `https://satisfyforge-control.floot.app` on the free plan. No paid upgrade or extra action was purchased.

The currently connected ChatGPT Gmail connector identifies as `cougarboy1999@gmail.com`, not the approved business sender. Do not use that connector to send the two queued business advisor messages. The owned bridge must keep the sender lock and refuse any account other than `satisfyforgee@gmail.com`.

The Control Center database now also contains:
- `mail_connections`
- `mail_queue`
- enum `mail_queue_state` (`queued`, `sending`, `sent`, `failed`)

Two clean advisor emails are already queued in that database:
- `sbdc-cleaning-startup` → `SBDC@miamioh.edu`
- `ecdi-cleaning-startup` → `clentz@ecdi.org`

The rewritten messages intentionally remove the old personal Gmail signature and the old Cash App/Chime payment usernames.

## Floot build-cap boundary

The final code patch could not be applied on 2026-10-13 because the free Floot workspace reached its 100 build-actions/day limit. The limit resets at `2026-10-14T06:00:00Z` (02:00 America/New_York on that date). Do not upgrade or buy extra build actions.

After the reset, finish these exact zero-cost steps:

1. Update `ConnectGoogleButton` to support `onConnected` / `onError` callbacks.
2. In `google_integrations_callback_GET`, after `finalizeGoogleConnection`, upsert the connected address into `mail_connections` and set `is_approved_sender=true` only when the normalized address equals `satisfyforgee@gmail.com`.
3. Add an admin-only `mail-send-pending` endpoint.
4. In that endpoint call `getGoogleAccessToken(db, 'satisfyforgee@gmail.com')` before every Gmail API request.
5. Send with Gmail API `POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send` using an RFC822 message encoded as base64url.
6. Select only `mail_queue.state='queued'`; mark each row `sending`, then `sent` with Gmail message ID and timestamp, or `failed` with a sanitized error.
7. Never resend `sent` rows.
8. Extend Control Center status/UI with a Business Gmail card, connection status, queue status, and a `Connect business Gmail` button using Floot `feature='gmail'`.
9. When the correct business Google account connects, send only the pre-approved queued advisor messages; if another Google account is connected, refuse to send and display the wrong-account warning.
10. Typecheck, publish `satisfyforge-control.floot.app`, and verify the app still requires owner authentication.

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
