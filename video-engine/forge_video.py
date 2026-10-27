#!/usr/bin/env python3
"""SatisfyForge zero-cost vertical-video assembly and QA.

Uses a locally installed FFmpeg/ffprobe. No paid API is required.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
SUPPORTED_VERTICAL_RESOLUTIONS = {(1080, 1920), (2160, 3840)}


@dataclass(frozen=True)
class RenderSpec:
    input_video: Path
    output_video: Path
    voiceover: Path | None = None
    captions: Path | None = None
    width: int = TARGET_WIDTH
    height: int = TARGET_HEIGHT
    fps: int = TARGET_FPS
    crf: int = 20
    preset: str = "medium"


def _owned_runtime_candidates(name: str) -> list[Path]:
    """Return zero-cost local runtime candidates without committing binaries to Git."""
    env_name = f"SATISFYFORGE_{name.upper()}"
    candidates: list[Path] = []
    if os.environ.get(env_name):
        candidates.append(Path(os.environ[env_name]).expanduser())

    base = Path.home() / "SatisfyForge/tools/media-runtime/node_modules"
    if name == "ffmpeg":
        candidates.append(base / "ffmpeg-static/ffmpeg")
    elif name == "ffprobe":
        arch = platform.machine().lower()
        preferred = "arm64" if arch in {"arm64", "aarch64"} else "x64"
        candidates.extend([
            base / f"ffprobe-static/bin/darwin/{preferred}/ffprobe",
            base / "ffprobe-static/bin/darwin/arm64/ffprobe",
            base / "ffprobe-static/bin/darwin/x64/ffprobe",
        ])
    return candidates


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    for candidate in _owned_runtime_candidates(name):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    env_name = f"SATISFYFORGE_{name.upper()}"
    raise RuntimeError(
        f"{name} was not found. Put it on PATH, set {env_name}, "
        "or install the owned SatisfyForge media runtime under ~/SatisfyForge/tools/media-runtime."
    )


def _filter_escape(path: Path) -> str:
    # FFmpeg filter syntax needs more escaping than ordinary shell arguments.
    value = str(path.resolve()).replace("\\", "/")
    for old, new in [(":", r"\:"), ("'", r"\'"), (",", r"\,"), ("[", r"\["), ("]", r"\]")]:
        value = value.replace(old, new)
    return value


def build_video_filter(spec: RenderSpec) -> str:
    filters = [
        f"scale={spec.width}:{spec.height}:force_original_aspect_ratio=increase",
        f"crop={spec.width}:{spec.height}",
        f"fps={spec.fps}",
        "format=yuv420p",
    ]
    if spec.captions:
        filters.append(f"subtitles='{_filter_escape(spec.captions)}'")
    return ",".join(filters)


def build_render_command(spec: RenderSpec, ffmpeg: str = "ffmpeg") -> list[str]:
    if spec.crf < 0 or spec.crf > 51:
        raise ValueError("CRF must be between 0 and 51")
    if spec.fps <= 0 or spec.width <= 0 or spec.height <= 0:
        raise ValueError("FPS and dimensions must be positive")

    cmd = [ffmpeg, "-hide_banner", "-y", "-i", str(spec.input_video)]
    if spec.voiceover:
        cmd += ["-i", str(spec.voiceover)]

    cmd += [
        "-map", "0:v:0",
        "-vf", build_video_filter(spec),
        "-c:v", "libx264",
        "-preset", spec.preset,
        "-crf", str(spec.crf),
        "-pix_fmt", "yuv420p",
        "-r", str(spec.fps),
        "-movflags", "+faststart",
    ]

    if spec.voiceover:
        cmd += [
            "-map", "1:a:0",
            "-c:a", "aac",
            "-b:a", "192k",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-shortest",
        ]
    else:
        # Preserve source audio when it exists, but do not fail on silent clips.
        cmd += ["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"]

    cmd += [str(spec.output_video)]
    return cmd


def _fraction_to_float(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None


def analyze_probe(payload: dict[str, Any]) -> dict[str, Any]:
    streams = payload.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = payload.get("format", {})
    if not video:
        return {"ok": False, "errors": ["No video stream found"], "warnings": [], "facts": {}}

    fps = _fraction_to_float(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    facts = {
        "codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "width": video.get("width"),
        "height": video.get("height"),
        "fps": fps,
        "duration_seconds": float(fmt.get("duration", 0) or 0),
        "has_audio": bool(audio),
        "audio_codec": audio.get("codec_name") if audio else None,
    }

    errors: list[str] = []
    warnings: list[str] = []
    if facts["codec"] != "h264":
        errors.append(f"Video codec is {facts['codec']!r}, expected H.264")
    if facts["pixel_format"] != "yuv420p":
        errors.append(f"Pixel format is {facts['pixel_format']!r}, expected yuv420p")
    if (facts["width"], facts["height"]) not in SUPPORTED_VERTICAL_RESOLUTIONS:
        errors.append(f"Resolution is {facts['width']}x{facts['height']}, expected 1080x1920 or 2160x3840")
    if fps is None or abs(fps - TARGET_FPS) > 0.05:
        errors.append(f"Average frame rate is {fps!r}, expected {TARGET_FPS} fps")
    if facts["duration_seconds"] <= 0:
        errors.append("Duration is missing or zero")
    if not audio:
        warnings.append("No audio stream found")
    elif facts["audio_codec"] != "aac":
        warnings.append(f"Audio codec is {facts['audio_codec']!r}, AAC is preferred")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "facts": facts}


def probe_file(path: Path, ffprobe: str | None = None) -> dict[str, Any]:
    ffprobe = ffprobe or require_binary("ffprobe")
    cmd = [
        ffprobe, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return analyze_probe(json.loads(result.stdout))


def parse_quality_intervals(log: str, duration_seconds: float | None = None) -> dict[str, list[dict[str, float]]]:
    """Parse FFmpeg's structured black, freeze and silence filter messages."""
    result: dict[str, list[dict[str, float]]] = {"black": [], "freeze": [], "silence": []}
    patterns = {
        "black": re.compile(r"black_start:\s*([\d.]+)\s+black_end:\s*([\d.]+)\s+black_duration:\s*([\d.]+)"),
        "freeze_start": re.compile(r"freeze_start:\s*([\d.]+)"),
        "freeze_end": re.compile(r"freeze_end:\s*([\d.]+)"),
        "silence_start": re.compile(r"silence_start:\s*([\d.]+)"),
        "silence_end": re.compile(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)"),
    }
    pending: dict[str, float] = {}
    for line in log.splitlines():
        black = patterns["black"].search(line)
        if black:
            start, end, dur = map(float, black.groups())
            result["black"].append({"start": start, "end": end, "duration": dur})
        for kind in ("freeze", "silence"):
            start_match = patterns[f"{kind}_start"].search(line)
            if start_match:
                pending[kind] = float(start_match.group(1))
            end_match = patterns[f"{kind}_end"].search(line)
            if end_match:
                end = float(end_match.group(1))
                start = pending.pop(kind, None)
                if start is not None and end >= start:
                    result[kind].append({"start": start, "end": end, "duration": end - start})
    # FFmpeg may emit freeze_start without freeze_end when a video ends frozen.
    if duration_seconds is not None and duration_seconds > 0:
        for kind, start in pending.items():
            if start < duration_seconds:
                result[kind].append({"start": start, "end": duration_seconds,
                                     "duration": duration_seconds - start})
    return result


def quality_scan(path: Path, *, ffmpeg: str | None = None,
                 ffprobe: str | None = None, strict: bool = False) -> dict[str, Any]:
    """Check format and suspicious media intervals; no publishing or editing."""
    report = probe_file(path, ffprobe)
    if not report["facts"]:
        return report
    ffmpeg = ffmpeg or require_binary("ffmpeg")
    base = [ffmpeg, "-hide_banner", "-nostdin", "-i", str(path)]
    scans = [base + ["-vf", "blackdetect=d=0.5:pix_th=0.08,freezedetect=n=-50dB:d=2",
                     "-an", "-f", "null", "-"]]
    if report["facts"]["has_audio"]:
        scans.append(base + ["-vn", "-af", "silencedetect=n=-35dB:d=2",
                             "-f", "null", "-"])
    segments = {"black": [], "freeze": [], "silence": []}
    for cmd in scans:
        result = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            report["errors"].append("FFmpeg quality scan failed: " + result.stderr[-600:])
            continue
        parsed = parse_quality_intervals(result.stderr, report["facts"]["duration_seconds"])
        for kind in segments:
            segments[kind].extend(parsed[kind])
    report["segments"] = segments
    descriptions = {"black": "black-screen", "freeze": "frozen-scene", "silence": "audio-silence"}
    for kind, items in segments.items():
        for item in items:
            report["warnings"].append(
                f"Possible {descriptions[kind]} segment at {item['start']:.2f}–{item['end']:.2f}s "
                f"({item['duration']:.2f}s); review creatively before approving")
    if strict and segments and any(segments.values()):
        report["errors"].append("Strict quality gate: suspicious segments require review")
    report["ok"] = not report["errors"]
    return report


def validate_inputs(spec: RenderSpec) -> None:
    for label, path in [("input video", spec.input_video), ("voiceover", spec.voiceover), ("captions", spec.captions)]:
        if path is not None and not path.is_file():
            raise FileNotFoundError(f"{label} not found: {path}")
    spec.output_video.parent.mkdir(parents=True, exist_ok=True)


def render(spec: RenderSpec) -> dict[str, Any]:
    validate_inputs(spec)
    ffmpeg = require_binary("ffmpeg")
    cmd = build_render_command(spec, ffmpeg)
    subprocess.run(cmd, check=True)
    report = probe_file(spec.output_video)
    if not report["ok"]:
        raise RuntimeError("Render completed but QA failed: " + "; ".join(report["errors"]))
    return report


def _print_report(report: dict[str, Any]) -> None:
    print(json.dumps(report, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SatisfyForge owned vertical video renderer and QA tool")
    sub = parser.add_subparsers(dest="command", required=True)

    r = sub.add_parser("render", help="Normalize and assemble a publish-ready vertical MP4")
    r.add_argument("--input", required=True, type=Path)
    r.add_argument("--output", required=True, type=Path)
    r.add_argument("--voiceover", type=Path)
    r.add_argument("--captions", type=Path, help="SRT/ASS captions to burn into the video")
    r.add_argument("--crf", type=int, default=20)
    r.add_argument("--preset", default="medium")
    r.add_argument("--resolution", choices=["1080x1920", "2160x3840"], default="1080x1920",
                   help="Vertical full HD or 4K output (upscaling does not create missing detail)")

    q = sub.add_parser("validate", help="Run publish-format QA on an existing MP4")
    q.add_argument("--input", required=True, type=Path)

    deep = sub.add_parser("quality", help="Format QA plus black/freeze/silence detection")
    deep.add_argument("--input", required=True, type=Path)
    deep.add_argument("--strict", action="store_true", help="Fail if any suspicious intervals are found")

    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            width, height = map(int, args.resolution.split("x"))
            report = render(RenderSpec(args.input, args.output, args.voiceover,
                                       args.captions, width=width, height=height,
                                       crf=args.crf, preset=args.preset))
        elif args.command == "quality":
            if not args.input.is_file():
                raise FileNotFoundError(f"input video not found: {args.input}")
            report = quality_scan(args.input, strict=args.strict)
        else:
            if not args.input.is_file():
                raise FileNotFoundError(f"input video not found: {args.input}")
            report = probe_file(args.input)
        _print_report(report)
        return 0 if report["ok"] else 2
    except (RuntimeError, FileNotFoundError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
