#!/usr/bin/env python3
"""Run two-player real-engine golden rescue and combo test on a temporary place."""
from __future__ import annotations
import os, subprocess, tempfile, time, sys
from pathlib import Path
from run_smoke import find_studio, find_rojo, build_place, GAMES, _terminate_process_group, _critical_creator_errors
ROOT=Path(__file__).resolve().parents[2]
PASS="SF_SNACK_RUSH_RESULT ok=true result=PASS:snackquake_rescue_rush"
def main():
    studio,rojo=find_studio(None),find_rojo(None)
    out=Path(tempfile.mkdtemp(prefix="satisfyforge-snack-rush-"))
    place=build_place(rojo,GAMES["snackquake"],out)
    log=out/"studio.log"
    cmd=[str(studio),"--task","RunScript","--localPlaceFile",str(place),
         "--runScriptFile",str(ROOT/"tests/roblox/snackquake_rescue_rush_harness.luau"),"--quitAfterExecution"]
    with log.open("w",encoding="utf-8") as fh:
        proc=subprocess.Popen(cmd,cwd=ROOT,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        deadline=time.monotonic()+85
        while time.monotonic()<deadline:
            lines=log.read_text(errors="replace").splitlines()
            if any("[FLog::CreatorOutput] "+PASS in l or "[FLog::CreatorOutput] SF_SNACK_RUSH_FAIL" in l or "[FLog::CreatorOutput] SF_SNACK_RUSH_RESULT ok=" in l for l in lines):
                break
            if proc.poll() is not None: break
            time.sleep(.4)
    finally:
        if proc.poll() is None: _terminate_process_group(proc)
    lines=log.read_text(errors="replace").splitlines()
    for line in lines:
        if "[FLog::CreatorOutput] SF_SNACK_RUSH" in line or "[FLog::CreatorError]" in line:
            print(line)
    passed=any("[FLog::CreatorOutput] "+PASS in l for l in lines) and not _critical_creator_errors("\n".join(lines))
    print(("PASS" if passed else "FAIL")+" | two-player golden rescue and combo")
    print("Artifacts:",out)
    return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
