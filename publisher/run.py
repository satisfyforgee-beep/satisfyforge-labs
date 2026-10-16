#!/usr/bin/env python3
"""SatisfyForge direct social publisher.

Runs due queue items through official platform APIs without Buffer/Metricool.
Designed for scheduled GitHub Actions execution with $0 upfront spend.

Required secrets vary by platform. Never hard-code credentials in this file.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parent
QUEUE_PATH = ROOT / "queue.json"
STATE_PATH = ROOT / "state.json"
HISTORY_PATH = ROOT / "history.json"
HTTP_TIMEOUT = 60
SUPPORTED_PLATFORMS = {"instagram", "facebook", "youtube", "tiktok"}


class PublishError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("publish_at must include a timezone")
    return dt.astimezone(timezone.utc)


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise PublishError(f"Missing required secret: {name}")
    return value


def normalize_concept(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def validate_media_sha256(value: Any, item_id: str) -> str:
    digest = str(value or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError(f"{item_id}: media_sha256 must be a 64-character SHA-256 hex digest")
    return digest


def validate_queue(
    queue: Dict[str, Any],
    expected_account_identity: str | None = None,
    history: Dict[str, Any] | None = None,
) -> None:
    """Fail closed before any platform write when queue data is unsafe.

    In addition to malformed jobs, this blocks concepts/assets already recorded
    as completed or permanently retired and prevents the same concept or media
    hash from being queued twice under different IDs/times.
    """
    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError("queue.items must be a list")

    history = history if history is not None else load_json(HISTORY_PATH, {})
    blocked_concepts = {normalize_concept(str(x)) for x in history.get("blocked_concepts", [])}
    completed_concepts = {normalize_concept(str(x)) for x in history.get("completed_concepts", [])}
    completed_hashes = {str(x).strip().lower() for x in history.get("completed_media_sha256", [])}

    ids: set[str] = set()
    queued_concepts: set[str] = set()
    queued_hashes: set[str] = set()
    exact_jobs: set[tuple[str, str, str]] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"queue.items[{index}] must be an object")

        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise ValueError(f"queue.items[{index}] must have a non-empty id")
        if item_id in ids:
            raise ValueError(f"duplicate queue item id: {item_id}")
        ids.add(item_id)

        if item.get("approved_for_direct_publish") is not True:
            raise ValueError(f"{item_id}: approved_for_direct_publish must be true")
        account_identity = str(item.get("account_identity", "")).strip()
        if not account_identity:
            raise ValueError(f"{item_id}: account_identity is required")
        if expected_account_identity is not None and account_identity != expected_account_identity:
            raise ValueError(f"{item_id}: account_identity does not match verified publisher identity")

        concept_key = normalize_concept(str(item.get("concept_key", "")))
        if not concept_key:
            raise ValueError(f"{item_id}: concept_key is required")
        if concept_key in blocked_concepts:
            raise ValueError(f"{item_id}: concept_key is permanently blocked: {concept_key}")
        if concept_key in completed_concepts:
            raise ValueError(f"{item_id}: concept_key is already completed: {concept_key}")
        if concept_key in queued_concepts:
            raise ValueError(f"duplicate queued concept: {concept_key}")
        queued_concepts.add(concept_key)

        media_sha256 = validate_media_sha256(item.get("media_sha256"), item_id)
        if media_sha256 in completed_hashes:
            raise ValueError(f"{item_id}: media_sha256 is already completed")
        if media_sha256 in queued_hashes:
            raise ValueError(f"duplicate queued media_sha256: {media_sha256}")
        queued_hashes.add(media_sha256)

        publish_at = item.get("publish_at")
        if not isinstance(publish_at, str):
            raise ValueError(f"{item_id}: publish_at must be a timezone-aware string")
        canonical_time = parse_time(publish_at).isoformat()

        video_url = item.get("video_url")
        if not isinstance(video_url, str) or not video_url.startswith(("https://", "http://")):
            raise ValueError(f"{item_id}: video_url must be an http(s) URL")

        platforms = item.get("platforms")
        if not isinstance(platforms, dict) or not platforms:
            raise ValueError(f"{item_id}: platforms must be a non-empty object")

        enabled_count = 0
        for platform, cfg in platforms.items():
            if platform not in SUPPORTED_PLATFORMS:
                raise ValueError(f"{item_id}: unsupported platform: {platform}")
            if not isinstance(cfg, dict):
                raise ValueError(f"{item_id}/{platform}: configuration must be an object")
            if not cfg.get("enabled", False):
                continue
            enabled_count += 1
            signature = (platform, video_url, canonical_time)
            if signature in exact_jobs:
                raise ValueError(
                    f"exact duplicate publish job: {platform} {video_url} {canonical_time}"
                )
            exact_jobs.add(signature)

        if enabled_count == 0:
            raise ValueError(f"{item_id}: at least one platform must be enabled")


def check_json_response(resp: requests.Response, context: str) -> Dict[str, Any]:
    try:
        payload = resp.json()
    except ValueError:
        payload = {"raw": resp.text[:1000]}
    if not resp.ok:
        raise PublishError(f"{context} failed ({resp.status_code}): {payload}")
    return payload


def publish_instagram(video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Publish a Reel directly with the Instagram Graph API."""
    ig_user_id = require_env("META_IG_USER_ID")
    token = require_env("META_ACCESS_TOKEN")
    graph_version = os.environ.get("META_GRAPH_VERSION", "v24.0")
    base = f"https://graph.facebook.com/{graph_version}"

    create_data = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": cfg.get("caption", ""),
        "share_to_feed": "true" if cfg.get("share_to_feed", True) else "false",
        "access_token": token,
    }
    create_resp = requests.post(
        f"{base}/{ig_user_id}/media", data=create_data, timeout=HTTP_TIMEOUT
    )
    created = check_json_response(create_resp, "Instagram media container creation")
    container_id = created.get("id")
    if not container_id:
        raise PublishError(f"Instagram did not return a container id: {created}")

    # Instagram processes Reels asynchronously. Poll conservatively.
    deadline = time.time() + 15 * 60
    last_status: Dict[str, Any] = {}
    while time.time() < deadline:
        status_resp = requests.get(
            f"{base}/{container_id}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=HTTP_TIMEOUT,
        )
        last_status = check_json_response(status_resp, "Instagram container status")
        code = str(last_status.get("status_code", "")).upper()
        if code == "FINISHED":
            break
        if code in {"ERROR", "EXPIRED"}:
            raise PublishError(f"Instagram processing failed: {last_status}")
        time.sleep(10)
    else:
        raise PublishError(f"Instagram processing timed out: {last_status}")

    publish_resp = requests.post(
        f"{base}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=HTTP_TIMEOUT,
    )
    published = check_json_response(publish_resp, "Instagram media publish")
    return {
        "status": "sent",
        "container_id": container_id,
        "external_id": published.get("id"),
    }


def refresh_google_token() -> str:
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": require_env("GOOGLE_CLIENT_ID"),
            "client_secret": require_env("GOOGLE_CLIENT_SECRET"),
            "refresh_token": require_env("GOOGLE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=HTTP_TIMEOUT,
    )
    payload = check_json_response(resp, "Google OAuth token refresh")
    token = payload.get("access_token")
    if not token:
        raise PublishError("Google OAuth refresh returned no access_token")
    return token


def download_video(video_url: str) -> tuple[str, str, int]:
    resp = requests.get(video_url, stream=True, timeout=HTTP_TIMEOUT)
    if not resp.ok:
        raise PublishError(f"Video download failed ({resp.status_code})")

    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
    if not content_type.startswith("video/"):
        guessed = mimetypes.guess_type(video_url)[0]
        content_type = guessed if guessed and guessed.startswith("video/") else "video/mp4"

    suffix = mimetypes.guess_extension(content_type) or ".mp4"
    fd, path = tempfile.mkstemp(prefix="satisfyforge_", suffix=suffix)
    size = 0
    try:
        with os.fdopen(fd, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
    except Exception:
        try:
            os.unlink(path)
        finally:
            raise
    return path, content_type, size


def publish_youtube(video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Publish directly through YouTube Data API resumable uploads."""
    access_token = refresh_google_token()
    path, content_type, size = download_video(video_url)
    try:
        metadata = {
            "snippet": {
                "title": cfg.get("title") or "SatisfyForge Short",
                "description": cfg.get("description", ""),
                "tags": cfg.get("tags", []),
                "categoryId": str(cfg.get("category_id", "27")),
            },
            "status": {
                "privacyStatus": cfg.get("privacy", "public"),
                "selfDeclaredMadeForKids": bool(cfg.get("made_for_kids", False)),
            },
        }
        init_resp = requests.post(
            "https://www.googleapis.com/upload/youtube/v3/videos",
            params={"uploadType": "resumable", "part": "snippet,status"},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(size),
                "X-Upload-Content-Type": content_type,
            },
            data=json.dumps(metadata),
            timeout=HTTP_TIMEOUT,
        )
        if not init_resp.ok:
            check_json_response(init_resp, "YouTube resumable session creation")
        upload_url = init_resp.headers.get("Location")
        if not upload_url:
            raise PublishError("YouTube resumable session returned no Location header")

        with open(path, "rb") as f:
            upload_resp = requests.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": content_type,
                    "Content-Length": str(size),
                },
                data=f,
                timeout=max(HTTP_TIMEOUT, 10 * 60),
            )
        uploaded = check_json_response(upload_resp, "YouTube video upload")
        video_id = uploaded.get("id")
        return {
            "status": "sent",
            "external_id": video_id,
            "external_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
        }
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass


def publish_tiktok(video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Direct-post through TikTok Content Posting API using PULL_FROM_URL.

    TikTok requires an approved app + video.publish authorization. Public visibility
    also depends on TikTok's app audit. PULL_FROM_URL requires a verified domain or URL prefix.
    """
    token = require_env("TIKTOK_ACCESS_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    creator_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        headers=headers,
        json={},
        timeout=HTTP_TIMEOUT,
    )
    creator = check_json_response(creator_resp, "TikTok creator info")
    data = creator.get("data") or {}
    allowed_privacy = data.get("privacy_level_options") or []
    requested_privacy = cfg.get("privacy", "PUBLIC_TO_EVERYONE")
    if allowed_privacy and requested_privacy not in allowed_privacy:
        raise PublishError(
            f"TikTok privacy {requested_privacy} is not allowed for this account; options={allowed_privacy}"
        )

    body = {
        "post_info": {
            "title": cfg.get("caption", "")[:2200],
            "privacy_level": requested_privacy,
            "disable_comment": bool(cfg.get("disable_comment", False)),
            "disable_duet": bool(cfg.get("disable_duet", False)),
            "disable_stitch": bool(cfg.get("disable_stitch", False)),
            "brand_organic_toggle": bool(cfg.get("brand_organic", False)),
            "is_aigc": bool(cfg.get("is_aigc", False)),
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": video_url,
        },
    }
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/video/init/",
        headers=headers,
        json=body,
        timeout=HTTP_TIMEOUT,
    )
    initialized = check_json_response(init_resp, "TikTok direct post init")
    result_data = initialized.get("data") or {}
    publish_id = result_data.get("publish_id")
    if not publish_id:
        raise PublishError(f"TikTok returned no publish_id: {initialized}")

    # A successful init is not the same as a published public post. Track until terminal.
    deadline = time.time() + 10 * 60
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        status_resp = requests.post(
            "https://open.tiktokapis.com/v2/post/publish/status/fetch/",
            headers=headers,
            json={"publish_id": publish_id},
            timeout=HTTP_TIMEOUT,
        )
        last = check_json_response(status_resp, "TikTok publish status")
        status_data = last.get("data") or {}
        status = str(status_data.get("status", "")).upper()
        if status in {"PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"}:
            return {
                "status": "sent" if status == "PUBLISH_COMPLETE" else "needs_check",
                "external_id": publish_id,
                "platform_status": status,
            }
        if status in {"FAILED", "PUBLISH_FAILED"}:
            raise PublishError(f"TikTok publish failed: {last}")
        time.sleep(10)

    return {
        "status": "needs_check",
        "external_id": publish_id,
        "platform_status": (last.get("data") or {}).get("status"),
        "reason": "TikTok status did not reach a terminal state before timeout",
    }


def publish_platform(platform: str, video_url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    if platform == "instagram":
        return publish_instagram(video_url, cfg)
    if platform == "youtube":
        return publish_youtube(video_url, cfg)
    if platform == "tiktok":
        return publish_tiktok(video_url, cfg)
    raise PublishError(f"Unsupported direct platform: {platform}")


def require_runtime_publish_identity() -> str:
    if os.environ.get("SF_DIRECT_PUBLISHER_ENABLED", "").lower() != "true":
        raise PublishError("DIRECT_PUBLISHER_DISABLED")
    if os.environ.get("SF_PUBLISH_ACCOUNT_IDENTITY_VERIFIED", "").lower() != "true":
        raise PublishError("PUBLISH_ACCOUNT_IDENTITY_NOT_VERIFIED")
    identity = os.environ.get("SF_PUBLISH_ACCOUNT_IDENTITY", "").strip()
    if not identity:
        raise PublishError("PUBLISH_ACCOUNT_IDENTITY_MISSING")
    return identity


def main() -> int:
    expected_identity = require_runtime_publish_identity()
    queue = load_json(QUEUE_PATH, {"items": []})
    validate_queue(queue, expected_account_identity=expected_identity)
    state = load_json(STATE_PATH, {"items": {}})
    state_items = state.setdefault("items", {})
    changed = False
    now = utcnow()

    for item in queue.get("items", []):
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            print("Skipping queue item without id")
            continue
        publish_at = parse_time(item["publish_at"])
        if publish_at > now:
            continue
        video_url = item.get("video_url")
        if not video_url:
            print(f"{item_id}: no video_url; skipped")
            continue

        item_state = state_items.setdefault(item_id, {})
        for platform, cfg in (item.get("platforms") or {}).items():
            if not cfg.get("enabled", False):
                continue
            prior = item_state.get(platform) or {}
            if prior.get("status") in {"sent", "needs_check"}:
                print(f"{item_id}/{platform}: {prior.get('status')} already recorded; no duplicate attempt")
                continue

            print(f"Publishing {item_id} -> {platform}")
            try:
                result = publish_platform(platform, video_url, cfg)
                result["updated_at"] = utcnow().isoformat()
                item_state[platform] = result
                print(f"{item_id}/{platform}: {result.get('status')}")
            except Exception as exc:
                # We intentionally do not blindly retry unknown write failures. An API POST can
                # succeed remotely even if the response is lost locally, which would create duplicates.
                item_state[platform] = {
                    "status": "needs_check",
                    "reason": str(exc)[:2000],
                    "updated_at": utcnow().isoformat(),
                }
                print(f"{item_id}/{platform}: needs_check: {exc}")
            changed = True
            save_json(STATE_PATH, state)

    if changed:
        save_json(STATE_PATH, state)
    else:
        print("No due unpublished work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

