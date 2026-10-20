"""Offline mock tests only. Never use real or production account credentials."""
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from zerocost_bot.journal import OrderJournal
from zerocost_bot.tradier_paper import (
    SANDBOX_HOST, PaperBlocked, BrokerUncertain, TradierSandbox,
    _normalize_preview, _items, _choose_account, build_paper_otoco, _tag,
)

NOW = datetime(2026, 10, 20, 14, 0, tzinfo=timezone.utc)
# 14:00 UTC is 10:00 a.m. EDT on October 20, 2026.
ACCOUNT = "VA00001234"


def profile():
    return {"profile": {"account": [{"account_number": ACCOUNT}]}}


def balance(pending=0, cash=100000):
    return {"balances": {"account_number": ACCOUNT, "total_cash": cash,
                         "pending_orders_count": pending}}


def preview_result():
    return {"order": {"result": True, "status": "ok", "cost": 15.0,
                      "fees": 0.0, "commission": 0.0}}


class SimulatedBroker:
    """Capture requests; only mock responses; never touches a network."""

    def __init__(self, *,
                 positions=None, orders=None, pending=0, cash=100000,
                 preview=None, post=None, order_status=None):
        self.calls = []
        self.positions = positions or []
        self.orders = orders or []
        self.pending = pending
        self.cash = cash
        self.preview_response = preview or preview_result()
        self.post_response = post or {"order": {"status": "ok", "id": 74215}}
        self.order_status = order_status or {
            "order": {"id": 74215, "status": "open", "exec_quantity": 0,
                      "quantity": 1},
        }

    def __call__(self, method, path, query, form):
        self.calls.append((method, path, query, form))
        if method == "GET" and path == "/user/profile":
            return profile()
        if method == "GET" and path.endswith("/balances"):
            return balance(self.pending, self.cash)
        if method == "GET" and path.endswith("/positions"):
            return {"positions": {"position": self.positions}} if self.positions else {
                "positions": None}
        if method == "GET" and path.endswith("/orders"):
            return {"orders": {"order": self.orders}} if self.orders else {
                "orders": None}
        if method == "GET" and "/orders/" in path:
            return self.order_status
        if method == "POST" and path.endswith("/orders"):
            if form.get("preview") == "true":
                return self.preview_response
            return self.post_response
        raise AssertionError("unallowlisted broker mock request: " + method + path)


def broker(**kwargs):
    transport = SimulatedBroker(**kwargs)
    return TradierSandbox(token="not-real-test-token", transport=transport), transport


class BuilderTests(unittest.TestCase):
    def test_single_atomic_bracket_with_paper_tag(self):
        payload = build_paper_otoco(
            "SOFI", Decimal("15.20"), tag="sfpaper" + "a" * 16)
        self.assertEqual(payload["class"], "otoco")
        self.assertEqual(payload["price[0]"], "15.20")
        self.assertEqual(payload["price[1]"], "15.74")
        self.assertEqual(payload["stop[2]"], "14.89")
        self.assertEqual(payload["symbol[0]"], payload["symbol[1]"])
        self.assertEqual(payload["symbol[1]"], payload["symbol[2]"])
        self.assertEqual(payload["side[1]"], "sell")
        self.assertEqual(payload["side[2]"], "sell")
        self.assertEqual(payload["type[1]"], "limit")
        self.assertEqual(payload["type[2]"], "stop")

    def test_out_of_scope_trades_cannot_be_built(self):
        for symbol, price, qty in (
            ("SOFI", 21, 1), ("SOFI", 0, 1),
            ("SOFI", 15, 2), ("SPY_?", 15, 1),
            ("BTC/USD", 15, 1), ("SOFI", float("nan"), 1),
            ("SOFI", float("inf"), 1),
        ):
            with self.subTest(symbol=symbol, price=price, qty=qty):
                with self.assertRaises(PaperBlocked):
                    build_paper_otoco(symbol, price, quantity=qty,
                                      tag="sfpaper" + "a" * 16)

    def test_rejects_untrusted_tag_and_missing_account(self):
        with self.assertRaises(PaperBlocked):
            build_paper_otoco("SOFI", 15, tag="other")
        with self.assertRaises(PaperBlocked):
            _choose_account({"profile": {"account": []}})
        with self.assertRaises(PaperBlocked):
            _choose_account({"profile": {"account": [
                {"account_number": ACCOUNT}, {"account_number": "VA00002222"}]}})

    def test_empty_nested_records_and_broker_malformation(self):
        self.assertEqual(_items({"orders": None}, "orders", "order"), [])
        self.assertEqual(_items({"positions": "null"}, "positions", "position"), [])
        self.assertEqual(_items({"orders": "null"}, "orders", "order"), [])
        self.assertEqual(_items({"orders": {"order": "null"}}, "orders", "order"), [])
        with self.assertRaises(BrokerUncertain):
            _items({"positions": "unknown"}, "positions", "position")
        self.assertEqual(_items({"orders": {"order": {"status": "open"}}},
                                "orders", "order"), [{"status": "open"}])
        with self.assertRaises(BrokerUncertain):
            _items({"orders": {}}, "orders", "order")


class RequestTests(unittest.TestCase):
    def test_only_sandbox_hostname_is_hardcoded(self):
        self.assertEqual(SANDBOX_HOST, "https://sandbox.tradier.com/v1")
        self.assertNotIn("api.tradier.com/v1", SANDBOX_HOST)
        sb, records = broker()
        with self.assertRaises(PaperBlocked):
            sb._request("POST", "/user/profile", form={})
        with self.assertRaises(PaperBlocked):
            sb._request("GET", "https://api.tradier.com/v1/user/profile")
        with self.assertRaises(PaperBlocked):
            sb._request("GET", "/accounts/" + ACCOUNT + "/history")
        with self.assertRaises(PaperBlocked):
            sb._request("DELETE", "/accounts/" + ACCOUNT + "/orders/1")
        self.assertEqual(records.calls, [])

    def test_direct_order_request_never_bypasses_bracket_constraints(self):
        sb, tr = broker()
        tag = _tag(ACCOUNT, NOW.date(), "SOFI")
        p = build_paper_otoco("SOFI", 15, tag=tag)
        bad = dict(p, **{"side[2]": "sell_short"})
        with self.assertRaises(PaperBlocked):
            sb._request("POST", "/accounts/" + ACCOUNT + "/orders",
                        form=bad, paper_armed=True)
        self.assertEqual(tr.calls, [])

    def test_unarmed_request_is_always_preview_true(self):
        sb, tr = broker()
        payload = build_paper_otoco(
            "SOFI", 15, tag=_tag(ACCOUNT, NOW.date(), "SOFI"))
        result = sb._request("POST", "/accounts/" + ACCOUNT + "/orders",
                             form=payload)
        self.assertEqual(result["order"]["status"], "ok")
        self.assertEqual(tr.calls[-1][3]["preview"], "true")

    def test_paper_write_requires_explicit_env_gate(self):
        sb, tr = broker()
        payload = build_paper_otoco(
            "SOFI", 15, tag=_tag(ACCOUNT, NOW.date(), "SOFI"))
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PaperBlocked):
                sb._request("POST", "/accounts/" + ACCOUNT + "/orders",
                            form=payload, paper_armed=True)
        self.assertEqual(tr.calls, [])

    def test_preview_is_not_broker_order(self):
        sb, tr = broker()
        result = sb.preview("SOFI", "15.00", now=NOW)
        self.assertEqual(result["status"], "PREVIEW_OK")
        self.assertTrue(result["otoco_exits"])
        self.assertTrue(result["simulated_only"])
        self.assertEqual(len([c for c in tr.calls if c[0] == "POST"]), 1)
        self.assertEqual(tr.calls[-1][3]["preview"], "true")

    def test_preview_rejects_missing_balance_positions_or_duplicate_orders(self):
        for kwargs in (
            {"cash": 1}, {"pending": 1},
            {"positions": [{"symbol": "SOFI", "quantity": 1}]},
            {"orders": [{"status": "filled", "id": 5}]},
        ):
            sb, tr = broker(**kwargs)
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(PaperBlocked):
                    sb.preview("SOFI", 15, now=NOW)
                self.assertFalse(any(c[0] == "POST" for c in tr.calls))

    def test_disallowed_symbol_never_previews(self):
        sb, tr = broker()
        with self.assertRaises(PaperBlocked):
            sb.preview("SPY", 15, now=NOW)
        self.assertFalse(any(c[0] == "POST" for c in tr.calls))

    def test_rejects_preview_warning_and_bad_response(self):
        for payload in (
            {"order": {"result": False, "status": "ok"}},
            {"order": {"result": True, "status": "ok", "warnings": ["risk"]}},
            {"order": {"status": "ok"}},
            {"order": {"result": True, "status": "bad"}},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(PaperBlocked):
                    _normalize_preview(payload)


class PaperLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal = OrderJournal(str(Path(self.tmp.name) / "trades.sqlite3"))

    def test_no_paper_submit_without_two_gates(self):
        sb, tr = broker()
        with patch.dict(os.environ, { "SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED" }):
            with self.assertRaises(PaperBlocked):
                sb.submit_paper("SOFI", 15, self.journal, now=NOW)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(PaperBlocked):
                sb.submit_paper("SOFI", 15, self.journal,
                                explicitly_armed=True, now=NOW)
        self.assertEqual(tr.calls, [])

    def test_only_open_hours_accept_paper_submission(self):
        sb, tr = broker()
        with patch.dict(os.environ, {"SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED"}):
            with self.assertRaises(PaperBlocked):
                sb.submit_paper("SOFI", 15, self.journal,
                    explicitly_armed=True,
                    now=datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc))
        self.assertEqual(tr.calls, [])

    def test_order_submission_is_only_paper_and_never_assumed_filled(self):
        sb, tr = broker()
        with patch.dict(os.environ, {"SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED"}):
            result = sb.submit_paper("SOFI", 15, self.journal,
                                     explicitly_armed=True, now=NOW)
        self.assertEqual(result["status"], "SUBMITTED_TO_SANDBOX_NOT_A_FILL")
        self.assertTrue(result["protective_exits_requested"])
        self.assertEqual(self.journal.status(result["journal_key"])["state"],
                         "submitted")
        posts = [c for c in tr.calls if c[0] == "POST"]
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0][3]["preview"], "true")
        self.assertNotIn("preview", posts[1][3])
        with patch.dict(os.environ, {"SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED"}):
            with self.assertRaises(PaperBlocked):
                sb.submit_paper("SOFI", 15, self.journal,
                                 explicitly_armed=True, now=NOW)
        self.assertEqual(len([c for c in tr.calls if c[0] == "POST"]), 3)
        # Repeat gets a *new preview* before journal veto, but no second submit.

    def test_account_daily_cap_still_blocks_different_symbol(self):
        sb, transport = broker()
        with patch.dict(os.environ, {
                "SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED"}):
            sb.submit_paper("SOFI", 15, self.journal,
                            explicitly_armed=True, now=NOW)
            with self.assertRaises(PaperBlocked):
                sb.submit_paper("AAL", 12, self.journal,
                                explicitly_armed=True, now=NOW)
        # Both previews are harmless but just ONE sandbox submission.
        active = [c for c in transport.calls
                  if c[0] == "POST" and c[3].get("preview") != "true"]
        self.assertEqual(len(active), 1)

    def test_uncertain_submission_marks_unknown_never_retries(self):
        class Uncertain(SimulatedBroker):
            def __call__(self, method, path, query, form):
                if method == "POST" and form.get("preview") != "true":
                    raise URLError("timeout - simulated")
                return super().__call__(method, path, query, form)
        s = Uncertain()
        sb = TradierSandbox(token="fake", transport=s)
        with patch.dict(os.environ, {"SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED"}):
            with self.assertRaises(BrokerUncertain):
                sb.submit_paper("SOFI", 15, self.journal,
                                 explicitly_armed=True, now=NOW)
        from zerocost_bot.journal import order_key
        from zoneinfo import ZoneInfo
        import hashlib
        account_hash = hashlib.sha256(ACCOUNT.encode()).hexdigest()[:12]
        midnight = NOW.astimezone(ZoneInfo("America/New_York")).replace(
            hour=0, minute=0, second=0, microsecond=0)
        key = order_key("tradier-sandbox-otoco-" + account_hash,
                        "DAILY", midnight)
        found = self.journal.status(key)
        self.assertEqual(found["state"], "unknown")

    def test_readback_does_not_treat_pending_as_filled(self):
        sb, _ = broker()
        info = sb.order_readback(74215)
        self.assertEqual(info["status"], "open")
        self.assertFalse(info["is_fill_confirmed"])

    def test_partial_fill_flagged_for_reconciliation(self):
        sb, _ = broker(order_status={"order": {
            "id": 74215, "status": "partially_filled",
            "quantity": 2, "exec_quantity": 1,
        }})
        info = sb.order_readback(74215)
        self.assertTrue(info["needs_reconciliation"])
        self.assertFalse(info["is_fill_confirmed"])

    def test_broker_filled_only_when_quantities_match(self):
        sb, _ = broker(order_status={"order": {
            "id": 74215, "status": "filled",
            "quantity": 1, "exec_quantity": 1,
        }})
        self.assertTrue(sb.order_readback(74215)["is_fill_confirmed"])

    def test_mismatched_order_does_not_mark_fill(self):
        sb, _ = broker(order_status={"order": {
            "id": 74000, "status": "filled",
            "quantity": 1, "exec_quantity": 1,
        }})
        with self.assertRaises(BrokerUncertain):
            sb.order_readback(74215)


if __name__ == "__main__":
    unittest.main()
