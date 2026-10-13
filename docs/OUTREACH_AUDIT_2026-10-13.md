# Outreach audit — 2026-10-13

Verified at approximately 12:24 UTC (08:24 America/New_York).

## Hunter sending diagnosis

The three canonical sequences are started, active, not paused, and use Hunter email account 182135 (`satisfyforgee@gmail.com`).

| Sequence | Offer | Recipients | Recipient state | Sent |
|---|---|---:|---|---:|
| 904604 | Home Service Lead Rescue | 9 | 9 pending | 0 |
| 904608 | Lead Follow-Up Automation | 3 | 3 pending | 0 |
| 904610 | Gym Membership Growth | 3 | 3 pending | 0 |

There is no recorded bounce, cancellation, unsubscribe, or per-recipient error.

The zero-send count was expected at the audit time because the sequence start date is 2026-10-13 and the effective scheduling overlap had not opened:

- Sequence window: 14:00–21:00 on weekdays.
- Sender account window: 09:00–16:59 UTC on weekdays.
- Effective overlap: 14:00–16:59 UTC (10:00–12:59 America/New_York on 2026-10-13).
- Sender status: active.
- Sender daily limit: 15, exactly matching the 15 pending recipients across the three sequences.

No restart, duplicate sequence, recipient addition, or schedule mutation was made. Recheck after the effective window. If the counts remain zero after 16:59 UTC, inspect platform send logs/account health before changing anything.

## Gmail and lead safety

The Gmail connector available to this command-center run is authenticated as `cougarboy1999@gmail.com`, not the approved SatisfyForge sender. No business email was sent from that account. Inbox search was also temporarily rejected by Gmail with `RATE_LIMIT_EXCEEDED`, so no new inquiry or reply is claimed from this pass.

Continue using Hunter account 182135 for the active prospecting sequences. The owned Mail Bridge must fail closed unless the connected Google account is exactly `satisfyforgee@gmail.com`.

## Commerce boundary

No payment link was sent. Tool Vault checkout remains quarantined until independent checkout and fulfillment verification. The Creator Kit public page may be described only as publicly verified at $7.99; payment and delivery remain untested.


## 12:17 ET follow-up

- Hunter email account 182135 is now active on `Eastern Time (US & Canada)`, weekdays 09:00–16:59, with a 15-message daily limit.
- All three sequences remain active and all 15 recipients remain `pending`; sent, delivered, bounced and replied counts remain zero.
- The sequences themselves still have a 14:00–21:00 window. Because the account timezone is now Eastern, their first eligible local time is 14:00 ET.
- A safe API attempt to align only the three sequence windows with the sender window was rejected with `sequence_locked`: Hunter does not allow schedule-window edits after a sequence has started.
- No pause, restart, duplicate campaign or recipient mutation was performed. The next verification point is after 14:00 ET.
- The connected Gmail connector remains `cougarboy1999@gmail.com`. A focused inbox check found no qualified SatisfyForge inquiry; the only match was an unrelated Temu promotion. No email was sent from the personal account.
- The Dancing Plague Instagram retry through Buffer is verified `sent` at 10:07 ET: https://www.instagram.com/reel/Deb_AXaAGto/
