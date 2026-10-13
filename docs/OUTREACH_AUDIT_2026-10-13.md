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


## 16:20 ET verification

### Hunter delivery

The original 15-recipient batch has now sent without a restart or recipient mutation.

| Sequence | Sent | Delivered | Bounced | Opened | Replied |
|---|---:|---:|---:|---:|---:|
| 904604 — Home Service Lead Rescue | 9 | 8 | 1 | 0 | 0 |
| 904608 — Lead Follow-Up Automation | 3 | 3 | 0 | 2 | 0 |
| 904610 — Gym Membership Growth | 3 | 3 | 0 | 0 | 0 |
| **Total** | **15** | **14** | **1** | **2** | **0** |

No sequence restart, duplicate campaign, recipient addition, or new send was performed. The next useful action is reply monitoring and lead qualification; zero replies were verified in this pass.

### Wix lead intake

A read-only query of the canonical Wix Forms namespace returned zero submissions. No qualified site inquiry or business reply was available to advance.

### Dancing Plague YouTube recovery

- Metricool item 393673008 reached a definite `ERROR` after its scheduled 16:00 ET time: `You have reached your Metricool account limit.`
- Buffer's YouTube channel `6accefb0778b240e2fe77d27` was connected, unlocked, and had no matching post in the intended time window.
- One automatic Buffer publish attempt was made using the existing finished media URL. Buffer rejected it before post creation with `Video could not be read from its URL`.
- No Buffer post was created and no publication is claimed. The unchanged URL was not resubmitted.
- TikTok item 393673161 remained `PENDING` for 18:00 ET and was not touched before its intended time.

Recovery blocker: the finished video needs a Buffer-readable media asset or another confirmed zero-cost automatic upload route. Do not retry the same Metricool URL.


## 18:00 ET publishing recovery

Dancing Plague YouTube was recovered without a paid service or manual/notification publishing:

- Metricool item `393673008` remained a definite account-limit error.
- The finished MP4 was imported into Wix Media Manager and reached `READY` as media ID `72b571_eaa2560f3ec34db18bd6c6f593a0c3b2`.
- A final duplicate check found no matching Buffer YouTube post and confirmed Wix had no connected YouTube publisher.
- Buffer automatic post `6acea9df7a29109965b36662` returned `sent`.
- Public URL: https://www.youtube.com/watch?v=NdFtf7h43z8
- The post retained Education category, public privacy, not-made-for-kids status, and truthful AI-generated-content disclosure.

Dancing Plague TikTok item `393673161` was still `PENDING` immediately after its 18:00 ET intended time. No retry or duplicate was submitted; check later for a definite terminal result.
