#!/usr/bin/env python3
"""Offline fail-closed validation for the SatisfyForge direct publisher."""
from __future__ import annotations

import argparse
import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--identity", default=None, help="Expected verified business identity")
    args = parser.parse_args()

    queue = run.load_json(run.QUEUE_PATH, {"items": []})
    history = run.load_json(run.HISTORY_PATH, {})
    run.validate_queue(queue, expected_account_identity=args.identity, history=history)
    print(f"DIRECT_PUBLISHER_PREFLIGHT_OK queue_items={len(queue.get('items', []))}")
    print(f"blocked_concepts={len(history.get('blocked_concepts', []))}")
    print(f"completed_concepts={len(history.get('completed_concepts', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
