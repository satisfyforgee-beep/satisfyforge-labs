#!/usr/bin/env python3
"""Build and runtime-smoke SatisfyForge Roblox places through Roblox Studio CLI.

This uses Roblox Studio's documented RunScript task, so runtime checks are executed
by the Roblox engine rather than a generic Lua interpreter.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class GameSpec:
    key: str
    project: Path
    smoke: Path
    pass_marker: str


GAMES = {
    "brainrot-rush": GameSpec(
        "brainrot-rush",
        ROOT / "src/roblox/BrainrotRush.project.json",
        ROOT / "tests/roblox/brainrot_runtime_smoke.luau",
        "SF_SMOKE_PASS BrainrotRush",
    ),
    "tile-panic": GameSpec(
        "tile-panic",
        ROOT / "src/roblox/tile-panic/default.project.json",
        ROOT / "tests/roblox/tile_panic_runtime_smoke.luau",
        "SF_SMOKE_PASS TilePanic",
    ),
    "snackquake": GameSpec(
        "snackquake",
        ROOT / "src/roblox/snackquake/default.project.json",
        ROOT / "tests/roblox/snackquake_runtime_smoke.luau",
        "SF_SMOKE_PASS Snackquake",
    ),
}


def find_studio(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env = os.environ.get("ROBLOX_STUDIO")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path("/Applications/RobloxStudio.app/Contents/MacOS/RobloxStudio"))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Roblox Studio executable not found; use --studio or ROBLOX_STUDIO")


def find_rojo(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env = os.environ.get("ROJO")
    if env:
        candidates.append(Path(env).expanduser())
    on_path = shutil.which("rojo")
    if on_path:
        candidates.append(Path(on_path))
    candidates.append(Path.home() / "SatisfyForge/tools/rojo/rojo")
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError("Rojo executable not found; use --rojo or ROJO")


def run_checked(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


def build_place(rojo: Path, spec: GameSpec, out_dir: Path) -> Path:
    place = out_dir / f"{spec.key}.rbxlx"
    result = run_checked([str(rojo), "build", str(spec.project), "-o", str(place)], cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Rojo build failed for {spec.key}:\n{result.stdout}\n{result.stderr}")
    if not place.is_file() or place.stat().st_size == 0:
        raise RuntimeError(f"Rojo reported success but no place was built for {spec.key}")
    return place


def runtime_smoke(studio: Path, spec: GameSpec, place: Path, out_dir: Path) -> tuple[bool, str]:
    log_path = out_dir / f"{spec.key}.studio.log"
    command = [
        str(studio),
        "--task", "RunScript",
        "--localPlaceFile", str(place),
        "--runScriptFile", str(spec.smoke),
        "--quitAfterExecution",
    ]
    result = run_checked(command)
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    log_path.write_text(combined, encoding="utf-8", errors="replace")

    creator_errors = [line for line in combined.splitlines() if "[FLog::CreatorError]" in line]
    passed = spec.pass_marker in combined and not creator_errors and result.returncode == 0

    interesting = []
    for line in combined.splitlines():
        if any(token in line for token in ("SF_SMOKE", "CreatorError", "CreatorWarning")):
            interesting.append(line)
    summary = "\n".join(interesting[-120:])
    if not summary:
        summary = f"No SatisfyForge smoke markers found. Full log: {log_path}"
    return passed, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SatisfyForge Roblox Studio runtime smoke tests")
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--studio", help="Path to RobloxStudio executable")
    parser.add_argument("--rojo", help="Path to Rojo executable")
    parser.add_argument("--keep-artifacts", action="store_true")
    args = parser.parse_args(argv)

    studio = find_studio(args.studio)
    rojo = find_rojo(args.rojo)
    selected = list(GAMES.values()) if args.game == "all" else [GAMES[args.game]]

    base_tmp = Path(tempfile.mkdtemp(prefix="satisfyforge-roblox-smoke-"))
    failures = 0
    try:
        for spec in selected:
            print(f"=== {spec.key}: build ===", flush=True)
            place = build_place(rojo, spec, base_tmp)
            print(f"built {place} ({place.stat().st_size} bytes)", flush=True)
            print(f"=== {spec.key}: Roblox Studio runtime smoke ===", flush=True)
            passed, summary = runtime_smoke(studio, spec, place, base_tmp)
            print(summary, flush=True)
            print(("PASS" if passed else "FAIL") + f" | {spec.key}", flush=True)
            if not passed:
                failures += 1
        print(f"Artifacts: {base_tmp}", flush=True)
        return 1 if failures else 0
    finally:
        if not args.keep_artifacts and failures == 0:
            shutil.rmtree(base_tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
