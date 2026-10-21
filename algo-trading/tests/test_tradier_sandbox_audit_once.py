"""Offline contract tests: one-shot SANDBOX audit can perform GETs ONLY."""
import json
import unittest

from zerocost_bot.tradier_paper import TradierSandbox
from tradier_sandbox_audit_once import examine, _view_order, _listify_envelope


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


if __name__ == "__main__":
    unittest.main()
