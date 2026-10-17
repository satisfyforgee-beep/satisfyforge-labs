#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PASS = 'SF_SNACK_MOBILE_GATE_PASS'

def critical_creator_errors(text: str) -> list[str]:
    known_editor_noise = ('[Roblox][SelectDragger.SelectDragger.',)
    errors=[]
    for line in text.splitlines():
        if '[FLog::CreatorError]' not in line:
            continue
        if any(token in line for token in known_editor_noise):
            continue
        errors.append(line)
    return errors

def find_studio(explicit=None):
    items=[]
    if explicit: items.append(Path(explicit).expanduser())
    if os.environ.get('ROBLOX_STUDIO'): items.append(Path(os.environ['ROBLOX_STUDIO']).expanduser())
    items.append(Path('/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio'))
    for p in items:
        if p.is_file(): return p
    raise FileNotFoundError('Roblox Studio executable not found')

def find_rojo(explicit=None):
    items=[]
    if explicit: items.append(Path(explicit).expanduser())
    if os.environ.get('ROJO'): items.append(Path(os.environ['ROJO']).expanduser())
    q=shutil.which('rojo')
    if q: items.append(Path(q))
    items.append(Path.home()/'SatisfyForge/tools/rojo/rojo')
    for p in items:
        if p.is_file() and os.access(p, os.X_OK): return p
    raise FileNotFoundError('Rojo executable not found')

def stop_group(p):
    if p.poll() is not None: return
    try: os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError: return
    end=time.monotonic()+4
    while p.poll() is None and time.monotonic()<end: time.sleep(.1)
    if p.poll() is None:
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass

def main(argv=None):
    ap=argparse.ArgumentParser(description='Run Snackquake phone-shaped viewport HUD regression gate')
    ap.add_argument('--studio'); ap.add_argument('--rojo'); ap.add_argument('--keep-artifacts',action='store_true'); ap.add_argument('--timeout',type=int,default=90)
    a=ap.parse_args(argv); studio=find_studio(a.studio); rojo=find_rojo(a.rojo)
    out=Path(tempfile.mkdtemp(prefix='satisfyforge-roblox-mobile-')); place=out/'snackquake.rbxlx'; log=out/'snack-mobile.studio.log'
    b=subprocess.run([str(rojo),'build',str(ROOT/'src/roblox/snackquake/default.project.json'),'-o',str(place)],cwd=ROOT,text=True,capture_output=True)
    if b.returncode or not place.is_file(): print('FAIL | mobile build',file=sys.stderr); return 1
    cmd=[str(studio),'--task','RunScript','--localPlaceFile',str(place),'--runScriptFile',str(ROOT/'tests/roblox/snackquake_mobile_harness.luau'),'--quitAfterExecution']
    with log.open('w',encoding='utf-8',errors='replace') as fh:
        p=subprocess.Popen(cmd,cwd=ROOT,text=True,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+a.timeout; passed=False
    try:
        while time.monotonic()<deadline:
            text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
            if PASS in text: passed=True; break
            if critical_creator_errors(text) or 'mobile gate failed' in text: break
            if p.poll() is not None: break
            time.sleep(.4)
    finally:
        if p.poll() is None: time.sleep(.8); stop_group(p)
    text=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
    lines=[x for x in text.splitlines() if 'SF_SNACK_MOBILE_GATE_' in x or '[FLog::CreatorError]' in x]
    print('\n'.join(lines[-160:]))
    critical=critical_creator_errors(text)
    if critical:
        print('Critical CreatorErrors:\n'+'\n'.join(critical[-20:]))
        passed=False
    print(('PASS' if passed else 'FAIL')+' | snackquake mobile viewport')
    print(f'Artifacts: {out}')
    if passed and not a.keep_artifacts: shutil.rmtree(out,ignore_errors=True)
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
