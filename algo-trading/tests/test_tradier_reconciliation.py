"""Offline brokerage-graph tests only: neither network nor broker order writes."""
from copy import deepcopy
import json
import unittest

from zerocost_bot.tradier_reconciliation import (
    BracketAssessment, SandboxReconciler, assess_bracket, assess_native_otoco,
)
from zerocost_bot.tradier_paper import (
    TradierSandbox, BrokerUncertain, PaperBlocked,
)

PID = 92000
SYMBOL = "SOFI"


def entry(status="filled", executed=1):
    return {
        "id": PID, "status": status, "quantity": 1,
        "exec_quantity": executed, "symbol": SYMBOL,
        "side": "buy", "type": "limit",
    }


def children(target_status="open", stop_status="open"):
    return [
        {"id": PID + 1, "parent_order_id": PID,
         "symbol": SYMBOL, "side": "sell", "type": "limit",
         "quantity": 1, "exec_quantity": int(target_status == "filled"),
         "price": "15.80", "status": target_status},
        {"id": PID + 2, "parent_order_id": PID,
         "symbol": SYMBOL, "side": "sell", "type": "stop",
         "quantity": 1, "exec_quantity": int(stop_status == "filled"),
         "stop": "14.80", "status": stop_status},
    ]


def holding(quantity=1):
    return [{"symbol": SYMBOL, "quantity": str(quantity)}] if quantity else []


def check(parent=None, linked=None, positions=None):
    return assess_bracket(
        entry() if parent is None else parent,
        children() if linked is None else linked,
        holding() if positions is None else positions,
        expected_symbol=SYMBOL,
    )


class ExitReconciliationTests(unittest.TestCase):
    def test_verified_protected_position_requires_two_linked_sell_exits(self):
        result = check()
        self.assertEqual(result.readiness, "PROTECTED_PAPER_POSITION")
        self.assertEqual(result.verified_children, 2)
        self.assertFalse(result.live_order_enabled)
        self.assertEqual(result.action, "DO_NOT_TRADE")
        self.assertNotIn(str(PID), json.dumps(result.as_report()))

    def test_verified_closed_position_requires_one_fill_one_cancel(self):
        result = check(linked=children("filled", "canceled"), positions=[])
        self.assertEqual(result.readiness, "CLOSED_PAPER_POSITION")
        self.assertEqual(result.verified_children, 2)

    def test_stop_exit_can_be_filled_and_target_cancelled(self):
        result = check(linked=children("canceled", "filled"), positions=[])
        self.assertEqual(result.readiness, "CLOSED_PAPER_POSITION")

    def test_parent_open_waits_and_does_not_claim_protection(self):
        result = check(parent=entry("open", 0), linked=[])
        self.assertEqual(result.readiness, "AWAITING_ENTRY")
        self.assertEqual(result.verified_children, 0)

    def test_parent_pending_waits(self):
        result = check(parent=entry("pending", 0), linked=[])
        self.assertEqual(result.readiness, "AWAITING_ENTRY")

    def test_unfilled_rejected_is_terminal_without_position(self):
        result = check(parent=entry("rejected", 0), linked=[])
        self.assertEqual(result.readiness, "ENTRY_NOT_FILLED")

    def test_missing_child_is_unprotected(self):
        result = check(linked=children()[:1])
        self.assertEqual(result.readiness, "HALT_AND_RECONCILE")
        self.assertIn("two", result.reason)

    def test_matching_symbol_is_not_proof_of_parent_relationship(self):
        unlinked = children()
        for obj in unlinked:
            obj.pop("parent_order_id")
        self.assertEqual(check(linked=unlinked).readiness,
                         "HALT_AND_RECONCILE")

    def test_wrong_parent_link_is_never_accepted(self):
        linked = children()
        linked[0]["parent_order_id"] = PID + 500
        self.assertEqual(check(linked=linked).readiness,
                         "HALT_AND_RECONCILE")

    def test_ambiguous_parent_link_fails(self):
        linked = children()
        linked[0]["parent_id"] = PID
        self.assertEqual(check(linked=linked).readiness, "HALT_AND_RECONCILE")

    def test_does_not_count_duplicate_child_id(self):
        linked = children()
        linked[1]["id"] = linked[0]["id"]
        self.assertEqual(check(linked=linked).readiness, "HALT_AND_RECONCILE")

    def test_does_not_count_wrong_side_or_wrong_stock(self):
        for key, value in [("side", "sell_short"), ("symbol", "AAL"),
                           ("quantity", 2)]:
            data = children()
            data[0][key] = value
            with self.subTest(key=key):
                self.assertEqual(check(linked=data).readiness,
                                 "HALT_AND_RECONCILE")

    def test_does_not_count_duplicated_stop_or_limit(self):
        data = children()
        data[1]["type"] = "limit"
        self.assertEqual(check(linked=data).readiness, "HALT_AND_RECONCILE")

    def test_missing_stop_or_price_is_unverified(self):
        for index, prop in ((0, "price"), (1, "stop")):
            data = children()
            data[index].pop(prop)
            self.assertEqual(check(linked=data).readiness, "HALT_AND_RECONCILE")

    def test_canceled_stop_with_open_position_is_unsafe(self):
        self.assertEqual(
            check(linked=children("open", "canceled")).readiness,
            "HALT_AND_RECONCILE",
        )

    def test_one_child_filled_but_position_is_still_open(self):
        self.assertEqual(check(linked=children("filled", "canceled")).readiness,
                         "HALT_AND_RECONCILE")

    def test_account_flat_with_both_exits_working_is_inconsistent(self):
        self.assertEqual(check(positions=[]).readiness, "HALT_AND_RECONCILE")

    def test_partial_entry_requires_immediate_reconciliation(self):
        self.assertEqual(
            check(parent=entry("partially_filled", .5)).readiness,
            "HALT_AND_RECONCILE",
        )

    def test_filled_parent_with_missing_executed_quantity_is_unverified(self):
        e = entry()
        e.pop("exec_quantity")
        self.assertEqual(check(parent=e).readiness, "HALT_AND_RECONCILE")

    def test_unknown_broker_status_is_unverified(self):
        e = entry()
        e["status"] = "mystery"
        self.assertEqual(check(parent=e).readiness, "HALT_AND_RECONCILE")

    def test_holding_unrelated_position_blocks(self):
        self.assertEqual(
            check(positions=[{"symbol": "AAL", "quantity": 1}]).readiness,
            "HALT_AND_RECONCILE",
        )

    def test_children_stopped_before_parent_filled(self):
        self.assertEqual(
            check(parent=entry("open", 0),
                  linked=children("filled", "canceled")).readiness,
            "HALT_AND_RECONCILE",
        )

    def test_broker_receipt_without_fill_is_not_a_protected_position(self):
        self.assertEqual(check(parent=entry("open", 0)).readiness, "AWAITING_ENTRY")
        self.assertNotEqual(check(parent=entry("open", 0)).readiness,
                            "PROTECTED_PAPER_POSITION")


class StubBroker:
    def __init__(self, parent=None, linked=None, positions=None):
        self.parent = parent if parent is not None else entry()
        self.linked = linked if linked is not None else children()
        self.positions = positions if positions is not None else holding()
        self.calls = []

    def __call__(self, method, path, query, form):
        self.calls.append((method, path, query, form))
        if method != "GET":
            raise AssertionError("broker action in read-only reconciler")
        if path == "/user/profile":
            return {"profile": {"account": {"account_number": "VA00001234"}}}
        if path.endswith("/balances"):
            return {"balances": {"account_number": "VA00001234",
                                 "total_cash": "1000", "pending_orders_count": 0}}
        if path.endswith("/positions"):
            return {"positions": {"position": self.positions}}
        if path.endswith("/orders"):
            return {"orders": {"order": [self.parent] + self.linked}}
        if path.endswith("/orders/" + str(PID)):
            return {"order": self.parent}
        for child in self.linked:
            if path.endswith("/orders/" + str(child["id"])):
                return {"order": child}
        raise AssertionError("not an allowed broker endpoint")


class NativeTradierOtocoTests(unittest.TestCase):
    @staticmethod
    def native(*, stop_status="open", profit_status="open",
               position=1, group_status="open"):
        group = {
            "id": PID, "class": "otoco", "status": group_status,
            "leg": [
                {"symbol": SYMBOL, "side": "buy", "type": "limit", "price": "14.84",
                 "quantity": 1, "exec_quantity": 1, "status": "filled"},
                {"symbol": SYMBOL, "side": "sell", "type": "limit", "price": "15.36",
                 "quantity": 1,
                 "exec_quantity": int(profit_status == "filled"),
                 "status": profit_status},
                {"symbol": SYMBOL, "side": "sell", "type": "stop", "stop_price": "14.54",
                 "quantity": 1,
                 "exec_quantity": int(stop_status == "filled"),
                 "status": stop_status},
            ],
        }
        return group, holding(position)

    def test_real_sandbox_group_shape_is_protected(self):
        group, positions = self.native()
        out = assess_native_otoco(group, positions)
        self.assertEqual(out.readiness, "PROTECTED_PAPER_POSITION")
        self.assertEqual(out.verified_children, 2)
        self.assertFalse(out.live_order_enabled)

    def test_native_group_without_two_exits_halts(self):
        group, positions = self.native()
        group["leg"].pop()
        self.assertEqual(assess_native_otoco(group, positions).readiness,
                         "HALT_AND_RECONCILE")

    def test_native_group_with_expired_stop_halts(self):
        group, positions = self.native(stop_status="expired")
        self.assertEqual(assess_native_otoco(group, positions).readiness,
                         "HALT_AND_RECONCILE")

    def test_native_group_closed_requires_one_filled_exit_and_zero_position(self):
        group, positions = self.native(
            profit_status="filled", stop_status="canceled", position=0)
        self.assertEqual(assess_native_otoco(group, positions).readiness,
                         "CLOSED_PAPER_POSITION")
        group, positions = self.native(
            profit_status="filled", stop_status="canceled", position=1)
        self.assertEqual(assess_native_otoco(group, positions).readiness,
                         "HALT_AND_RECONCILE")

    def test_native_group_unfilled_entry_does_not_claim_protection(self):
        group, positions = self.native(position=0)
        group["leg"][0].update(status="open", exec_quantity=0)
        self.assertEqual(assess_native_otoco(group, positions).readiness,
                         "AWAITING_ENTRY")

    def test_native_group_bad_size_symbol_or_side_halts(self):
        for change in (
            {"symbol": "AAL"}, {"quantity": 2}, {"side": "sell_short"},
            {"type": "market"}, {"status": "unknown"}
        ):
            group, positions = self.native()
            group["leg"][2].update(change)
            with self.subTest(change=change):
                self.assertEqual(assess_native_otoco(group, positions).readiness,
                                 "HALT_AND_RECONCILE")

    def test_broker_native_group_exact_id_get_only(self):
        group, positions = self.native()
        class CompositeTransport(StubBroker):
            def __call__(self, method, path, query, form):
                self.calls.append((method, path, query, form))
                if method != "GET":
                    raise AssertionError("no writes")
                if path == "/user/profile":
                    return {"profile": {"account": {"account_number": "VA00001234"}}}
                if path.endswith("/balances"):
                    return {"balances": {"pending_orders_count": 2,
                                         "total_cash": 99950}}
                if path.endswith("/positions"):
                    return {"positions": {"position": positions}}
                if path.endswith("/orders"):
                    return {"orders": {"order": group}}
                if path.endswith("/orders/" + str(PID)):
                    return {"order": group}
                raise AssertionError("unexpected path")
        source = CompositeTransport()
        reporter = SandboxReconciler(
            TradierSandbox(token="FAKE", transport=source))
        report = reporter.inspect(PID, symbol=SYMBOL)
        self.assertEqual(report["readiness"], "PROTECTED_PAPER_POSITION")
        self.assertTrue(all(c[0] == "GET" for c in source.calls))
        self.assertNotIn("VA00001234", json.dumps(report))
        self.assertNotIn(str(PID), json.dumps(report))


class ReadOnlyRemoteTests(unittest.TestCase):
    def test_real_adapter_get_only(self):
        fake = StubBroker()
        sandbox = TradierSandbox(token="SYNTHETIC_ONLY", transport=fake)
        status = SandboxReconciler(sandbox).inspect(
            PID, symbol=SYMBOL)
        self.assertEqual(status["readiness"], "PROTECTED_PAPER_POSITION")
        self.assertFalse(status["live_order_enabled"])
        self.assertEqual({call[0] for call in fake.calls}, {"GET"})
        self.assertNotIn("VA00001234", json.dumps(status))
        self.assertNotIn(str(PID), json.dumps(status))

    def test_each_independent_exit_order_must_be_read_back(self):
        fake = StubBroker()
        status = SandboxReconciler(
            TradierSandbox(token="FAKE", transport=fake)).inspect(
                PID, symbol=SYMBOL)
        self.assertEqual(status["readiness"], "PROTECTED_PAPER_POSITION")
        detail_calls = [call for call in fake.calls
                        if call[1].endswith("/orders/" + str(PID+1))
                        or call[1].endswith("/orders/" + str(PID+2))]
        self.assertEqual(len(detail_calls), 2)
        self.assertTrue(all(call[0] == "GET" for call in detail_calls))

    def test_individual_broker_response_must_retain_parent_link(self):
        class BadChild(StubBroker):
            def __call__(self, method, path, query, form):
                if path.endswith("/orders/" + str(PID+1)):
                    value = dict(self.linked[0])
                    value.pop("parent_order_id")
                    return {"order": value}
                return super().__call__(method, path, query, form)
        with self.assertRaises(BrokerUncertain):
            SandboxReconciler(TradierSandbox(
                token="FAKE", transport=BadChild())).inspect(
                    PID, symbol=SYMBOL)

    def test_no_broker_schema_guess_on_missing_children(self):
        fake = StubBroker(linked=[])
        status = SandboxReconciler(
            TradierSandbox(token="FAKE", transport=fake)).inspect(
                PID, symbol=SYMBOL)
        self.assertEqual(status["readiness"], "HALT_AND_RECONCILE")

    def test_wrong_parent_id_is_hard_failure(self):
        fake = StubBroker(parent=entry())
        fake.parent = dict(fake.parent, id=PID+99)
        with self.assertRaises(BrokerUncertain):
            SandboxReconciler(TradierSandbox(
                token="FAKE", transport=fake)).inspect(PID, symbol=SYMBOL)

    def test_rejects_invalid_order_id_without_network(self):
        fake = StubBroker()
        with self.assertRaises(BrokerUncertain):
            SandboxReconciler(
                TradierSandbox(token="FAKE", transport=fake)).inspect(
                    "22/../../../order", symbol=SYMBOL)
        self.assertEqual(fake.calls, [])

    def test_rejects_invalid_symbol_without_network(self):
        fake = StubBroker()
        with self.assertRaises(PaperBlocked):
            SandboxReconciler(
                TradierSandbox(token="FAKE", transport=fake)).inspect(
                    PID, symbol="BTC/USD")
        self.assertEqual(fake.calls, [])


if __name__ == "__main__":
    unittest.main()
