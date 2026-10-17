#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts" / "roblox-release"
TARGETS = ROOT / "src" / "roblox" / "publish_targets.json"
PERSISTENCE_EVIDENCE = ROOT / "tests" / "roblox" / "brainrot_persistence_evidence.json"
BRAINROT_SERVER = ROOT / "src" / "roblox" / "BrainrotRush.server.lua"
BRAINROT_CLIENT = ROOT / "src" / "roblox" / "BrainrotRush.client.lua"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {"command": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

def keychain_present() -> bool:
    p = subprocess.run(["security","find-generic-password","-a","satisfyforge","-s","SatisfyForgeRobloxOpenCloud"], capture_output=True)
    return p.returncode == 0

def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
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

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_live_persistence(targets: dict) -> dict:
    evidence = load_json(PERSISTENCE_EVIDENCE)
    qa = targets.get("brainrot_rush_qa", {})
    current_hashes = {"server": sha256(BRAINROT_SERVER), "client": sha256(BRAINROT_CLIENT)}
    reasons: list[str] = []
    if not evidence:
        reasons.append("persistence evidence file is missing or invalid")
    if evidence.get("passed") is not True:
        reasons.append("evidence is not marked passed")
    if evidence.get("cleanup_restored_nil") is not True:
        reasons.append("QA test record cleanup was not verified")
    if evidence.get("universe_id") != qa.get("universe_id") or evidence.get("place_id") != qa.get("place_id"):
        reasons.append("evidence target IDs do not match the saved private QA target")
    if evidence.get("source_sha256") != current_hashes:
        reasons.append("Brainrot Rush source changed after the live persistence verification")
    before = evidence.get("before", {})
    after = evidence.get("after_gameplay_touch", {})
    rejoin = evidence.get("after_rejoin", {})
    if not (after.get("Brainrot", 0) > before.get("Brainrot", 0) and after.get("Collected", 0) > before.get("Collected", 0)):
        reasons.append("evidence does not show progression earned through gameplay")
    if any(rejoin.get(k) != after.get(k) for k in ("Brainrot", "Collected", "Level", "Rebirths")):
        reasons.append("rejoin values do not match the values saved before leaving")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "evidence_file": str(PERSISTENCE_EVIDENCE.relative_to(ROOT)),
        "verified_at": evidence.get("verified_at"),
        "universe_id": evidence.get("universe_id"),
        "place_id": evidence.get("place_id"),
        "current_source_sha256": current_hashes,
        "verified_source_sha256": evidence.get("source_sha256", {}),
        "before": before,
        "after_gameplay_touch": after,
        "after_rejoin": rejoin,
        "cleanup_restored_nil": evidence.get("cleanup_restored_nil") is True,
    }

def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    static = run([sys.executable, "tests/roblox/validate_brainrot_rush.py"])
    smoke = run([sys.executable, "tools/roblox-studio/run_smoke.py", "--game", "all", "--keep-artifacts"])
    multiplayer = run([sys.executable, "tools/roblox-studio/run_multiplayer.py"])
    mobile = run([sys.executable, "tools/roblox-studio/run_mobile.py"])
    tile_multiplayer = run([sys.executable, "tools/roblox-studio/run_tile_multiplayer.py"])
    snackquake_multiplayer = run([sys.executable, "tools/roblox-studio/run_snack_multiplayer.py"])
    snackquake_unit = run([sys.executable, "src/roblox/snackquake/tests/run_tests.py"])
    targets = load_json(TARGETS)
    target_saved = all(
        targets.get(name, {}).get("universe_id") and targets.get(name, {}).get("place_id")
        for name in ("snackquake", "brainrot_rush_qa")
    )
    tile_target_saved = bool(targets.get("tile_panic", {}).get("universe_id") and targets.get("tile_panic", {}).get("place_id"))
    creator_auth = creator_dashboard_authenticated()
    persistence = validate_live_persistence(targets)
    blockers=[]
    automation_warnings=[]
    if not target_saved:
        blockers.append("Verified Snackquake/Brainrot Rush QA universe/place IDs are missing from the repository.")
    if not tile_target_saved:
        blockers.append("Tile Panic has no verified private Roblox universe/place target; uploads remain blocked.")
    if not creator_auth:
        automation_warnings.append("Creator Dashboard browser session is not authenticated; Studio remains the current authenticated QA path.")
    if multiplayer["returncode"] != 0:
        blockers.append("Automated Brainrot Rush two-client multiplayer behavior gate is not passing reliably.")
    if tile_multiplayer["returncode"] != 0:
        blockers.append("Automated Tile Panic two-client lobby-escape regression is not passing.")
    if snackquake_multiplayer["returncode"] != 0:
        blockers.append("Automated Snackquake two-client action isolation gate is not passing.")
    if snackquake_unit["returncode"] != 0:
        blockers.append("Snackquake pure-rules or persistence regression suite is not passing.")
    if not persistence["passed"]:
        blockers.append("Live DataStore persistence evidence is missing, stale, or does not match the current Brainrot Rush source.")
    if mobile["returncode"] == 0:
        blockers.append("Automated iPhone/Galaxy portrait+landscape HUD bounds pass, but real-device touch-control comfort and physical Android/iPhone UX are not yet verified.")
    else:
        blockers.append("Automated phone-shaped portrait/landscape HUD regression gate is not passing.")
    blockers.append("Snackquake: live save/rejoin, full rescue-loop, physical mobile UX and performance gates remain unverified.")
    blockers.append("Tile Panic: full 18-wave reward/persistence flow, physical mobile UX and performance gates remain unverified.")
    blockers.append("Owner review of public metadata/content questionnaire is still required before public launch.")
    report = {
        "generated_at": now,
        "static_brainrot": {"passed": static["returncode"] == 0, **static},
        "studio_smoke_all": {"passed": smoke["returncode"] == 0, **smoke},
        "brainrot_multiplayer_behavior": {"passed": multiplayer["returncode"] == 0, **multiplayer},
        "brainrot_mobile_viewport": {"passed": mobile["returncode"] == 0, **mobile},
        "tile_panic_multiplayer_boundary": {"passed": tile_multiplayer["returncode"] == 0, **tile_multiplayer},
        "snackquake_multiplayer_actions": {"passed": snackquake_multiplayer["returncode"] == 0, **snackquake_multiplayer},
        "snackquake_unit_regressions": {"passed": snackquake_unit["returncode"] == 0, **snackquake_unit},
        "brainrot_live_persistence": persistence,
        "roblox_open_cloud_key_in_keychain": keychain_present(),
        "creator_dashboard_authenticated": creator_auth,
        "publish_target_ids_saved": target_saved,
        "tile_panic_publish_target_saved": tile_target_saved,
        "publish_targets": targets,
        "automation_warnings": automation_warnings,
        "release_blockers": blockers,
    }
    out = REPORT_DIR / "latest.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"REPORT={out}")
    print(f"STATIC_BRAINROT={'PASS' if report['static_brainrot']['passed'] else 'FAIL'}")
    print(f"STUDIO_SMOKE_ALL={'PASS' if report['studio_smoke_all']['passed'] else 'FAIL'}")
    print(f"BRAINROT_MULTIPLAYER_BEHAVIOR={'PASS' if report['brainrot_multiplayer_behavior']['passed'] else 'FAIL'}")
    print(f"BRAINROT_MOBILE_VIEWPORT={'PASS' if report['brainrot_mobile_viewport']['passed'] else 'FAIL'}")
    print(f"TILE_PANIC_MULTIPLAYER={'PASS' if report['tile_panic_multiplayer_boundary']['passed'] else 'FAIL'}")
    print(f"SNACKQUAKE_MULTIPLAYER={'PASS' if report['snackquake_multiplayer_actions']['passed'] else 'FAIL'}")
    print(f"SNACKQUAKE_UNIT={'PASS' if report['snackquake_unit_regressions']['passed'] else 'FAIL'}")
    print(f"BRAINROT_LIVE_PERSISTENCE={'PASS' if persistence['passed'] else 'FAIL'}")
    print(f"ROBLOX_KEYCHAIN={'PRESENT' if report['roblox_open_cloud_key_in_keychain'] else 'MISSING'}")
    print(f"CREATOR_DASHBOARD={'AUTHENTICATED' if creator_auth else 'NOT_AUTHENTICATED'}")
    print(f"PUBLISH_TARGET_IDS={'PRESENT' if target_saved else 'MISSING'}")
    print(f"TILE_PANIC_PUBLISH_TARGET={'PRESENT' if tile_target_saved else 'MISSING'}")
    print(f"AUTOMATION_WARNINGS={len(automation_warnings)}")
    print(f"BLOCKERS={len(blockers)}")
    return 0 if all((
        report['static_brainrot']['passed'],
        report['studio_smoke_all']['passed'],
        report['brainrot_multiplayer_behavior']['passed'],
        report['brainrot_mobile_viewport']['passed'],
        report['tile_panic_multiplayer_boundary']['passed'],
        report['snackquake_multiplayer_actions']['passed'],
        report['snackquake_unit_regressions']['passed'],
        persistence['passed'],
    )) else 1

if __name__ == "__main__":
    raise SystemExit(main())
