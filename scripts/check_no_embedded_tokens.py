#!/usr/bin/env python3
"""Fail closed when obvious credential material is committed.

This scanner reports only the file and rule name, never the matching value.
It intentionally scans Git-tracked files and skips binary content.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

RULES = {
    "Meta access token": re.compile(rb"\bEAA[A-Za-z0-9]{80,}\b"),
    "GitHub personal token": re.compile(rb"\b(?:ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "Google API key": re.compile(rb"\bAIza[A-Za-z0-9_-]{30,}\b"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Private key block": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Literal publisher secret": re.compile(
        rb"(?i)\b(?:META_ACCESS_TOKEN|META_FB_PAGE_ACCESS_TOKEN|GOOGLE_CLIENT_SECRET|"
        rb"GOOGLE_REFRESH_TOKEN|TIKTOK_ACCESS_TOKEN)\b\s*[:=]\s*['\"]"
        rb"[A-Za-z0-9._~+/-]{24,}['\"]"
    ),
}

SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".pdf", ".zip",
    ".woff", ".woff2", ".ttf", ".ico", ".rbxlx",
}


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z"], stderr=subprocess.DEVNULL
    )
    return [ROOT / p.decode("utf-8") for p in raw.split(b"\0") if p]


def main() -> int:
    findings: list[tuple[str, str]] = []
    for path in tracked_files():
        if path.resolve() == SELF or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            continue
        for rule_name, pattern in RULES.items():
            if pattern.search(data):
                findings.append((str(path.relative_to(ROOT)), rule_name))

    if findings:
        print("Credential guard failed. Remove or rotate the detected secret material.")
        for filename, rule_name in findings:
            print(f"- {filename}: {rule_name}")
        print("Only secret names/placeholders belong in Git; values belong in GitHub Actions Secrets.")
        return 1

    print("Credential guard passed: no obvious embedded credential material found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
