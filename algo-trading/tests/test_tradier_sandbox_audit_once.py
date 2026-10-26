"""Offline contract tests: one-shot SANDBOX audit can perform GETs ONLY."""
import json
import unittest

from zerocost_bot.tradier_paper import TradierSandbox
from tradier_sandbox_audit_once import examine, _view_order, _listify_envelope, _group_view, _paper_entry_preflight


class FakeTransport:
    def __init__(self, *, positions=None, orders=None):
        self.calls = []
        self.positions = positions or []
        self.orders = orders or []

    def __call__(self, method, path, query, form):
        self.calls.append((method, path, query, form))
        if method != "GET" or form is not None:
            raise AssertionError("AUDIT TRIED TO WRITE A BROKER ORDER")
        if path == "/user/profile":
            return {"profile": {"account": [{"account_number": "VA00001234"}]}}
        if path.endswith("/balances"):
            return {"balances": {"pending_orders_count": 0, "total_cash": 100000}}
        if path.endswith("/positions"):
            return {"positions": {"position": self.positions}} if self.positions else {
                "positions": "null"}
        if path.endswith("/orders"):
            return {"orders": {"order": self.orders}} if self.orders else {
                "orders": "null"}
        if "/orders/" in path:
            num = int(path.split("/")[-1])
            return {"order": next(x for x in self.orders if x["id"] == num)}
        raise AssertionError("unsupported audit endpoint " + path)


def samples():
    return [
        {"id": 191001, "tag": "SECRET_SHOULD_BE_REDACTED",
         "status": "filled", "symbol": "SOFI", "side": "buy",
         "type": "limit", "class": "equity", "exec_quantity": 1,
         "quantity": 1, "avg_fill_price": 14.84,
         "unexpected_customer_email": "customer-private@example.test"},
        {"id": 191002, "parent_order_id": 191001, "status": "open",
         "symbol": "SOFI", "side": "sell", "type": "stop",
         "class": "equity", "exec_quantity": 0, "quantity": 1,
         "stop": "14.54"},
    ]


class SandboxAuditTests(unittest.TestCase):
    def test_order_shape_labels_only(self):
        row = _view_order(samples()[0])
        blob = json.dumps(row)
        self.assertEqual(row["status"], "filled")
        self.assertEqual(row["executed"], "one")
        self.assertNotIn("191001", blob)
        self.assertNotIn("SECRET", blob)
        self.assertNotIn("customer-private", blob)

    def test_full_audit_only_get_and_no_pii_or_ids(self):
        transport = FakeTransport(
            positions=[{"symbol": "SOFI", "quantity": 1}],
            orders=samples())
        broker = TradierSandbox(token="FAKE_SECRET_TOKEN", transport=transport)
        result = examine(broker)
        self.assertTrue(result["balances_readable"])
        self.assertEqual(result["sofi_order_count"], 2)
        self.assertEqual(result["sofi_quantity"], "one")
        self.assertEqual(result["sofi_order_detail_views"][0]["status"], "filled")
        self.assertTrue(all(method == "GET" for method, *_ in transport.calls))
        exposed = json.dumps(result)
        for private in ("191001", "191002", "VA00001234",
                        "FAKE_SECRET_TOKEN", "customer-private", "SECRET_SHOULD"):
            self.assertNotIn(private, exposed)
        self.assertEqual(result["orders_submitted_by_audit"], 0)
        self.assertEqual(result["live_money_orders"], 0)

    def test_empty_account_returned_without_inventing_fills(self):
        transport = FakeTransport()
        broker = TradierSandbox(token="FAKE", transport=transport)
        result = examine(broker)
        self.assertEqual(result["positions_shape"], "empty_positions")
        self.assertEqual(result["orders_shape"], "empty_orders")
        self.assertEqual(result["sofi_order_count"], 0)
        self.assertEqual(result["sofi_order_detail_views"], [])
        self.assertEqual(result["sofi_quantity"], "zero")

    def test_nested_order_summary_without_order_ids(self):
        row = _view_order({
            "symbol": "SOFI", "status": "open", "class": "otoco",
            "order": [{"id": 42}, {"id": 43}], "secret_field": "private",
        })
        self.assertEqual(row["nested_children_type"], "list")
        self.assertEqual(row["nested_children_count_max25"], 2)
        self.assertNotIn("42", json.dumps(row))
        self.assertNotIn("private", json.dumps(row))

    def test_three_native_otoco_group_legs_protected_on_realistic_schema(self):
        group = {
            "id": 987654321, "class": "otoco", "status": "open",
            "num_legs": 3,
            "leg": [
                {"id": 1, "symbol": "SOFI", "side": "buy", "type": "limit",
                 "quantity": 1, "exec_quantity": 1, "status": "filled",
                 "price": "14.84"},
                {"id": 2, "symbol": "SOFI", "side": "sell", "type": "limit",
                 "quantity": 1, "exec_quantity": 0, "status": "open",
                 "price": "15.36"},
                {"id": 3, "symbol": "SOFI", "side": "sell", "type": "stop",
                 "quantity": 1, "exec_quantity": 0, "status": "open",
                 "stop_price": "14.54"},
            ],
        }
        view = _view_order(group)
        self.assertEqual(view["nested_children_count_max25"], 3)
        self.assertEqual(view["nested_legs"][2]["stop"], "14.54")
        self.assertEqual(_group_view(group, "one")["state"],
                         "PAPER_ENTRY_FILLED_EXITS_ACTIVE")
        self.assertEqual(_group_view(group, "zero")["state"],
                         "UNVERIFIED")
        self.assertNotIn("987654321", json.dumps(view))

    def test_incomplete_otoco_group_not_called_protected(self):
        group = {
            "class": "otoco",
            "leg": [
                {"symbol": "SOFI", "side": "buy", "type": "limit",
                 "quantity": 1, "exec_quantity": 1, "status": "filled"},
            ],
        }
        self.assertEqual(_group_view(group, "one")["state"],
                         "CHILD_LEGS_UNVERIFIED")

    def test_real_reconciler_on_one_composite_otoco(self):
        group = {
            "id": 191100, "class": "otoco", "status": "open",
            "leg": [
                {"symbol": "SOFI", "side": "buy", "type": "limit",
                 "price": "14.84", "quantity": 1, "exec_quantity": 1,
                 "status": "filled"},
                {"symbol": "SOFI", "side": "sell", "type": "limit",
                 "price": "15.36", "quantity": 1, "exec_quantity": 0,
                 "status": "open"},
                {"symbol": "SOFI", "side": "sell", "type": "stop",
                 "stop_price": "14.54", "quantity": 1, "exec_quantity": 0,
                 "status": "open"},
            ],
        }
        tr = FakeTransport(positions=[{"symbol": "SOFI", "quantity": 1}],
                           orders=[group])
        report = examine(TradierSandbox(token="FAKE", transport=tr))
        self.assertEqual(
            report["native_reconciler"]["readiness"],
            "PROTECTED_PAPER_POSITION")
        self.assertEqual(
            report["native_reconciler"]["verified_protective_exits"], 2)
        self.assertEqual(report["native_reconciler"]["actions_sent"], 0)
        self.assertTrue(all(x[0] == "GET" for x in tr.calls))
        self.assertNotIn("191100", json.dumps(report))

    def test_broker_error_remains_sanitized(self):
        class Broken(FakeTransport):
            def __call__(self, method, path, query, form):
                if path.endswith("/orders"):
                    raise OSError("SUPER_SECRET_URL_WITH_ACCOUNT")
                return super().__call__(method, path, query, form)
        report = examine(TradierSandbox(token="fake", transport=Broken()))
        self.assertEqual(report["order_failure"]["failure"], "broker_block_or_uncertain")
        self.assertNotIn("SUPER_SECRET", json.dumps(report))

    def test_malformed_response_does_not_invent_orders(self):
        rows, state = _listify_envelope({"orders": {"order": "wtf"}},
                                         "orders", "order")
        self.assertEqual(rows, [])
        self.assertEqual(state, "malformed_records")

    def test_existing_share_with_no_orders_halts_paper_entry(self):
        tr = FakeTransport(positions=[{"symbol": "SOFI", "quantity": 1}])
        report = examine(TradierSandbox(token="FAKE", transport=tr))
        self.assertEqual(report["paper_entry_preflight"], {
            "orders_allowed": False, "state": "HALT_POSITION_EXITS_UNVERIFIED",
        })
        self.assertTrue(all(call[0] == "GET" for call in tr.calls))

    def test_existing_protected_share_remains_ineligible_for_new_entry(self):
        report = {
            "positions_shape": "single_dict", "orders_shape": "list",
            "pending_orders_count_class": "zero", "orders_count": 1,
            "orders_pagination_flags": {"at_limit": False, "total_pages_more_than_one": False},
            "total_position_count": 1,
            "native_reconciler": {"readiness": "PROTECTED_PAPER_POSITION",
                                  "verified_protective_exits": 2},
        }
        self.assertEqual(_paper_entry_preflight(report)["state"],
                         "BLOCKED_EXISTING_PROTECTED_POSITION")
        self.assertFalse(_paper_entry_preflight(report)["orders_allowed"])

    def test_unknown_broker_inventory_and_pagination_fail_closed(self):
        report = {
            "positions_shape": "empty_positions", "orders_shape": "empty_orders",
            "pending_orders_count_class": "zero", "orders_count": 0,
            "orders_pagination_flags": {"at_limit": False, "total_pages_more_than_one": False},
            "total_position_count": 0,
        }
        self.assertEqual(_paper_entry_preflight(report)["state"],
                         "FLAT_ACCOUNT_READ_ONLY_NOT_AUTHORIZED")
        report["orders_pagination_flags"]["total_pages_more_than_one"] = True
        self.assertEqual(_paper_entry_preflight(report)["state"],
                         "HALT_BROKER_STATE_UNVERIFIED")
        report["orders_pagination_flags"]["total_pages_more_than_one"] = False
        report["orders_shape"] = "malformed_records"
        self.assertEqual(_paper_entry_preflight(report)["state"],
                         "HALT_BROKER_STATE_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
