#!/usr/bin/env python3
"""Fail CI if quarantined or unverified checkouts reach operational surfaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEXT_SUFFIXES = {".html", ".md", ".txt", ".json", ".py", ".js", ".ts", ".tsx", ".yml", ".yaml"}
OPERATIONAL_ROOTS = ("satisfyforge-site", "publisher", "sales")


def load_blocked_product_ids(registry_path: Path) -> set[str]:
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return {
        item["product_id"]
        for item in data.get("checkouts", [])
        if item.get("status") != "verified"
    }


def scan_operational_surfaces(repo_root: Path, registry_path: Path | None = None) -> list[str]:
    registry_path = registry_path or repo_root / "commerce" / "checkout_registry.json"
    blocked_ids = load_blocked_product_ids(registry_path)
    blocked_tokens = {f"payhip.com/b/{product_id}" for product_id in blocked_ids}
    violations: list[str] = []

    for root_name in OPERATIONAL_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in sorted(blocked_tokens):
                if token in text:
                    violations.append(f"{path.relative_to(repo_root)} contains blocked checkout {token}")

    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    violations = scan_operational_surfaces(repo_root)
    if violations:
        print("Commerce safety validation failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1
    print("Commerce safety validation passed: no quarantined checkout links on operational surfaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
