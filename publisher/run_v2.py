#!/usr/bin/env python3
"""SatisfyForge Direct Publisher v2.

Extends the proven v1 runner with a direct Facebook Reels adapter while keeping
v1's queue/state/duplicate-protection behavior. The runner only calls a
platform when that platform is enabled on a due queue item.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import requests

import run as core


# v1 was created against an older Graph version. Keep one configurable value,
# but use the current project default when the repository variable is unset.
if not os.environ.get("META_GRAPH_VERSION"):
    os.environ["META_GRAPH_VERSION"] = "v26.0"

LEGACY_PUBLISH = core.publish_platform


def publish_facebook(video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Publish a Facebook Page Reel from a public video URL.

    Uses Meta's Page Reels start -> hosted upload -> finish flow. A Page ID and
    Page access token are deliberately separate from the Instagram credentials
    so the publisher cannot accidentally use the wrong token type.
    """

    page_id = core.require_env("META_FB_PAGE_ID")
    token = core.require_env("META_FB_PAGE_ACCESS_TOKEN")
    graph_version = os.environ.get("META_GRAPH_VERSION") or "v26.0"
    base = f"https://graph.facebook.com/{graph_version}"

    start_resp = requests.post(
        f"{base}/{page_id}/video_reels",
        params={
            "upload_phase": "start",
            "access_token": token,
        },
        timeout=core.HTTP_TIMEOUT,
    )
    started = core.check_json_response(start_resp, "Facebook Reel start")
    video_id = started.get("video_id")
    upload_url = started.get("upload_url")
    if not video_id or not upload_url:
        raise core.PublishError(
            f"Facebook Reel start returned incomplete upload data: {started}"
        )

    upload_resp = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {token}",
            "file_url": video_url,
        },
        timeout=max(core.HTTP_TIMEOUT, 10 * 60),
    )
    uploaded = core.check_json_response(upload_resp, "Facebook Reel hosted upload")
    if uploaded.get("success") is False:
        raise core.PublishError(f"Facebook Reel hosted upload failed: {uploaded}")

    finish_data = {
        "upload_phase": "finish",
        "video_id": video_id,
        "video_state": "PUBLISHED",
        "access_token": token,
    }
    description = cfg.get("caption") or cfg.get("description") or ""
    title = cfg.get("title") or ""
    if description:
        finish_data["description"] = description
    if title:
        finish_data["title"] = title

    finish_resp = requests.post(
        f"{base}/{page_id}/video_reels",
        data=finish_data,
        timeout=core.HTTP_TIMEOUT,
    )
    finished = core.check_json_response(finish_resp, "Facebook Reel finish")
    if finished.get("success") is False:
        raise core.PublishError(f"Facebook Reel finish failed: {finished}")

    return {
        "status": "sent",
        "external_id": str(video_id),
        "platform_response": finished,
    }


def publish_platform(platform: str, video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if platform == "facebook":
        return publish_facebook(video_url, cfg)
    return LEGACY_PUBLISH(platform, video_url, cfg)


def main() -> int:
    # v1's main loop already owns queue timing, state persistence and the
    # no-blind-retry duplicate policy. Swap only the dispatcher.
    core.publish_platform = publish_platform
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
