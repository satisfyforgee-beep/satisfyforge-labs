# SatisfyForge Direct Publisher

Goal: publish SatisfyForge media directly to official platform APIs without Buffer or Metricool as the normal publishing layer.

## Zero-cost operating rule

This project is designed around **$0 upfront operating spend**. We do not buy social schedulers, ads, credits, servers, followers, inventory, or trials. Where a platform charges a transaction fee, that fee should be deducted from money already received from a customer rather than funded in advance.

The publisher can run from GitHub Actions on a schedule and call the official platform APIs directly. GitHub is only the automation runner; it is not a social scheduling intermediary.

## Current architecture

- `queue.json` — one source of truth for scheduled content.
- `state.json` — records per-platform publish state to prevent accidental duplicates.
- `run.py` — proven v1 queue/state engine and Instagram, YouTube, TikTok adapters.
- `run_v2.py` — current entry point. Adds direct Facebook Page Reels while reusing v1 queue/state/duplicate protection.
- `test_run_v2.py` — contract tests for the Facebook hosted-Reel flow.
- Instagram — direct Meta/Instagram publishing path.
- Facebook — direct Meta Page Reels start → hosted upload → finish path.
- YouTube — direct YouTube Data API resumable upload path.
- TikTok — direct Content Posting API path using `PULL_FROM_URL` when the app/account is approved and the media domain or URL prefix is verified.

The GitHub workflow runs syntax + contract tests before every publisher execution. A platform is contacted only when it is enabled on a due queue item.

## One-time connections still required

Owning our publisher removes Buffer/Metricool limits, but it cannot remove the social networks' own authorization rules. The account owner still has to approve OAuth/app permissions once for each platform.

Required repository secrets when those direct connections are ready:

- `META_IG_USER_ID`
- `META_ACCESS_TOKEN`
- `META_FB_PAGE_ID`
- `META_FB_PAGE_ACCESS_TOKEN`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `TIKTOK_ACCESS_TOKEN`

Optional repository variable:

- `META_GRAPH_VERSION` — defaults to `v26.0` in the v2 runner when unset.

Never commit tokens, passwords, OTPs, bank information, or tax information to the repository.

## Queue format

```json
{
  "items": [
    {
      "id": "example-v1",
      "publish_at": "2026-10-13T14:00:00Z",
      "video_url": "https://example.com/video.mp4",
      "platforms": {
        "instagram": {
          "enabled": true,
          "caption": "Caption here",
          "share_to_feed": true
        },
        "facebook": {
          "enabled": true,
          "title": "Optional Reel title",
          "caption": "Facebook Reel description"
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
- AI-content disclosure fields are carried when supported by the direct adapter.
- Facebook credentials are kept separate from Instagram credentials so the wrong token type is not silently reused.

## Temporary fallbacks

Buffer and Wix Social Publisher can remain temporary zero-cost bridges for accounts whose official direct API credentials are not yet installed. They are not the intended permanent publishing layer. Manual/notification publishing is not used.

## Revenue rule

New SatisfyForge projects should prefer customer-funded models: digital products, preorders, deposits, sponsorships, affiliate/revenue-share deals, print-on-demand, and marketplace fees deducted from completed sales. Avoid models that require us to front cash before a customer or sponsor pays.
