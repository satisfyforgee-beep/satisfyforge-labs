#!/usr/bin/env python3
"""Real Roblox Studio two-client test for Hyper Mutation Rush."""
from __future__ import annotations
import subprocess, tempfile, time, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_smoke import _terminate_process_group, _critical_creator_errors, find_rojo, run_checked
ROOT=Path(__file__).resolve().parents[2]
def main():
 out=Path(tempfile.mkdtemp(prefix="satisfyforge-mutation-mp-"))
 log=out/"studio.log"
 place=out/"mutation.rbxlx"
 result=run_checked([str(find_rojo(None)),"build",str(ROOT/"src/roblox/hyper-mutation-rush/default.project.json"),"-o",str(place)],cwd=ROOT)
 if result.returncode: raise RuntimeError(result.stderr or result.stdout)
 cmd=["/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio",
      "--task","RunScript","--localPlaceFile",str(place),
      "--runScriptFile",str(ROOT/"tests/roblox/hyper_mutation_multiplayer_harness.luau"),
      "--quitAfterExecution"]
 with log.open("w") as f: proc=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  for _ in range(160):
   data=log.read_text(errors="replace")
   if "[FLog::CreatorOutput] SF_MUTATION_MP_PASS" in data or "[FLog::CreatorOutput] SF_MUTATION_MP_RESULT" in data or "[FLog::CreatorOutput] SF_MUTATION_MP_FAIL" in data:break
   if proc.poll() is not None:break
   time.sleep(.5)
 finally:
  if proc.poll() is None:_terminate_process_group(proc)
 data=log.read_text(errors="replace")
 for line in data.splitlines():
  if "[FLog::CreatorOutput] SF_MUTATION_MP" in line or "[FLog::CreatorError]" in line:print(line[-800:])
 print("LOG",log)
 ok=(("[FLog::CreatorOutput] SF_MUTATION_MP_PASS" in data or "SF_MUTATION_MP_RESULT ok=true result=PASS:mutation_multiplayer" in data) and "[FLog::CreatorOutput] SF_MUTATION_MP_SERVER_PASS" in data and not _critical_creator_errors(data))
 print("MUTATION_MULTIPLAYER_"+("PASS" if ok else "FAIL"))
 return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())
