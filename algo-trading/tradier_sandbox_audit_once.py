#!/usr/bin/env python3
"""ONE-TIME READ-ONLY Tradier sandbox brokerage reconciliation.

This script uses ONLY Tradier SANDBOX GET endpoints. It never POSTs,
modifies, cancels, or creates ANY paper/live order. It redacts:
tokens, account/order identifiers, client tags, names and raw responses.
Reports order states, checked fields, SOFI position and schema flags
needed to investigate a potentially existing 2026-10-21 OTOCO trade.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import sys

from zerocost_bot.tradier_paper import TradierSandbox, _choose_account

_STATES = {"pending", "open", "partially_filled", "filled", "rejected",
           "expired", "canceled", "pending_cancel", "error"}
_TYPES = {"market", "limit", "stop", "stop_limit", "debit", "credit", "even"}
_SIDES = {"buy", "sell", "buy_to_open", "sell_to_close",
          "buy_to_close", "sell_to_open", "sell_short", "buy_to_cover"}
_CLASSES = {"equity", "otoco", "oco", "oto", "option", "multileg", "combo"}
_SAFE_DETAIL_KEYS = frozenset((
    "status", "side", "type", "class", "quantity", "exec_quantity",
    "remaining_quantity", "symbol", "price", "stop", "order",
    "parent_id", "parent_order_id", "avg_fill_price", "tag",
    "create_date", "duration", "errors", "error", "legs",
    "result", "partner_id", "leg", "num_legs",
))


def _enum(value, options):
    return value if isinstance(value, str) and value in options else "unknown"


def _quantity(value):
    if isinstance(value, bool):
        return "unknown"
    try:
        n = Decimal(str(value))
        if not n.is_finite() or n < 0:
            return "unknown"
        if n == 0:
            return "zero"
        if n == 1:
            return "one"
        return "multiple"
    except (InvalidOperation, TypeError, ValueError):
        return "unknown"


def _listify_envelope(root, key, member):
    """Return records and a safe envelope-shape label; no raw fields."""
    if not isinstance(root, dict):
        return [], "root_not_object"
    if key not in root:
        return [], "missing_" + key
    raw = root[key]
    if raw is None or raw == "null":
        return [], "empty_" + key
    if not isinstance(raw, dict):
        return [], "unexpected_" + key + "_envelope"
    if member not in raw:
        return [], "missing_" + member
    rows = raw[member]
    if rows is None or rows == "null":
        return [], "empty_" + member
    if isinstance(rows, dict):
        return [rows], "single_dict"
    if isinstance(rows, list) and all(isinstance(x, dict) for x in rows):
        return rows, "list"
    return [], "malformed_records"


def _positive_price(value):
    if isinstance(value, bool):
        return None
    try:
        dec = Decimal(str(value))
        if dec.is_finite() and 0 < dec <= Decimal("50.00"):
            return str(dec.quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError, TypeError):
        pass
    return None


def _view_leg(leg):
    if not isinstance(leg, dict):
        return {"shape": "invalid"}
    return {
        "sofi": leg.get("symbol") == "SOFI",
        "status": _enum(leg.get("status"), _STATES),
        "side": _enum(leg.get("side"), _SIDES),
        "type": _enum(leg.get("type"), _TYPES),
        "quantity": _quantity(leg.get("quantity")),
        "executed": _quantity(leg.get("exec_quantity")),
        "price": _positive_price(leg.get("price")),
        "stop": _positive_price(
            leg.get("stop") if leg.get("stop") is not None else
            leg.get("stop_price")),
        "has_errors": any(leg.get(k) is not None
                          for k in ("errors", "error")),
    }


def _group_view(group, position_count):
    """Classify a native OTOCO only from its exact broker GET and 3 legs."""
    if not isinstance(group, dict) or group.get("class") != "otoco":
        return {"state": "NOT_AN_OTOCO"}
    details = group.get("leg")
    if isinstance(details, dict):
        details = [details]
    if not isinstance(details, list) or len(details) != 3:
        return {"state": "CHILD_LEGS_UNVERIFIED",
                "reason": "group_has_no_three_legs"}
    parts = [_view_leg(x) for x in details]
    entry, target, stop = parts
    if any(leg["has_errors"] for leg in parts):
        return {"state": "UNVERIFIED", "reason": "leg_error_present"}
    if not all(x["sofi"] and x["quantity"] == "one" for x in parts):
        return {"state": "UNVERIFIED", "reason": "symbol_or_quantity_mismatch"}
    if (entry["side"] != "buy" or entry["type"] != "limit"
        or target["side"] != "sell" or target["type"] != "limit"
        or stop["side"] != "sell" or stop["type"] != "stop"):
        return {"state": "UNVERIFIED", "reason": "leg_geometry_mismatch"}
    if not target["price"] or not stop["stop"]:
        return {"state": "UNVERIFIED", "reason": "exit_prices_missing"}
    if (entry["status"] == "filled" and entry["executed"] == "one"
        and target["status"] in ("open", "pending")
        and stop["status"] in ("open", "pending")
        and position_count == "one"):
        return {"state": "PAPER_ENTRY_FILLED_EXITS_ACTIVE",
                "reason": "broker_group_3_legs_and_position_agree"}
    if (entry["status"] in ("open", "pending")
        and entry["executed"] == "zero" and position_count == "zero"):
        return {"state": "PAPER_ENTRY_WAITING",
                "reason": "entry_not_filled"}
    if (entry["status"] == "filled" and entry["executed"] == "one"
        and position_count == "one"):
        return {"state": "FILLED_BUT_EXITS_NOT_VERIFIED",
                "reason": "exit_leg_status_uncertain"}
    return {"state": "UNVERIFIED", "reason": "group_or_position_inconsistent"}


def _view_order(order):
    if not isinstance(order, dict):
        return {"shape": "not_object"}
    inner = order.get("leg", order.get("order"))
    if isinstance(inner, dict):
        nested = "dict"
        children = [inner]
    elif isinstance(inner, list):
        nested = "list"
        children = inner[:5]
    else:
        nested = "none"
        children = []
    nested_count = len(children)
    return {
        "sofi_symbol": order.get("symbol") == "SOFI",
        "status": _enum(order.get("status"), _STATES),
        "side": _enum(order.get("side"), _SIDES),
        "type": _enum(order.get("type"), _TYPES),
        "class": _enum(order.get("class"), _CLASSES),
        "quantity": _quantity(order.get("quantity")),
        "executed": _quantity(order.get("exec_quantity")),
        "remaining": _quantity(order.get("remaining_quantity")),
        "has_price": order.get("price") is not None,
        "has_stop": order.get("stop") is not None,
        "has_parent_link": any(order.get(k) is not None
                               for k in ("parent_order_id", "parent_id")),
        "has_tag": order.get("tag") is not None,
        "has_errors": any(order.get(k) is not None for k in ("errors", "error")),
        "nested_children_type": nested,
        "nested_children_count_max25": nested_count,
        "group_num_legs": _quantity(order.get("num_legs")),
        "nested_legs": [_view_leg(x) for x in children],
        "known_field_names": sorted(set(order.keys()) & _SAFE_DETAIL_KEYS),
        "unrecognized_field_count": len(set(order.keys()) - _SAFE_DETAIL_KEYS),
    }


def _safe_failure(stage, error):
    # Error class only; never raw HTTP response, token, URL or account ID.
    from urllib.error import HTTPError
    from zerocost_bot.tradier_paper import BrokerUncertain, PaperBlocked
    if isinstance(error, (BrokerUncertain, PaperBlocked)):
        kind = "broker_block_or_uncertain"
    elif isinstance(error, (ValueError, TypeError, KeyError)):
        kind = "invalid_broker_shape"
    elif isinstance(error, OSError):
        kind = "io_failure"
    else:
        kind = "unexpected_error"
    return {"stage": stage, "failure": kind}


def examine(client):
    report = {
        "environment": "TRADIER_SANDBOX_ONLY",
        "mode": "GET_ONLY_BROKER_AUDIT",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "orders_submitted_by_audit": 0,
        "live_money_orders": 0,
    }
    try:
        profile = client._request("GET", "/user/profile")
        account = _choose_account(profile)
    except Exception as error:
        report["failure"] = _safe_failure("sandbox_profile", error)
        return report
    base = "/accounts/" + account
    try:
        raw_balances = client._request("GET", base + "/balances")
        balances = raw_balances.get("balances")
        if not isinstance(balances, dict):
            balances = (raw_balances.get("balance") or {}).get("balances")
        if not isinstance(balances, dict):
            raise ValueError("invalid balance structure")
        report["balances_readable"] = True
        report["pending_orders_count_class"] = _quantity(
            balances.get("pending_orders_count"))
    except Exception as error:
        report["balance_failure"] = _safe_failure("sandbox_balances", error)
    try:
        positions_raw = client._request("GET", base + "/positions")
        positions, shape = _listify_envelope(positions_raw, "positions", "position")
        report["positions_shape"] = shape
        report["total_position_count"] = min(len(positions), 100)
        report["sofi_positions"] = sum(p.get("symbol") == "SOFI" for p in positions)
        report["sofi_quantity"] = _quantity(sum(
            Decimal(str(p.get("quantity", 0))) for p in positions
            if p.get("symbol") == "SOFI"))
    except Exception as error:
        report["position_failure"] = _safe_failure("sandbox_positions", error)
    try:
        orders_raw = client._request(
            "GET", base + "/orders",
            query={"limit": 1000, "includeTags": "true"})
        orders, shape = _listify_envelope(orders_raw, "orders", "order")
        report["orders_shape"] = shape
        report["orders_count"] = min(len(orders), 1001)
        report["orders_pagination_flags"] = {
            "total_pages_more_than_one": (
                isinstance(orders_raw.get("orders"), dict)
                and isinstance(orders_raw["orders"].get("total_pages"), int)
                and orders_raw["orders"]["total_pages"] > 1
            ),
            "at_limit": len(orders) >= 1000,
        }
        report["orders_summary"] = [
            _view_order(item) for item in orders[:12]
        ]
        report["sofi_order_count"] = sum(
            o.get("symbol") == "SOFI" for o in orders)
        # Exact GET for every SOFI order only (max 12). IDs never logged.
        detail = []
        for item in orders:
            if item.get("symbol") != "SOFI" or len(detail) >= 12:
                continue
            ident = item.get("id")
            if isinstance(ident, bool) or not str(ident).isdigit():
                detail.append({"failure": "malformed_order_identifier"})
                continue
            try:
                raw = client._request(
                    "GET", base + "/orders/" + str(ident),
                    query={"includeTags": "true"})
                detail.append(_view_order(raw.get("order")))
            except Exception as error:
                detail.append(_safe_failure("sofi_order_detail", error))
        report["sofi_order_detail_views"] = detail
        # Composite OTOCO orders have no top-level SOFI symbol, so they
        # must be inspected as a GROUP by exact ID before deciding whether
        # the entry and both protective legs are working.
        groups = []
        for item in orders:
            if item.get("class") != "otoco" or len(groups) >= 3:
                continue
            ident = item.get("id")
            if isinstance(ident, bool) or not str(ident).isdigit():
                groups.append({"state": "MALFORMED_GROUP_ID"})
                continue
            try:
                raw = client._request(
                    "GET", base + "/orders/" + str(ident),
                    query={"includeTags": "true"})
                group = raw.get("order")
                groups.append({
                    "detail": _view_order(group),
                    "protection": _group_view(group, report.get("sofi_quantity")),
                })
            except Exception as error:
                groups.append(_safe_failure("otoco_group_detail", error))
        report["otoco_group_inspections"] = groups
    except Exception as error:
        report["order_failure"] = _safe_failure("sandbox_orders", error)
    return report


def main():
    try:
        client = TradierSandbox()
        # Only the sanctioned GET interface is invoked by examine().
        report = examine(client)
        print(json.dumps(report, allow_nan=False, sort_keys=True))
        return 0 if "failure" not in report and "order_failure" not in report else 1
    except Exception:
        print(json.dumps({
            "environment": "TRADIER_SANDBOX_ONLY",
            "mode": "GET_ONLY_BROKER_AUDIT",
            "failure": {"stage": "startup", "failure": "unavailable"},
            "orders_submitted_by_audit": 0,
        }, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
