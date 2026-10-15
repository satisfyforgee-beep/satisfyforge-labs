#!/usr/bin/env python3
"""Build and runtime-smoke SatisfyForge Roblox places through Roblox Studio CLI.

This uses Roblox Studio's documented RunScript task, so runtime checks are executed
by the Roblox engine rather than a generic Lua interpreter.
"""
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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


def _critical_creator_errors(text: str) -> list[str]:
    # Roblox Studio occasionally emits errors from its own editor plugins while the
    # tested place is healthy. Ignore only this exact Roblox-owned SelectDragger
    # signature; every other CreatorError remains release-blocking.
    known_editor_noise = ("[Roblox][SelectDragger.SelectDragger.",)
    errors: list[str] = []
    for line in text.splitlines():
        if "[FLog::CreatorError]" not in line:
            continue
        if any(token in line for token in known_editor_noise):
            continue
        errors.append(line)
    return errors


def _terminate_process_group(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 4.0
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.1)
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def runtime_smoke(studio: Path, spec: GameSpec, place: Path, out_dir: Path) -> tuple[bool, str]:
    log_path = out_dir / f"{spec.key}.studio.log"
    command = [
        str(studio),
        "--task", "RunScript",
        "--localPlaceFile", str(place),
        "--runScriptFile", str(spec.smoke),
        "--quitAfterExecution",
    ]

    # Write Studio output directly to a file rather than capture_output. Some Studio
    # child processes inherit captured pipes and can keep Python waiting after the
    # smoke script has already emitted its explicit PASS marker. Polling the log and
    # terminating only this spawned process group makes the gate bounded and leaves
    # the user's normal Studio sessions untouched.
    with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
        proc = subprocess.Popen(
            command,
            cwd=ROOT,
            text=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    timeout_seconds = 45.0
    deadline = time.monotonic() + timeout_seconds
    saw_pass = False
    timed_out = False
    try:
        while time.monotonic() < deadline:
            combined = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            if _critical_creator_errors(combined):
                break
            if spec.pass_marker in combined:
                saw_pass = True
                # Give Studio a brief chance to shut down normally, then clean up
                # the CLI test group if it lingers.
                time.sleep(0.8)
                break
            if proc.poll() is not None:
                break
            time.sleep(0.25)
        else:
            timed_out = True
    finally:
        if proc.poll() is None:
            _terminate_process_group(proc)

    combined = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    creator_errors = _critical_creator_errors(combined)
    saw_pass = saw_pass or spec.pass_marker in combined
    passed = saw_pass and not creator_errors and not timed_out

    interesting = []
    for line in combined.splitlines():
        if any(token in line for token in ("SF_SMOKE", "CreatorError", "CreatorWarning")):
            interesting.append(line)
    if timed_out:
        interesting.append(f"SMOKE_TIMEOUT after {timeout_seconds:.0f}s")
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
