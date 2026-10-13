# SatisfyForge Mail Bridge

Owned zero-cost Gmail sending core for the SatisfyForge Control Center.

## Purpose

Replace paid multi-account mail tools for the specific SatisfyForge business-mail workflow. The Control Center will use Floot's built-in Google integration for owner authorization and this code's Gmail API message rules for sending.

## Hard safety rules

- Allowed sender: `satisfyforgee@gmail.com` only.
- `cougarboy1999@gmail.com` and every other account are rejected for business sending.
- OAuth access tokens are supplied only at runtime by Floot's Google integration. They are never committed to GitHub or manually stored in the database.
- Message headers are sanitized against newline/header injection.
- Queue items must have an idempotency key and a terminal `sent` state before production wiring is considered complete.
- A sent queue item must never be automatically resent.
- No tracking pixels, link wrapping, purchased sending service, or paid mail subscription is required.

## Files

- `src/gmail.mjs` — MIME builder, sender lock, base64url encoder, Gmail API send call, stable idempotency key.
- `test/gmail.test.mjs` — local/CI verification with a mocked Gmail endpoint; no real email is sent by tests.

## Floot deployment target

Project: SatisfyForge Control Center

The Floot app already has:
- owner auth
- a Floot-managed database
- Floot Google integration provisioned
- `mail_connections` database state
- `mail_queue` with the prepared SBDC and ECDI advisor messages

After Floot's free daily build-action allowance resets, finish these application-layer pieces:

1. Add a Business Gmail card to the authenticated admin dashboard.
2. Use Floot's Google integration connect button to authorize Google.
3. On successful connection, resolve the connected Google account email and store only safe connection metadata (email/scopes/status), never tokens.
4. Mark the connection `send_approved` only when the account is exactly `satisfyforgee@gmail.com`.
5. Add an admin-only send-pending endpoint. At request time it obtains a short-lived Google access token from Floot, applies the sender lock from this package, loads one queued message, calculates/checks its idempotency key, calls Gmail `users/me/messages/send`, and atomically records the Gmail message/thread IDs plus `sent_at`.
6. If a queue row is already `sent`, return the existing result instead of sending again.
7. Show queued/sent/failed state on the Control Center.
8. Typecheck, publish and verify owner auth before any real send.

## Prepared advisor messages

Two legitimate one-recipient cleaning-business advisor requests are staged in the Control Center database:
- SBDC advisor request to `SBDC@miamioh.edu`
- ECDI advisor request to `clentz@ecdi.org`

They are not to be sent from a personal Gmail account. Until the owned bridge is live, Hunter contains matching one-recipient drafts as a fallback but they remain stopped.

## Test

```bash
cd mail-bridge
npm test
```

CI workflow: `.github/workflows/mail-bridge-test.yml`.

No real Gmail credentials or messages are used by the test suite.
