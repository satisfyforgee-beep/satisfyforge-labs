"""Read-only, fail-closed Tradier SANDBOX order and protective-exit verification.

The module cannot submit, cancel, replace or modify any order. A parent
OTOCO receipt and/or fill alone do NOT prove its triggered OCO exits are
working. Never infer child linkage merely from matching symbols or prices.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Mapping
import re

from .tradier_paper import (
    TradierSandbox, BrokerUncertain, PaperBlocked,
)

_ID = re.compile(r"[0-9]{1,18}$")
_STATES = frozenset(("pending", "open", "partially_filled", "filled",
                     "rejected", "expired", "canceled", "pending_cancel", "error"))
_MARKET_WORKING = frozenset(("open", "pending"))
_TERMINAL = frozenset(("rejected", "canceled", "expired"))
# Deliberately supports only a precisely identified parent relationship.
# An undocumented generic "same-day/same-symbol" match is unsafe.
_ALLOWED_LINK_FIELDS = ("parent_id", "parent_order_id")


def _id(raw):
    if isinstance(raw, bool):
        raise BrokerUncertain("invalid sandbox order ID")
    if isinstance(raw, int):
        raw = str(raw)
    if not isinstance(raw, str) or not _ID.fullmatch(raw) or int(raw) < 1:
        raise BrokerUncertain("missing or malformed sandbox order ID")
    return raw


def _number(raw, name):
    if isinstance(raw, bool):
        raise BrokerUncertain(name + " is not numeric")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        raise BrokerUncertain(name + " missing or invalid") from None
    if not value.is_finite() or value < 0:
        raise BrokerUncertain(name + " non-finite or negative")
    return value


def _status(raw):
    if not isinstance(raw, str) or raw not in _STATES:
        raise BrokerUncertain("unknown order status")
    return raw


def _link_matches(child, parent_id):
    """Only explicit broker-generated parent links count as proof of kinship."""
    if not isinstance(child, dict):
        return False
    present = [k for k in _ALLOWED_LINK_FIELDS if child.get(k) is not None]
    if len(present) != 1:
        # Contradictory links (or missing links) cannot be verified.
        return False
    try:
        return _id(child[present[0]]) == parent_id
    except BrokerUncertain:
        return False


def _order_fill(order):
    requested = _number(order.get("quantity"), "order quantity")
    executed = _number(order.get("exec_quantity"), "executed quantity")
    if requested == 0 or executed > requested:
        raise BrokerUncertain("broker order has inconsistent fill quantities")
    status = _status(order.get("status"))
    # Filled must be fully executed; no other state can claim full fill.
    if (status == "filled") != (executed == requested):
        raise BrokerUncertain("fill quantities contradict order status")
    return status, requested, executed


@dataclass(frozen=True)
class BracketAssessment:
    """Only anonymous counts/states leave the reconciliation library."""
    readiness: str
    reason: str
    parent_status: str
    verified_children: int
    live_order_enabled: bool = False
    action: str = "DO_NOT_TRADE"

    def as_report(self):
        return {
            "environment": "TRADIER_SANDBOX_ONLY",
            "readiness": self.readiness,
            "reason": self.reason,
            "parent_status": self.parent_status,
            "verified_protective_exits": self.verified_children,
            "live_order_enabled": False,
            "order_action": "DO_NOT_TRADE",
        }


def _blocked(reason, parent_status="unknown", count=0):
    return BracketAssessment("HALT_AND_RECONCILE", reason, parent_status, count)


def assess_bracket(parent, candidates, positions, *, expected_symbol):
    """Verify a 1-share OTOCO entry plus linked opposite sell exits.

    A successfully filled parent with no explicitly linked children is treated
    as UNPROTECTED, never as a safe position. Broker might supply nested legs
    not present in the current-session orders response: in that case stop and
    investigate, don't silently invent children.
    """
    if not isinstance(parent, dict):
        return _blocked("parent order absent")
    if not isinstance(candidates, list) or not isinstance(positions, list):
        return _blocked("broker order or positions inventory missing")
    try:
        parent_id = _id(parent.get("id"))
        parent_status, parent_qty, parent_exec = _order_fill(parent)
        symbol = parent.get("symbol")
        if (symbol != expected_symbol or
                not isinstance(symbol, str) or not re.fullmatch(r"[A-Z]{1,5}", symbol)):
            return _blocked("parent symbol mismatch", parent_status)
        if parent_qty != 1 or parent.get("side") != "buy":
            return _blocked("parent must be one-share equity buy", parent_status)
    except BrokerUncertain:
        return _blocked("parent order details incomplete or inconsistent")

    # Explicitly look for broker-attested child links; don't infer from
    # candidates sharing symbols, order times, account or matching strikes.
    children = []
    seen = set()
    for child in candidates:
        if not isinstance(child, dict):
            return _blocked("malformed order inventory", parent_status)
        if child.get("id") is not None:
            try:
                cid = _id(child.get("id"))
            except BrokerUncertain:
                return _blocked("malformed child order ID", parent_status)
            if cid == parent_id:
                continue
        else:
            return _blocked("unidentified order in inventory", parent_status)
        if _link_matches(child, parent_id):
            if cid in seen:
                return _blocked("duplicate linked child order", parent_status)
            seen.add(cid)
            children.append(child)

    if parent_status in _TERMINAL and parent_exec == 0:
        return BracketAssessment(
            "ENTRY_NOT_FILLED", "entry rejected/cancelled/expired without fill",
            parent_status, len(children),
        )
    if parent_status in ("pending", "open") and parent_exec == 0:
        if any(x.get("status") == "filled" for x in children):
            return _blocked("exit reported filled before parent", parent_status, len(children))
        return BracketAssessment(
            "AWAITING_ENTRY", "entry not filled; OCO exits need not be active yet",
            parent_status, len(children),
        )
    if parent_status in ("partially_filled", "pending_cancel", "error") or parent_exec != 1:
        return _blocked("partial or uncertain entry requires broker reconciliation",
                        parent_status, len(children))

    # From here, parent is fully filled. Positions must be resolved before
    # claiming the entry is protected or the bracket is closed.
    holding = Decimal(0)
    for item in positions:
        if not isinstance(item, dict):
            return _blocked("malformed position inventory", parent_status, len(children))
        if item.get("symbol") != expected_symbol:
            # An unrelated account position makes exposure ambiguous.
            return _blocked("unrelated account position is present", parent_status,
                            len(children))
        try:
            amt = _number(item.get("quantity"), "position quantity")
        except BrokerUncertain:
            return _blocked("unknown account position quantity", parent_status,
                            len(children))
        holding += amt
    if holding not in (Decimal("0"), Decimal("1")):
        return _blocked("unexpected number of owned shares", parent_status,
                        len(children))
    if len(children) != 2:
        return _blocked("entry filled but two explicitly linked exits are not verified",
                        parent_status, len(children))

    observed = {}
    for child in children:
        try:
            status, qty, executed = _order_fill(child)
            if (child.get("side") != "sell" or child.get("symbol") != symbol
                    or qty != 1):
                return _blocked("child side, symbol or quantity mismatch",
                                parent_status, len(children))
            typ = child.get("type")
            if typ not in ("limit", "stop") or typ in observed:
                return _blocked("expected exactly one limit and one stop sell",
                                parent_status, len(children))
            if typ == "limit":
                if _number(child.get("price"), "target price") == 0:
                    return _blocked("invalid profit target", parent_status, len(children))
            else:
                if _number(child.get("stop"), "stop price") == 0:
                    return _blocked("invalid protective stop", parent_status, len(children))
            observed[typ] = status
        except BrokerUncertain:
            return _blocked("linked exit metadata incomplete", parent_status, len(children))
    if set(observed) != {"limit", "stop"}:
        return _blocked("missing one protective exit", parent_status, len(children))

    statuses = (observed["limit"], observed["stop"])
    if holding == 1 and all(x in _MARKET_WORKING for x in statuses):
        return BracketAssessment(
            "PROTECTED_PAPER_POSITION",
            "linked target and stop are working; inspect stop-market fill risk",
            parent_status, 2,
        )
    if holding == 0 and statuses.count("filled") == 1 and statuses.count("canceled") == 1:
        return BracketAssessment(
            "CLOSED_PAPER_POSITION",
            "one linked exit filled and the alternative was cancelled",
            parent_status, 2,
        )
    return _blocked("child exit states or position do not reconcile",
                    parent_status, len(children))


def assess_native_otoco(group, positions, *, expected_symbol="SOFI"):
    """Verify actual Tradier OTOCO schema: group-level id + embedded leg[].

    Unlike independent basic stock orders, Tradier returns native OTOCO
    orders as a group containing three legs, with no top-level symbol or
    quantity. This representation was verified in the user's real SANDBOX
    (READ ONLY) October 21, 2026. It is not safe to infer protection from
    a group-level "open" status alone.
    """
    if not isinstance(group, dict) or group.get("class") != "otoco":
        return _blocked("not a native OTOCO group")
    try:
        _id(group.get("id"))
    except BrokerUncertain:
        return _blocked("native OTOCO group has no valid order ID")
    if not isinstance(positions, list):
        return _blocked("positions missing for native OTOCO group")
    legs = group.get("leg")
    if isinstance(legs, dict):
        legs = [legs]
    if not isinstance(legs, list) or len(legs) != 3:
        return _blocked("native OTOCO must have exactly three broker-linked legs")
    if any(not isinstance(leg, dict) for leg in legs):
        return _blocked("malformed broker-native OTOCO leg")
    qty = Decimal(0)
    for pos in positions:
        if not isinstance(pos, dict) or pos.get("symbol") != expected_symbol:
            return _blocked("sandbox account has unrelated or malformed position")
        try:
            qty += _number(pos.get("quantity"), "position quantity")
        except BrokerUncertain:
            return _blocked("position quantity cannot be trusted")
    if qty not in (Decimal(0), Decimal(1)):
        return _blocked("unexpected sandbox position size")
    first, target, stop = legs
    for leg in legs:
        if leg.get("symbol") != expected_symbol:
            return _blocked("native OTOCO symbol mismatch")
        try:
            requested = _number(leg.get("quantity"), "leg quantity")
            if requested != 1:
                return _blocked("native OTOCO leg not one share")
            if leg.get("errors") or leg.get("error"):
                return _blocked("broker-native OTOCO reports order errors")
        except BrokerUncertain:
            return _blocked("native OTOCO quantities incomplete")
    if (first.get("side") != "buy" or first.get("type") != "limit"
        or target.get("side") != "sell" or target.get("type") != "limit"
        or stop.get("side") != "sell" or stop.get("type") != "stop"):
        return _blocked("native OTOCO is not a supported buy-target-stop bracket")
    try:
        entry_px = _number(first.get("price"), "entry limit")
        target_px = _number(target.get("price"), "target limit")
        stop_px = _number(
            stop.get("stop") if stop.get("stop") is not None
            else stop.get("stop_price"), "protective stop")
    except BrokerUncertain:
        return _blocked("native OTOCO entry or exit price missing")
    if not (Decimal(1) <= entry_px <= Decimal(20)
            and Decimal(0) < stop_px < entry_px < target_px):
        return _blocked("native OTOCO price geometry unsafe")

    statuses = []
    quantities = []
    for leg in legs:
        try:
            legstatus, required, executed = _order_fill(leg)
            statuses.append(legstatus)
            quantities.append(executed)
        except BrokerUncertain:
            return _blocked("native OTOCO status and executed quantities disagree")
    entry_status, target_status, stop_status = statuses
    group_status = group.get("status")
    if group_status not in _STATES:
        return _blocked("native OTOCO group status unrecognized", entry_status)
    if (entry_status in ("open", "pending") and quantities[0] == 0
            and qty == 0 and quantities[1] == 0 and quantities[2] == 0):
        return BracketAssessment("AWAITING_ENTRY",
                                 "native OTOCO entry has not filled",
                                 entry_status, 0)
    if (entry_status == "rejected" and qty == 0 and quantities[0] == 0):
        return BracketAssessment("ENTRY_NOT_FILLED",
                                 "native OTOCO entry rejected before fill",
                                 entry_status, 0)
    if (entry_status == "filled" and quantities[0] == 1 and qty == 1
            and group_status in ("open", "pending")
            and target_status in _MARKET_WORKING
            and stop_status in _MARKET_WORKING
            and quantities[1] == 0 and quantities[2] == 0):
        return BracketAssessment(
            "PROTECTED_PAPER_POSITION",
            "native Tradier OTOCO group shows filled entry and two working exits",
            entry_status, 2,
        )
    if (entry_status == "filled" and quantities[0] == 1 and qty == 0
            and ((target_status == "filled" and quantities[1] == 1
                  and stop_status == "canceled" and quantities[2] == 0)
                 or (stop_status == "filled" and quantities[2] == 1
                     and target_status == "canceled" and quantities[1] == 0))):
        return BracketAssessment(
            "CLOSED_PAPER_POSITION",
            "one native OTOCO exit filled and sibling canceled; position closed",
            entry_status, 2,
        )
    return _blocked(
        "native OTOCO order legs/positions not safely reconciled",
        entry_status, 2,
    )


class SandboxReconciler:
    """GET-only; never changes brokerage state. No credential/ID disclosure."""

    def __init__(self, broker: TradierSandbox):
        if not isinstance(broker, TradierSandbox):
            raise TypeError("sandbox-only broker required")
        self._broker = broker

    def inspect(self, order_id, *, symbol, account_selector=None):
        if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z]{1,5}", symbol):
            raise PaperBlocked("valid supported stock required")
        order_id = _id(order_id)
        snapshot = self._broker.state(account_selector)
        base = "/accounts/" + snapshot["account"]
        # Include tag if Tradier provides it; nothing sensitive is exported.
        raw = self._broker._request(
            "GET", base + "/orders/" + order_id, query={"includeTags": "true"})
        parent = raw.get("order") if isinstance(raw, dict) else None
        if not isinstance(parent, dict):
            raise BrokerUncertain("specific parent order is unavailable")
        if _id(parent.get("id")) != order_id:
            raise BrokerUncertain("specific order ID mismatch")
        # Tradier returns OTOCO as ONE composite group with three
        # embedded leg objects. Parent symbol/qty are absent at top-level.
        # Validate the group and its parent ID against the just-read
        # session orders list; use the group's native leg[] relationships.
        if parent.get("class") == "otoco":
            matching = [
                row for row in snapshot["orders"]
                if isinstance(row, dict) and str(row.get("id")) == order_id
            ]
            if len(matching) != 1 or matching[0].get("class") != "otoco":
                raise BrokerUncertain("native OTOCO group absent from order inventory")
            result = assess_native_otoco(
                parent, snapshot["positions"], expected_symbol=symbol)
            return result.as_report()
        # Order LIST records are not independently sufficient to certify
        # child protection. Resolve each explicitly linked child using an
        # exact GET, then verify the relationship again on that response.
        explicitly_linked = []
        for order in snapshot["orders"]:
            if not isinstance(order, dict):
                raise BrokerUncertain("malformed sandbox order list")
            if _link_matches(order, order_id):
                explicitly_linked.append(_id(order.get("id")))
        if len(set(explicitly_linked)) != len(explicitly_linked):
            raise BrokerUncertain("duplicate linked sandbox order")
        # Any ambiguous or unexpectedly numerous child orders halt instead
        # of triggering unbounded GET requests or assigning a protective label.
        if len(explicitly_linked) > 2:
            raise BrokerUncertain("unexpected number of linked exits")
        verified = []
        for child_id in explicitly_linked:
            raw_child = self._broker._request(
                "GET", base + "/orders/" + child_id,
                query={"includeTags": "true"})
            child = raw_child.get("order") if isinstance(raw_child, dict) else None
            if not isinstance(child, dict) or _id(child.get("id")) != child_id:
                raise BrokerUncertain("linked child could not be verified")
            if not _link_matches(child, order_id):
                raise BrokerUncertain("independent child linkage mismatch")
            verified.append(child)
        # Tradier's list may omit advanced-order parent links altogether.
        # In that case the filled position MUST NOT be marked protected.
        evidence = assess_bracket(parent, verified, snapshot["positions"],
                                  expected_symbol=symbol)
        return evidence.as_report()
