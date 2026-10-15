#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts" / "roblox-release"
TARGETS = ROOT / "src" / "roblox" / "publish_targets.json"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {"command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def keychain_present() -> bool:
    p = subprocess.run(["security","find-generic-password","-a","satisfyforge","-s","SatisfyForgeRobloxOpenCloud"], capture_output=True)
    return p.returncode == 0

def load_targets() -> dict:
    try:
        data=json.loads(TARGETS.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def creator_dashboard_authenticated() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=2) as r:
            pages=json.load(r)
        return any(
            p.get("type") == "page" and "create.roblox.com" in p.get("url", "") and "Log in to Roblox" not in p.get("title", "")
            for p in pages
        )
    except Exception:
        return False

def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    static = run([sys.executable, "tests/roblox/validate_brainrot_rush.py"])
    smoke = run([sys.executable, "tools/roblox-studio/run_smoke.py", "--game", "all", "--keep-artifacts"])
    targets = load_targets()
    target_saved = bool(targets.get("snackquake", {}).get("universe_id") and targets.get("snackquake", {}).get("place_id"))
    creator_auth = creator_dashboard_authenticated()
    blockers=[]
    if not target_saved: blockers.append("No verified Roblox universe/place IDs are stored in the repository.")
    if not creator_auth: blockers.append("Creator Dashboard session is not authenticated in the persistent browser profile.")
    blockers.extend([
        "2+ player multiplayer checks are not yet verified.",
        "Live DataStore persistence checks are not yet verified.",
        "Android/iPhone/mobile UX checks are not yet verified.",
        "Owner review of public metadata/content questionnaire is still required before public launch."
    ])
    report = {
        "generated_at": now,
        "static_brainrot": {"passed": static["returncode"] == 0, **static},
        "studio_smoke_all": {"passed": smoke["returncode"] == 0, **smoke},
        "roblox_open_cloud_key_in_keychain": keychain_present(),
        "creator_dashboard_authenticated": creator_auth,
        "publish_target_ids_saved": target_saved,
        "publish_targets": targets,
        "release_blockers": blockers
    }
    out = REPORT_DIR / "latest.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"REPORT={out}")
    print(f"STATIC_BRAINROT={'PASS' if report['static_brainrot']['passed'] else 'FAIL'}")
    print(f"STUDIO_SMOKE_ALL={'PASS' if report['studio_smoke_all']['passed'] else 'FAIL'}")
    print(f"ROBLOX_KEYCHAIN={'PRESENT' if report['roblox_open_cloud_key_in_keychain'] else 'MISSING'}")
    print(f"CREATOR_DASHBOARD={'AUTHENTICATED' if creator_auth else 'NOT_AUTHENTICATED'}")
    print(f"PUBLISH_TARGET_IDS={'PRESENT' if target_saved else 'MISSING'}")
    print(f"BLOCKERS={len(blockers)}")
    return 0 if report['static_brainrot']['passed'] and report['studio_smoke_all']['passed'] else 1

if __name__ == "__main__":
    raise SystemExit(main())
