#!/usr/bin/env python3
"""Run real Roblox Studio two-client tests for Rift Raiders."""
import subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run_smoke import find_rojo,run_checked,_terminate_process_group,_critical_creator_errors
ROOT=Path(__file__).resolve().parents[2]
def main():
 output=Path(tempfile.mkdtemp(prefix="satisfyforge-rift-mp-"))
 place=output/"rift.rbxlx"
 log=output/"studio.log"
 result=run_checked([str(find_rojo(None)),"build",
  str(ROOT/"src/roblox/rift-raiders/default.project.json"),"-o",str(place)],cwd=ROOT)
 if result.returncode: raise RuntimeError(result.stdout+"\n"+result.stderr)
 cmd=["/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio",
  "--task","RunScript","--localPlaceFile",str(place),
  "--runScriptFile",str(ROOT/"tests/roblox/rift_raiders_multiplayer.luau"),
  "--quitAfterExecution"]
 with log.open("w") as out:
  proc=subprocess.Popen(cmd,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 try:
  for _ in range(140):
   data=log.read_text(errors="replace")
   if "[FLog::CreatorOutput] SF_RIFT_MP_PASS" in data or "[FLog::CreatorOutput] SF_RIFT_MP_RESULT" in data or "[FLog::CreatorOutput] SF_RIFT_MP_FAIL" in data:break
   if proc.poll() is not None:break
   time.sleep(.5)
 finally:
  if proc.poll() is None:_terminate_process_group(proc)
 data=log.read_text(errors="replace")
 for line in data.splitlines():
  if "[FLog::CreatorOutput] SF_RIFT_MP" in line or "[FLog::CreatorError]" in line:print(line[-800:])
 print("LOG",log)
 ok=("SF_RIFT_MP_PASS" in data and "SF_RIFT_MP_RESULT ok=true result=PASS:rift_multiplayer" in data and not _critical_creator_errors(data))
 print("RIFT_MULTIPLAYER_"+("PASS" if ok else "FAIL"))
 return 0 if ok else 1
if __name__=="__main__":raise SystemExit(main())
