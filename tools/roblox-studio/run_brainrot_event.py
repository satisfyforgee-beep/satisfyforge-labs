#!/usr/bin/env python3
"""Run accelerated real-engine Brainrot event/cap/refill QA without changing release sources."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from run_multiplayer import find_studio, find_rojo, stop_group

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "src/roblox/BrainrotRush.server.lua"
CLIENT = ROOT / "src/roblox/BrainrotRush.client.lua"
HARNESS = ROOT / "tests/roblox/brainrot_event_lifecycle_harness.luau"
PASS = "SF_EVENT_PROBE_RESULT ok=true result=PASS:event_lifecycle"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=65)
    ap.add_argument("--keep-artifacts", action="store_true")
    args = ap.parse_args()
    studio, rojo = find_studio(None), find_rojo(None)
    original = SERVER.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    temp = Path(tempfile.mkdtemp(prefix="satisfyforge-brainrot-event-"))
    source = original.decode("utf-8")
    edits = {
        "local MAX_ORBS = 34": "local MAX_ORBS = 12",
        "local BASE_SPAWN_DELAY = 1.35": "local BASE_SPAWN_DELAY = 0.12",
        "local SNACKQUAKE_EVERY = 90": "local SNACKQUAKE_EVERY = 6",
        "local SNACKQUAKE_DURATION = 20": "local SNACKQUAKE_DURATION = 5",
    }
    for old, new in edits.items():
        if source.count(old) != 1:
            print(f"FAIL | expected one occurrence of {old!r}", file=sys.stderr)
            return 1
        source = source.replace(old, new)
    (temp / "Server.server.lua").write_text(source)
    (temp / "Client.client.lua").write_bytes(CLIENT.read_bytes())
    project = {
        "name": "BrainrotRushAcceleratedQA",
        "tree": {"$className": "DataModel",
            "ServerScriptService": {"$className": "ServerScriptService",
                "BrainrotRush": {"$path": "Server.server.lua"}},
            "StarterPlayer": {"$className": "StarterPlayer",
                "StarterPlayerScripts": {"$className": "StarterPlayerScripts",
                    "BrainrotRushHUD": {"$path": "Client.client.lua"}}}}}
    (temp / "default.project.json").write_text(json.dumps(project))
    place = temp / "brainrot-event-qa.rbxlx"
    build = subprocess.run([str(rojo), "build", str(temp / "default.project.json"), "-o", str(place)],
                           cwd=ROOT, text=True, capture_output=True)
    if build.returncode != 0 or not place.exists():
        print("FAIL | Rojo build", build.stdout, build.stderr)
        return 1
    log = temp / "studio.log"
    cmd = [str(studio), "--task", "RunScript", "--localPlaceFile", str(place),
           "--runScriptFile", str(HARNESS), "--quitAfterExecution"]
    with log.open("w") as fh:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT,
                                start_new_session=True)
    try:
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            contents = log.read_text(errors="replace")
            if any("[FLog::CreatorOutput] " + PASS in line or "[FLog::CreatorOutput] SF_EVENT_PROBE_RESULT ok=" in line or "[FLog::CreatorOutput] SF_EVENT_FAIL" in line for line in contents.splitlines()):
                break
            if proc.poll() is not None:
                break
            time.sleep(0.3)
    finally:
        if proc.poll() is None:
            time.sleep(0.5)
            stop_group(proc)
    contents = log.read_text(errors="replace")
    lines = [line for line in contents.splitlines()
             if "SF_EVENT_" in line or "[FLog::CreatorError]" in line]
    print("\n".join(lines[-40:]), flush=True)
    after = hashlib.sha256(SERVER.read_bytes()).hexdigest()
    passed = any("[FLog::CreatorOutput] " + PASS in line for line in contents.splitlines()) and not any("[FLog::CreatorOutput] SF_EVENT_FAIL" in line for line in contents.splitlines()) and before == after
    print(f"{'PASS' if passed else 'FAIL'} | accelerated event lifecycle / orb cap / cleanup")
    print(f"Release source unchanged: {before == after} ({before[:12]})")
    print(f"QA artifacts: {temp}")
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
