#!/usr/bin/env python3
"""Static fail-closed contract for SatisfyForge cloud-browser mutations."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BR = ROOT / "browser-runner"
WF = ROOT / ".github" / "workflows"


def fail(message):
    raise AssertionError(message)


def main():
    job = json.loads((BR / "job.json").read_text())
    if job.get("allowMutations") is not False:
        fail("committed browser job must default allowMutations=false")

    runner = (BR / "src" / "runner.mjs").read_text()
    for marker in [
        'process.env.SF_MUTATIONS_ARMED || "false"',
        "mutationTasks.has(taskName)",
        "taskIsMutation && !allowMutations",
        "taskIsMutation && !mutationsArmed",
        'code: "MUTATIONS_NOT_ARMED"',
    ]:
        if marker not in runner:
            fail("runner lost mutation guard: " + marker)

    tasks = (BR / "src" / "tasks.mjs").read_text()
    registry = re.search(r"export const mutationTasks\s*=\s*new Set\(\[(.*?)\]\);", tasks, re.S)
    if not registry:
        fail("tasks.mjs must export mutationTasks")
    declared = set(re.findall(r'"([^"]+)"', registry.group(1)))
    headers = re.findall(r'async\s+"([^"]+)"\s*\(\{([^}]*)\}\)', tasks)
    signature_mutations = {name for name, args in headers if "allowMutations" in args}
    if declared != signature_mutations:
        fail(f"mutation registry mismatch: {sorted(declared)} != {sorted(signature_mutations)}")
    if not declared:
        fail("no mutation tasks registered")

    expected = {
        "satisfyforge-cloud-browser-issues.yml",
        "satisfyforge-cloud-browser.yml",
        "satisfyforge-control-worker.yml",
    }
    seen = set()
    for path in WF.glob("*.yml"):
        text = path.read_text()
        if "node src/runner.mjs" not in text:
            continue
        seen.add(path.name)
        if 'SF_MUTATIONS_ARMED: ${{ vars.SF_BROWSER_MUTATIONS_ARMED }}' not in text:
            fail(path.name + " can run browser tasks without repository mutation arm")
    if seen != expected:
        fail(f"browser-runner workflow set changed: {sorted(seen)}")

    print("BROWSER_MUTATION_SAFETY=PASS")
    print("DEFAULT_ALLOW_MUTATIONS=false")
    print("REPOSITORY_ARM=SF_BROWSER_MUTATIONS_ARMED")
    print("MUTATION_TASKS=" + ",".join(sorted(declared)))


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, json.JSONDecodeError) as exc:
        print("BROWSER_MUTATION_SAFETY=FAIL:", exc)
        raise SystemExit(1)
