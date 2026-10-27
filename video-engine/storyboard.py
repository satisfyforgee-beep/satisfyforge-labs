#!/usr/bin/env python3
"""Review-first, licensed-scene assembly for SatisfyForge vertical stories.

JSON scene plan -> transparent timeline -> optional FFmpeg render -> format QA.
No AI voice account, stock-footage download, or publishing is invoked.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from forge_video import RenderSpec, build_video_filter, render, require_binary

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
LICENSE_CLASSES = {"owned", "public_domain", "licensed"}
CLAIM_CLASSES = {"verified", "unverified", "speculation"}


def _inside_assets(base: Path, filename: str, *, require_file: bool) -> Path:
    if not isinstance(filename, str) or not filename or Path(filename).is_absolute():
        raise ValueError("Asset paths must be nonempty and relative to assets directory")
    resolved = (base / filename).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("Asset path escapes its approved directory")
    if require_file and not resolved.is_file():
        raise FileNotFoundError(f"Required source media is missing: {filename}")
    return resolved


def prepare_plan(manifest_path: Path, *, require_files: bool = False) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    spec = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise ValueError("Manifest must be a JSON object")
    title = spec.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Story needs a descriptive title")
    assets = manifest_path.parent / "assets"
    claims = spec.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("claims must be a list")
    claim_by_id = {}
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("Claim must be an object")
        ident = claim.get("id")
        kind = claim.get("kind")
        if not isinstance(ident, str) or not ident or ident in claim_by_id:
            raise ValueError("Claims need unique IDs")
        if kind not in CLAIM_CLASSES or not isinstance(claim.get("text"), str) or not claim["text"].strip():
            raise ValueError("Claims need text and valid kind")
        if kind == "verified" and not str(claim.get("source_url", "")).startswith("https://"):
            raise ValueError("A verified claim must include its HTTPS source; check the source manually")
        claim_by_id[ident] = claim

    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or not 2 <= len(scenes) <= 40:
        raise ValueError("Story needs between 2 and 40 scenes")
    timeline = []
    ids = set()
    elapsed = 0.0
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError("Scene must be an object")
        ident = scene.get("id")
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("Scene IDs must be unique")
        ids.add(ident)
        duration = scene.get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 1 <= duration <= 30:
            raise ValueError("Scene must be 1–30 seconds")
        filename = scene.get("asset")
        path = _inside_assets(assets, filename, require_file=require_files)
        if path.suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
            raise ValueError("Unsupported scene media type")
        if scene.get("license") not in LICENSE_CLASSES:
            raise ValueError("Scene media needs owned/public_domain/licensed provenance")
        if not isinstance(scene.get("rights_note"), str) or not scene["rights_note"].strip():
            raise ValueError("Scene must document where use rights come from")
        if not isinstance(scene.get("visual_direction"), str) or not scene["visual_direction"].strip():
            raise ValueError("Each scene needs a creative visual direction")
        if not isinstance(scene.get("narration"), str) or not scene["narration"].strip():
            raise ValueError("Each scene needs planned human-reviewed narration")
        references = scene.get("claim_ids", [])
        if not isinstance(references, list) or any(not isinstance(c, str) or c not in claim_by_id for c in references):
            raise ValueError("Scene references an undefined factual claim")
        if any(claim_by_id[c]["kind"] != "verified" for c in references) and not scene.get("uncertainty_disclosure"):
            raise ValueError("Unverified or speculative claims need an explicit disclosure")
        duration = round(float(duration), 3)
        if require_files and scene["rights_note"].startswith("REPLACE:"):
            raise ValueError("Replace placeholder rights notes before rendering")
        timeline.append({"id": ident, "asset": filename, "license": scene["license"],
                         "rights_note": scene["rights_note"],
                         "start_seconds": round(elapsed, 3), "end_seconds": round(elapsed + duration, 3),
                         "duration_seconds": duration, "visual_direction": scene["visual_direction"],
                         "narration": scene["narration"], "claim_ids": references,
                         "uncertainty_disclosure": scene.get("uncertainty_disclosure", "")})
        elapsed += duration
    if elapsed > 300:
        raise ValueError("Review required for stories longer than five minutes")

    voiceover = spec.get("voiceover")
    captions = spec.get("captions")
    if voiceover is not None:
        if _inside_assets(assets, voiceover, require_file=require_files).suffix.lower() not in {".wav", ".mp3", ".m4a"}:
            raise ValueError("Voiceover must be .wav/.mp3/.m4a")
    if captions is not None:
        if _inside_assets(assets, captions, require_file=require_files).suffix.lower() not in {".srt", ".ass"}:
            raise ValueError("Captions must be .srt or .ass")
    return {"title": title, "duration_seconds": round(elapsed, 3),
            "scene_count": len(timeline), "timeline": timeline, "claims": claims,
            "claim_count": len(claims),
            "voiceover": voiceover, "captions": captions, "rendered": False,
            "human_review_required": ["Verify each cited claim and asset permission",
                                      "Listen for natural narration and accurate captions",
                                      "Review storytelling pace, shot variation and all visuals",
                                      "Approve final export before any publication"]}


def scene_command(ffmpeg: str, source: Path, output: Path, duration: float,
                  *, width: int, height: int) -> list[str]:
    is_still = source.suffix.lower() in IMAGE_EXTENSIONS
    before = ["-loop", "1", "-framerate", "30"] if is_still else ["-stream_loop", "-1"]
    filter_chain = build_video_filter(RenderSpec(source, output, width=width, height=height))
    return [ffmpeg, "-hide_banner", "-nostdin", "-y", *before, "-i", str(source),
            "-t", f"{duration:.3f}", "-vf", filter_chain, "-an", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
            str(output)]


def check_voiceover_duration(voiceover: Path, timeline_seconds: float) -> None:
    """Prevent `-shortest` from silently truncating scenes or narration."""
    probe = require_binary("ffprobe")
    command = [probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(voiceover)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    duration = float(json.loads(completed.stdout)["format"]["duration"])
    if not math.isfinite(duration) or abs(duration - timeline_seconds) > 0.75:
        raise ValueError(f"Voiceover {duration:.2f}s does not match planned story {timeline_seconds:.2f}s")


def render_story(manifest_path: Path, output: Path, *, resolution: str = "1080x1920") -> dict[str, Any]:
    if resolution not in {"1080x1920", "2160x3840"}:
        raise ValueError("Unsupported vertical resolution")
    if output.exists():
        raise FileExistsError("Preview output already exists; choose a new file path")
    plan = prepare_plan(manifest_path, require_files=True)
    if not plan["voiceover"]:
        raise ValueError("A human-reviewed voiceover audio file is required to render a story")
    width, height = map(int, resolution.split("x"))
    assets = manifest_path.resolve().parent / "assets"
    voiceover = _inside_assets(assets, plan["voiceover"], require_file=True)
    check_voiceover_duration(voiceover, plan["duration_seconds"])
    ffmpeg = require_binary("ffmpeg")
    with tempfile.TemporaryDirectory(prefix="sf-story-") as tmp:
        temp = Path(tmp)
        clips = []
        for i, scene in enumerate(plan["timeline"]):
            clip = temp / f"scene_{i:03}.mp4"
            source = _inside_assets(assets, scene["asset"], require_file=True)
            subprocess.run(scene_command(ffmpeg, source, clip, scene["duration_seconds"],
                                         width=width, height=height), check=True, capture_output=True)
            clips.append(clip)
        concat = temp / "timeline.txt"
        concat.write_text("".join(f"file '{p.name}'\n" for p in clips), encoding="utf-8")
        stitched = temp / "joined.mp4"
        subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-f", "concat", "-safe", "1",
                        "-i", str(concat), "-c", "copy", str(stitched)],
                       check=True, capture_output=True)
        report = render(RenderSpec(stitched, output, voiceover,
                                   _inside_assets(assets, plan["captions"], require_file=True) if plan["captions"] else None,
                                   width=width, height=height))
    return {**plan, "rendered": True, "output": str(output.resolve()), "technical_qa": report,
            "publication_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate/prepare/render a review-only licensed video story")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--render", action="store_true", help="Explicitly render local review preview")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resolution", choices=["1080x1920", "2160x3840"], default="1080x1920")
    args = parser.parse_args()
    if args.render and args.output is None:
        parser.error("--render needs --output")
    result = render_story(args.manifest, args.output, resolution=args.resolution) if args.render else prepare_plan(args.manifest)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
