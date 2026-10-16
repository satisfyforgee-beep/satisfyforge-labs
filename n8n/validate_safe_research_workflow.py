#!/usr/bin/env python3
"""Static safety contract for the inactive SatisfyForge n8n research draft."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_WORKFLOW = ROOT / "SatisfyForge_Operations_Safe_Research_Review_DRAFT.json"
WORKFLOW = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_WORKFLOW
BASE_ID = "appCOTV6T99fj1s2z"
REVIEW_TABLE = "tblwaK5xkOjIbaeN8"
RESEARCH_TABLE = "tblMEiMbaEHYgTS4B"
ALLOWED_TYPES = {
    "n8n-nodes-base.manualTrigger",
    "n8n-nodes-base.code",
    "n8n-nodes-base.airtable",
    "n8n-nodes-base.if",
    "n8n-nodes-base.noOp",
    "n8n-nodes-base.httpRequest",
}
EXPECTED_EDGES = {
    ("Manual Safe Test", 0, "Prepare Safe Input"),
    ("Prepare Safe Input", 0, "Build Safe Payload"),
    ("Build Safe Payload", 0, "Find Existing Review Item"),
    ("Find Existing Review Item", 0, "Find Existing Research Run"),
    ("Find Existing Research Run", 0, "Duplicate?"),
    ("Duplicate?", 0, "Duplicate Stop"),
    ("Duplicate?", 1, "Fetch Public Source"),
    ("Fetch Public Source", 0, "Extract Evidence"),
    ("Extract Evidence", 0, "Write Review Queue"),
    ("Write Review Queue", 0, "Write Research Run"),
    ("Write Research Run", 0, "Hard Stop — No Live Actions"),
}


def fail(msg: str) -> None:
    raise AssertionError(msg)


def table_id(node: dict) -> str | None:
    table = node.get("parameters", {}).get("table")
    return table.get("value") if isinstance(table, dict) else table


def base_id(node: dict) -> str | None:
    base = node.get("parameters", {}).get("base")
    return base.get("value") if isinstance(base, dict) else base


def edges(workflow: dict) -> set[tuple[str, int, str]]:
    out: set[tuple[str, int, str]] = set()
    for source, ports in workflow.get("connections", {}).items():
        for port_index, targets in enumerate(ports.get("main", [])):
            for target in targets:
                out.add((source, port_index, target.get("node")))
    return out


def main() -> int:
    data = json.loads(WORKFLOW.read_text())
    if data.get("active") is not False:
        fail("workflow must remain active:false")

    nodes = data.get("nodes", [])
    by_name = {n.get("name"): n for n in nodes}
    if len(by_name) != len(nodes):
        fail("node names must be unique")

    bad_types = sorted({n.get("type") for n in nodes} - ALLOWED_TYPES)
    if bad_types:
        fail(f"unapproved node types present: {bad_types}")

    triggers = [n for n in nodes if n.get("type") == "n8n-nodes-base.manualTrigger"]
    if [n.get("name") for n in triggers] != ["Manual Safe Test"]:
        fail("manual trigger must be the only trigger")

    credential_nodes = [n.get("name") for n in nodes if n.get("credentials")]
    if credential_nodes:
        fail(f"credential references must not be committed: {credential_nodes}")

    actual_edges = edges(data)
    if actual_edges != EXPECTED_EDGES:
        missing = sorted(EXPECTED_EDGES - actual_edges)
        extra = sorted(actual_edges - EXPECTED_EDGES)
        fail(f"workflow graph changed; missing={missing}; extra={extra}")

    expected_airtable = {
        "Find Existing Review Item": ("search", REVIEW_TABLE),
        "Find Existing Research Run": ("search", RESEARCH_TABLE),
        "Write Review Queue": ("create", REVIEW_TABLE),
        "Write Research Run": ("create", RESEARCH_TABLE),
    }
    airtable_nodes = [n for n in nodes if n.get("type") == "n8n-nodes-base.airtable"]
    if {n.get("name") for n in airtable_nodes} != set(expected_airtable):
        fail("Airtable node set changed")
    for name, (operation, table) in expected_airtable.items():
        node = by_name[name]
        if base_id(node) != BASE_ID or table_id(node) != table:
            fail(f"{name} points outside the approved Airtable base/table")
        if node.get("parameters", {}).get("operation") != operation:
            fail(f"{name} must use Airtable operation {operation}")

    review_formula = by_name["Find Existing Review Item"]["parameters"].get("filterByFormula", "")
    research_formula = by_name["Find Existing Research Run"]["parameters"].get("filterByFormula", "")
    if "{Dedup Key}" not in review_formula or "dedupKey" not in review_formula:
        fail("Review Queue duplicate search must use Dedup Key")
    if "{Research Key}" not in research_formula or "researchKey" not in research_formula:
        fail("Research Runs duplicate search must use Research Key")
    if not by_name["Find Existing Review Item"].get("alwaysOutputData"):
        fail("Review Queue search must always output data for a no-match path")
    if not by_name["Find Existing Research Run"].get("alwaysOutputData"):
        fail("Research Runs search must always output data for a no-match path")

    duplicate_expr = by_name["Duplicate?"]["parameters"]["conditions"]["conditions"][0].get("leftValue", "")
    if "Find Existing Review Item" not in duplicate_expr or "Find Existing Research Run" not in duplicate_expr:
        fail("Duplicate gate must consider both Airtable ledgers")

    prepare = by_name["Prepare Safe Input"]["parameters"].get("jsCode", "")
    for required in ("UNVERIFIED_TEST_ONLY", "identityVerified: false", "liveActionAllowed: false", "freeResourceVerified: true"):
        if required not in prepare:
            fail(f"safe test input lost required marker: {required}")

    build = by_name["Build Safe Payload"]["parameters"].get("jsCode", "")
    for required in ("dedupKey", "researchKey", "queueId", "researchId", "BLOCKED_UNTIL_IDENTITY_AND_REVIEW"):
        if required not in build:
            fail(f"safe payload lost required property: {required}")
    for required in ("SAFE_RESEARCH_SOURCE_REQUIRES_HTTPS", "SAFE_RESEARCH_SOURCE_CREDENTIALS_BLOCKED", "SAFE_RESEARCH_SOURCE_PRIVATE_HOST_BLOCKED", "SAFE_RESEARCH_SOURCE_INVALID_URL"):
        if required not in build:
            fail(f"source URL guard lost required marker: {required}")

    review_fields = by_name["Write Review Queue"]["parameters"]["columns"]["value"]
    if review_fields.get("Live Action Allowed") is not False:
        fail("Review Queue live-action gate must be hard-coded false")
    if review_fields.get("Status") != "Needs Review" or review_fields.get("Workflow") != "Research":
        fail("Review Queue writes must remain Research / Needs Review")
    if not review_fields.get("Account Identity") or not review_fields.get("Dedup Key"):
        fail("Review Queue write must include Account Identity and Dedup Key")

    research_fields = by_name["Write Research Run"]["parameters"]["columns"]["value"]
    for field in ("Research Key", "Account Identity", "Review Queue ID", "n8n Execution ID", "Evidence", "Source URL"):
        if not research_fields.get(field):
            fail(f"Research Run write missing {field}")

    http = by_name["Fetch Public Source"]["parameters"]
    if http.get("method", "GET").upper() != "GET":
        fail("research HTTP node must remain GET-only")
    if "canonicalUrl" not in http.get("url", ""):
        fail("research HTTP node must fetch the canonical source URL")

    terminals = {name for name in by_name if not any(e[0] == name for e in actual_edges)}
    if terminals != {"Duplicate Stop", "Hard Stop — No Live Actions"}:
        fail(f"unexpected terminal nodes: {sorted(terminals)}")

    print("SAFE_N8N_WORKFLOW=PASS")
    print(f"ACTIVE={data.get('active')}")
    print(f"NODES={len(nodes)}")
    print("TRIGGER=Manual Safe Test")
    print("DEDUP=Review Queue + Research Runs")
    print("WRITE_ORDER=Review Queue -> Research Runs -> Hard Stop")
    print("LIVE_ACTION_ALLOWED=false")
    print("CREDENTIAL_REFS=NONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as exc:
        print(f"SAFE_N8N_WORKFLOW=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
