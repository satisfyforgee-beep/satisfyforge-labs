#!/usr/bin/env python3
"""Normalize creator-platform analytics exports into one evidence schema."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ALIASES = {
    "content_id": ["content_id", "video_id", "post_id", "id", "video id", "post id"],
    "title": ["title", "video_title", "post_title", "caption", "video title", "post title", "description"],
    "published_at": ["published_at", "published", "date", "created_at", "publish date", "date published"],
    "views": ["views", "video views", "plays", "impressions", "reel plays", "total views"],
    "likes": ["likes", "like count", "reactions"],
    "comments": ["comments", "comment count"],
    "shares": ["shares", "share count"],
    "saves": ["saves", "saved", "bookmarks"],
    "clicks": ["clicks", "link clicks", "website clicks", "url clicks"],
    "revenue": ["revenue", "estimated revenue", "earnings", "sales revenue"],
}


@dataclass
class NormalizedRow:
    platform: str
    content_id: str
    title: str
    published_at: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    clicks: int
    revenue: float
    source_file: str
    observed_at: str


def _key(s: str) -> str:
    return " ".join(str(s).strip().lower().replace("_", " ").replace("-", " ").split())


def _lookup(row: dict[str, str], field: str) -> str:
    keyed = {_key(k): (v or "") for k, v in row.items()}
    for alias in ALIASES[field]:
        if _key(alias) in keyed:
            return keyed[_key(alias)].strip()
    return ""


def _number(value: str, integer: bool = False):
    clean = str(value or "").strip().replace(",", "").replace("$", "").replace("%", "")
    if clean in {"", "-", "—", "N/A", "n/a"}:
        return 0 if integer else 0.0
    try:
        n = float(clean)
    except ValueError:
        return 0 if integer else 0.0
    return int(round(n)) if integer else n


def normalize_csv(path: Path, platform: str, observed_at: str | None = None) -> list[NormalizedRow]:
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row")
        rows = []
        for index, row in enumerate(reader, start=1):
            content_id = _lookup(row, "content_id") or f"{path.stem}-{index}"
            title = _lookup(row, "title") or content_id
            rows.append(NormalizedRow(
                platform=platform.lower().strip(),
                content_id=content_id,
                title=title,
                published_at=_lookup(row, "published_at"),
                views=_number(_lookup(row, "views"), integer=True),
                likes=_number(_lookup(row, "likes"), integer=True),
                comments=_number(_lookup(row, "comments"), integer=True),
                shares=_number(_lookup(row, "shares"), integer=True),
                saves=_number(_lookup(row, "saves"), integer=True),
                clicks=_number(_lookup(row, "clicks"), integer=True),
                revenue=_number(_lookup(row, "revenue"), integer=False),
                source_file=path.name,
                observed_at=observed_at,
            ))
    return rows


def summarize(rows: Iterable[NormalizedRow]) -> dict:
    rows = list(rows)
    totals = {k: 0 for k in ["views", "likes", "comments", "shares", "saves", "clicks"]}
    revenue = 0.0
    for row in rows:
        for key in totals:
            totals[key] += getattr(row, key)
        revenue += row.revenue
    engagements = totals["likes"] + totals["comments"] + totals["shares"] + totals["saves"]
    views = totals["views"]
    top_views = max(rows, key=lambda r: r.views, default=None)
    top_revenue = max(rows, key=lambda r: r.revenue, default=None)
    rpm_candidates = [r for r in rows if r.views > 0]
    top_rpm = max(rpm_candidates, key=lambda r: r.revenue / r.views * 1000, default=None)
    return {
        "rows": len(rows),
        "totals": {**totals, "revenue": round(revenue, 2), "engagements": engagements},
        "ratios": {
            "engagement_rate": round(engagements / views, 6) if views else 0,
            "click_rate": round(totals["clicks"] / views, 6) if views else 0,
            "revenue_per_1000_views": round(revenue / views * 1000, 4) if views else 0,
        },
        "leaders": {
            "views": _leader(top_views, "views"),
            "revenue": _leader(top_revenue, "revenue"),
            "revenue_per_1000_views": _leader(top_rpm, "rpm"),
        },
    }


def _leader(row: NormalizedRow | None, metric: str) -> dict | None:
    if row is None:
        return None
    if metric == "rpm":
        value = round(row.revenue / row.views * 1000, 4) if row.views else 0
    else:
        value = getattr(row, metric)
    return {"platform": row.platform, "content_id": row.content_id, "title": row.title, "value": value}


def build_payload(rows: list[NormalizedRow]) -> dict:
    return {
        "schema": "satisfyforge.analytics.v1",
        "summary": summarize(rows),
        "items": [asdict(r) for r in rows],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize creator analytics CSV exports")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--platform", required=True, choices=["youtube", "tiktok", "instagram", "facebook", "x", "other"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")
    rows = normalize_csv(args.input, args.platform)
    payload = build_payload(rows)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
