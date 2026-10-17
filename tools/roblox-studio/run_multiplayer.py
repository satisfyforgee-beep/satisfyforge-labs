#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PASS_RESULT = "SF_MP_PROBE_RESULT ok=true result=PASS:multiplayer_behavior"
FAIL_RESULT = "SF_MP_PROBE_RESULT ok=true result=FAIL:"


def find_studio(explicit: str | None) -> Path:
    candidates=[]
    if explicit: candidates.append(Path(explicit).expanduser())
    if os.environ.get("ROBLOX_STUDIO"): candidates.append(Path(os.environ["ROBLOX_STUDIO"]).expanduser())
    candidates.append(Path('/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio'))
    for p in candidates:
        if p.is_file(): return p
    raise FileNotFoundError('Roblox Studio executable not found')


def find_rojo(explicit: str | None) -> Path:
    candidates=[]
    if explicit: candidates.append(Path(explicit).expanduser())
    if os.environ.get('ROJO'): candidates.append(Path(os.environ['ROJO']).expanduser())
    q=shutil.which('rojo')
    if q: candidates.append(Path(q))
    candidates.append(Path.home()/'SatisfyForge/tools/rojo/rojo')
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK): return p
    raise FileNotFoundError('Rojo executable not found')


def stop_group(proc: subprocess.Popen) -> None:
    if proc.poll() is not None: return
    try: os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError: return
    except PermissionError:
        try: proc.terminate()
        except (ProcessLookupError, PermissionError): return
    deadline=time.monotonic()+4
    while proc.poll() is None and time.monotonic()<deadline: time.sleep(0.1)
    if proc.poll() is None:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        except PermissionError:
            try: proc.kill()
            except (ProcessLookupError, PermissionError): pass


def one_attempt(studio: Path, place: Path, log: Path, timeout: int) -> tuple[bool,str]:
    cmd=[str(studio),'--task','RunScript','--localPlaceFile',str(place),'--runScriptFile',str(ROOT/'tests/roblox/brainrot_multiplayer_harness.luau'),'--quitAfterExecution']
    with log.open('w', encoding='utf-8', errors='replace') as fh:
        proc=subprocess.Popen(cmd,cwd=ROOT,text=True,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+timeout
    result=''
    try:
        while time.monotonic()<deadline:
            text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
            creator_errors=[line for line in text.splitlines() if '[FLog::CreatorError]' in line and 'Server Kick Message: SatisfyForge automated leave-isolation test' not in line]
            if creator_errors:
                result='creator_error'; break
            if PASS_RESULT in text:
                result='pass'; break
            if FAIL_RESULT in text:
                result='one_player'; break
            if proc.poll() is not None:
                result='exited'; break
            time.sleep(0.4)
        if not result: result='timeout'
    finally:
        if proc.poll() is None:
            time.sleep(1)
            stop_group(proc)
    text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
    interesting=[x for x in text.splitlines() if 'SF_MP_' in x or '[FLog::CreatorError]' in x]
    print('\n'.join(interesting[-120:]), flush=True)
    return result=='pass', result


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Run Brainrot Rush two-client Studio multiplayer gate')
    ap.add_argument('--studio'); ap.add_argument('--rojo'); ap.add_argument('--keep-artifacts',action='store_true')
    ap.add_argument('--attempts',type=int,default=2); ap.add_argument('--timeout',type=int,default=60)
    args=ap.parse_args(argv)
    studio=find_studio(args.studio); rojo=find_rojo(args.rojo)
    out=Path(tempfile.mkdtemp(prefix='satisfyforge-roblox-multiplayer-'))
    place=out/'brainrot-rush.rbxlx'
    b=subprocess.run([str(rojo),'build',str(ROOT/'src/roblox/BrainrotRush.project.json'),'-o',str(place)],cwd=ROOT,text=True,capture_output=True)
    if b.returncode != 0 or not place.is_file():
        print('FAIL | multiplayer build',file=sys.stderr); return 1
    passed=False
    reasons=[]
    for attempt in range(1,max(1,args.attempts)+1):
        print(f'=== multiplayer attempt {attempt}/{max(1,args.attempts)} ===', flush=True)
        ok, reason=one_attempt(studio,place,out/f'brainrot-multiplayer-attempt-{attempt}.studio.log',args.timeout)
        reasons.append(reason)
        if ok:
            passed=True; break
        if reason=='creator_error': break
        time.sleep(2)
    print(('PASS' if passed else 'FAIL')+' | brainrot-rush multiplayer')
    print('Attempt results: '+', '.join(reasons))
    print(f'Artifacts: {out}')
    if not args.keep_artifacts and passed: shutil.rmtree(out,ignore_errors=True)
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
