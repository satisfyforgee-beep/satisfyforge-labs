#!/usr/bin/env python3
"""Run Tile Panic two-client boundary regression in real Roblox Studio."""
from __future__ import annotations
import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = "SF_TILE_MP_RESULT ok=true result=PASS:tile_panic_boundary"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=95)
    ap.add_argument("--keep-artifacts", action="store_true")
    args = ap.parse_args()
    studio = Path(os.environ.get("ROBLOX_STUDIO", "/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"))
    rojo = shutil.which("rojo") or str(Path.home() / "SatisfyForge/tools/rojo/rojo")
    if not studio.is_file() or not Path(rojo).is_file():
        print("Studio or Rojo unavailable", file=sys.stderr)
        return 1
    folder = Path(tempfile.mkdtemp(prefix="satisfyforge-tile-mp-"))
    place = folder / "tile-panic.rbxlx"
    log = folder / "studio.log"
    build = subprocess.run([str(rojo), "build", str(ROOT / "src/roblox/tile-panic/default.project.json"), "-o", str(place)], cwd=ROOT, capture_output=True, text=True)
    if build.returncode or not place.is_file():
        print("FAIL: build", build.stderr, file=sys.stderr)
        return 1
    cmd = [str(studio), "--task", "RunScript", "--localPlaceFile", str(place), "--runScriptFile", str(ROOT / "tests/roblox/tile_panic_multiplayer_harness.luau"), "--quitAfterExecution"]
    with log.open("w", encoding="utf-8") as output:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            data = log.read_text(encoding="utf-8", errors="replace")
            if MARKER in data or "SF_TILE_MP_RESULT ok=true result=FAIL:" in data or "SF_TILE_MP_RESULT ok=false" in data or "[FLog::CreatorOutput] SF_TILE_MP_FAIL " in data:
                break
            if proc.poll() is not None:
                break
            time.sleep(.4)
    finally:
        if proc.poll() is None:
            try: os.killpg(proc.pid, signal.SIGTERM)
            except (PermissionError, ProcessLookupError):
                try: proc.terminate()
                except (PermissionError, ProcessLookupError): pass
            try: proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                try: os.killpg(proc.pid, signal.SIGKILL)
                except (PermissionError, ProcessLookupError):
                    try: proc.kill()
                    except (PermissionError, ProcessLookupError): pass
    data = log.read_text(encoding="utf-8", errors="replace")
    lines = [line for line in data.splitlines() if "SF_TILE_MP" in line or "[FLog::CreatorError]" in line]
    print("\n".join(lines[-70:]), flush=True)
    passed = MARKER in data and "SF_TILE_MP_RESULT ok=true result=FAIL:" not in data and "[FLog::CreatorError]" not in data
    print(("PASS" if passed else "FAIL") + " | tile-panic two-client boundary", flush=True)
    print("Artifacts:", folder, flush=True)
    if passed and not args.keep_artifacts:
        shutil.rmtree(folder, ignore_errors=True)
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
