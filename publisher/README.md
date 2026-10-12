# SatisfyForge Direct Publisher

Goal: publish SatisfyForge media directly to platform APIs without Buffer or Metricool as the normal publishing layer.

## Zero-cost operating rule

This project is designed around **$0 upfront operating spend**. We do not buy social schedulers, ads, credits, servers, followers, inventory, or trials. Where a platform charges a transaction fee, that fee should be deducted from money already received from a customer rather than funded in advance.

The publisher can run from GitHub Actions on a schedule and call the official platform APIs directly. GitHub is only the automation runner; it is not a social scheduling intermediary.

## Supported architecture

- `queue.json` — one source of truth for scheduled content.
- `state.json` — records per-platform publish state to prevent accidental duplicates.
- `run.py` — checks due items and dispatches them.
- Instagram — direct Meta/Instagram publishing path.
- YouTube — direct YouTube Data API resumable upload path.
- TikTok — direct Content Posting API path using `PULL_FROM_URL` when the app/account is approved and the media domain or URL prefix is verified.
- Facebook — planned direct adapter; Buffer can remain a temporary fallback only until the direct Meta video/reels adapter is finished and tested.

## One-time connections still required

Owning our publisher removes Buffer/Metricool limits, but it cannot remove the social networks' own authorization rules. The account owner still has to approve OAuth/app permissions once for each platform.

Required repository secrets when those direct connections are ready:

- `META_IG_USER_ID`
- `META_ACCESS_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `TIKTOK_ACCESS_TOKEN`

Never commit tokens, passwords, OTPs, bank information, or tax information to the repository.

## Queue format

```json
{
  "items": [
    {
      "id": "operation-mincemeat-v1",
      "publish_at": "2026-10-12T21:00:00Z",
      "video_url": "https://example.com/video.mp4",
      "platforms": {
        "instagram": {
          "enabled": true,
          "caption": "Caption here",
          "share_to_feed": true
        },
        "youtube": {
          "enabled": true,
          "title": "Title",
          "description": "Description",
          "privacy": "public",
          "category_id": "27"
        },
        "tiktok": {
          "enabled": true,
          "caption": "Caption here",
          "privacy": "PUBLIC_TO_EVERYONE",
          "is_aigc": true
        }
      }
    }
  ]
}
```

## Safety / duplicate policy

- A platform marked `sent` in `state.json` is never posted again automatically.
- Ambiguous network failures are marked `needs_check`, not blindly retried.
- The runner does not spend money.
- No posting happens until the platform's own API authorization is present.
- AI-content disclosure fields are carried when supported.

## Revenue rule

New SatisfyForge projects should prefer customer-funded models: digital products, preorders, deposits, sponsorships, affiliate/revenue-share deals, print-on-demand, and marketplace fees deducted from completed sales. Avoid models that require us to front cash before a customer or sponsor pays.
