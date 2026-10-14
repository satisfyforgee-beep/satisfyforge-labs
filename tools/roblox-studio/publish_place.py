#!/usr/bin/env python3
"""Safely publish a tested Roblox place to an EXISTING experience via Open Cloud.

The API key is never written to disk or printed. By default this script is a dry run;
`--confirm-publish` is required before any Roblox write occurs.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_PLACE_BYTES = 100 * 1024 * 1024
PUBLISH_URL = "https://apis.roblox.com/universes/v1/{universe_id}/places/{place_id}/versions?versionType=Published"


def validate_place(path: Path) -> tuple[str, int]:
    if not path.is_file():
        raise FileNotFoundError(f"Place file not found: {path}")
    if path.suffix.lower() not in {".rbxl", ".rbxlx"}:
        raise ValueError("Place file must end in .rbxl or .rbxlx")
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("Place file is empty")
    if size > MAX_PLACE_BYTES:
        raise ValueError(f"Place file is {size} bytes; Roblox place-file limit is 100 MiB")
    content_type = "application/xml" if path.suffix.lower() == ".rbxlx" else "application/octet-stream"
    return content_type, size


def run_smoke(game: str) -> None:
    runner = ROOT / "tools/roblox-studio/run_smoke.py"
    result = subprocess.run([sys.executable, str(runner), "--game", game], cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Roblox Studio runtime smoke failed for {game}; publish blocked")


def resolve_key(env_name: str) -> str:
    key = os.environ.get(env_name, "").strip()
    if key:
        return key

    # Preferred local path on macOS: keep the key in Keychain so recurring publishes
    # do not require the secret to appear in shell history, chat, repo files, or env files.
    if sys.platform == "darwin":
        result = subprocess.run(
            [
                "security", "find-generic-password",
                "-a", "satisfyforge",
                "-s", "SatisfyForgeRobloxOpenCloud",
                "-w",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

    key = getpass.getpass("Roblox Open Cloud API key (hidden; not saved): ").strip()
    if not key:
        raise ValueError("No Roblox Open Cloud API key supplied")
    return key


def publish(path: Path, universe_id: int, place_id: int, api_key: str, content_type: str) -> int:
    url = PUBLISH_URL.format(universe_id=universe_id, place_id=place_id)
    request = urllib.request.Request(
        url,
        data=path.read_bytes(),
        method="POST",
        headers={"x-api-key": api_key, "Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Roblox publish HTTP {exc.code}: {body[:1200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Roblox publish network error: {exc.reason}") from exc

    version = payload.get("versionNumber")
    if not isinstance(version, int):
        raise RuntimeError(f"Roblox response did not contain a versionNumber: {payload}")
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish a tested place to an existing Roblox place via Open Cloud")
    parser.add_argument("--file", required=True, type=Path, help="Local .rbxl or .rbxlx file")
    parser.add_argument("--universe-id", required=True, type=int)
    parser.add_argument("--place-id", required=True, type=int)
    parser.add_argument("--smoke-game", choices=["brainrot-rush", "tile-panic", "snackquake"], help="Run owned Studio runtime gate first")
    parser.add_argument("--api-key-env", default="ROBLOX_OPEN_CLOUD_KEY", help="Environment variable to read before hidden prompt")
    parser.add_argument("--confirm-publish", action="store_true", help="Required to perform the external Roblox write")
    args = parser.parse_args(argv)

    try:
        content_type, size = validate_place(args.file.expanduser().resolve())
        path = args.file.expanduser().resolve()
        if args.smoke_game:
            run_smoke(args.smoke_game)

        print(json.dumps({
            "ready": True,
            "file": str(path),
            "bytes": size,
            "content_type": content_type,
            "universe_id": args.universe_id,
            "place_id": args.place_id,
            "smoke_gate": args.smoke_game,
            "will_publish": bool(args.confirm_publish),
        }, indent=2))

        if not args.confirm_publish:
            print("DRY RUN ONLY: add --confirm-publish after verifying the exact target IDs.")
            return 0

        api_key = resolve_key(args.api_key_env)
        version = publish(path, args.universe_id, args.place_id, api_key, content_type)
        print(json.dumps({
            "published": True,
            "universe_id": args.universe_id,
            "place_id": args.place_id,
            "version_number": version,
        }, indent=2))
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
