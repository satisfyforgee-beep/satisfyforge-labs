"""Owner-authorized, one-time SOFI SANDBOX test. Entirely mocked broker."""
import contextlib
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zerocost_bot.tradier_paper import TradierSandbox, PaperBlocked, BrokerUncertain
from tradier_one_share_test import (
    DATE, SYMBOL, QTY, CAP, _APPROVAL_VAR, _APPROVAL_VALUE,
    authorized_window, execute_one_owner_approved_sandbox_trial, main,
)

NOW = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
ACCOUNT = "VA00001234"
PID = 91050


class FakeSandboxTransport:
    """Strict mock that records each POST but never contacts a real broker."""
    def __init__(self, *, price="14.75", cost="14.76",
                 clock_open=True, child_complete=True, fill=True,
                 existing_orders=False, exception_after_submit=False):
        self.price = price
        self.cost = cost
        self.clock_open = clock_open
        self.child_complete = child_complete
        self.fill = fill
        self.submitted = existing_orders
        self.exception_after_submit = exception_after_submit
        self.calls = []

    def parent(self):
        return {
            "id": PID, "status": "filled" if self.fill else "open",
            "symbol": SYMBOL, "side": "buy", "type": "limit",
            "quantity": 1, "exec_quantity": 1 if self.fill else 0,
        }

    def children(self):
        return [
            {"id": PID + 1, "status": "open", "symbol": SYMBOL,
             "side": "sell", "parent_order_id": PID,
             "type": "limit", "price": "15.28", "quantity": 1, "exec_quantity": 0},
            {"id": PID + 2, "status": "open", "symbol": SYMBOL,
             "side": "sell", "parent_order_id": PID,
             "type": "stop", "stop": "14.46", "quantity": 1, "exec_quantity": 0},
        ] if self.child_complete else []

    def __call__(self, method, path, query, form):
        self.calls.append((method, path, dict(form) if form else None))
        assert "api.tradier.com" not in path
        if method == "GET" and path == "/markets/quotes":
            return {"quotes": {"quote": {"symbol": SYMBOL, "ask": self.price}}}
        if method == "GET" and path == "/markets/clock":
            return {"clock": {"state": "open" if self.clock_open else "closed",
                              "date": DATE.isoformat()}}
        if method == "GET" and path == "/user/profile":
            return {"profile": {"account": [{"account_number": ACCOUNT}]}}
        if method == "GET" and path.endswith("/balances"):
            return {"balances": {"account_number": ACCOUNT,
                                 "total_cash": 100000,
                                 "pending_orders_count": 0}}
        if method == "GET" and path.endswith("/positions"):
            rows = [{"symbol": SYMBOL, "quantity": 1}] if self.submitted and self.fill else []
            return {"positions": {"position": rows}} if rows else {"positions": "null"}
        if method == "GET" and path.endswith("/orders"):
            if self.submitted:
                return {"orders": {"order": [self.parent()] + self.children()}}
            return {"orders": "null"}
        if method == "GET" and path.endswith("/orders/" + str(PID)):
            return {"order": self.parent()}
        if method == "GET" and path.endswith("/orders/" + str(PID + 1)):
            return {"order": self.children()[0]}
        if method == "GET" and path.endswith("/orders/" + str(PID + 2)):
            return {"order": self.children()[1]}
        if method == "POST" and path.endswith("/orders"):
            if form.get("preview") == "true":
                return {"order": {"status": "ok", "result": True,
                                  "cost": self.cost, "commission": 0, "fees": 0}}
            self.submitted = True
            if self.exception_after_submit:
                raise OSError("simulated broker connection timeout")
            return {"order": {"status": "ok", "id": PID}}
        raise AssertionError("unexpected broker request: " + method + path)

    def submitted_posts(self):
        return [x for x in self.calls if x[0] == "POST"
                and x[2].get("preview") != "true"]


def authorized_env():
    return {
        _APPROVAL_VAR: _APPROVAL_VALUE,
        "SF_TRADIER_PAPER_ENABLE": "SANDBOX_ONLY_APPROVED",
    }


def run_fake(fake, *, now=NOW):
    with tempfile.TemporaryDirectory() as tmp:
        broker = TradierSandbox(token="FAKE-ONLY", transport=fake)
        with patch.dict(os.environ, authorized_env(), clear=True):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = execute_one_owner_approved_sandbox_trial(
                    now=now, broker=broker,
                    journal_path=str(Path(tmp) / "once.sqlite3"),
                    sleep=lambda _: None, max_polls=2, poll_seconds=5)
                report_lines = [json.loads(x) for x in output.getvalue().splitlines()]
    return code, report_lines


class OneAuthorizedPaperTest(unittest.TestCase):
    def test_only_approved_day_and_clock_window(self):
        self.assertTrue(authorized_window(NOW))
        for stamp in (
            datetime(2026, 10, 21, 13, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 21, 18, 46, tzinfo=timezone.utc),
            datetime(2026, 10, 22, 14, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 20, 14, 0, tzinfo=timezone.utc),
            NOW.replace(tzinfo=None),
        ):
            self.assertFalse(authorized_window(stamp))

    def test_before_market_open_no_contact(self):
        fake = FakeSandboxTransport()
        code, reports = run_fake(
            fake, now=datetime(2026, 10, 21, 12, 30, tzinfo=timezone.utc))
        self.assertEqual(code, 0)
        self.assertEqual(reports[0]["status"], "PREMARKET_OR_OUTSIDE_APPROVED_WINDOW")
        self.assertEqual(fake.calls, [])

    def test_exact_approval_environment_required(self):
        fake = FakeSandboxTransport()
        broker = TradierSandbox(token="FAKE", transport=fake)
        with patch.dict(os.environ, {}, clear=True):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(execute_one_owner_approved_sandbox_trial(
                    now=NOW, broker=broker), 2)
        self.assertEqual(fake.calls, [])

    def test_one_valid_broker_submission_and_two_exits_reconciled(self):
        fake = FakeSandboxTransport()
        code, reports = run_fake(fake)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.submitted_posts()), 1)
        self.assertEqual(reports[0]["status"], "SUBMITTED_NOT_CONFIRMED_FILLED")
        self.assertEqual(reports[1]["status"], "BROKER_READBACK_VERIFIED")
        self.assertEqual(reports[1]["bracket_readiness"],
                         "PROTECTED_PAPER_POSITION")
        self.assertEqual(reports[1]["verified_protective_exits"], 2)
        self.assertFalse(reports[1]["live_money_trading_enabled"])
        for text in (ACCOUNT, "FAKE-ONLY", str(PID)):
            self.assertNotIn(text, json.dumps(reports))

    def test_existing_broker_orders_block_repeated_paper_entry(self):
        fake = FakeSandboxTransport(existing_orders=True)
        broker = TradierSandbox(token="FAKE", transport=fake)
        with patch.dict(os.environ, authorized_env(), clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(PaperBlocked):
                    execute_one_owner_approved_sandbox_trial(
                        now=NOW, broker=broker,
                        journal_path=str(Path(tmp)/"journal.sqlite3"),
                        sleep=lambda _: None, max_polls=1)
        self.assertEqual(fake.submitted_posts(), [])

    def test_quote_above_max_twenty_blocks(self):
        fake = FakeSandboxTransport(price="20.01")
        code, reports = run_fake(fake)
        self.assertEqual(code, 2)
        self.assertEqual(fake.submitted_posts(), [])
        self.assertEqual(reports[0]["status"], "BLOCKED")

    def test_preview_total_price_plus_fees_over_cap_blocks(self):
        fake = FakeSandboxTransport(cost="20.02")
        broker = TradierSandbox(token="FAKE", transport=fake)
        with patch.dict(os.environ, authorized_env(), clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(PaperBlocked):
                    execute_one_owner_approved_sandbox_trial(
                        now=NOW, broker=broker,
                        journal_path=str(Path(tmp)/"journal.sqlite3"),
                        sleep=lambda _: None, max_polls=1)
        self.assertEqual(fake.submitted_posts(), [])

    def test_broker_market_closed_prevents_order_even_in_time_window(self):
        fake = FakeSandboxTransport(clock_open=False)
        broker = TradierSandbox(token="FAKE", transport=fake)
        with patch.dict(os.environ, authorized_env(), clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(PaperBlocked):
                    execute_one_owner_approved_sandbox_trial(
                        now=NOW, broker=broker,
                        journal_path=str(Path(tmp)/"journal.sqlite3"),
                        sleep=lambda _: None, max_polls=1)
        self.assertEqual(fake.submitted_posts(), [])

    def test_broker_accepted_but_exit_unverifiable_requires_reconciliation(self):
        fake = FakeSandboxTransport(child_complete=False)
        code, reports = run_fake(fake)
        self.assertEqual(code, 1)
        self.assertEqual(len(fake.submitted_posts()), 1)
        self.assertEqual(reports[-1]["status"], "STOP_AND_RECONCILE")
        self.assertEqual(reports[-1]["reason_code"],
                         "protective_exits_unverified")

    def test_unknown_http_post_result_does_not_retry(self):
        fake = FakeSandboxTransport(exception_after_submit=True)
        broker = TradierSandbox(token="FAKE", transport=fake)
        with patch.dict(os.environ, authorized_env(), clear=True):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(BrokerUncertain):
                    execute_one_owner_approved_sandbox_trial(
                        now=NOW, broker=broker,
                        journal_path=str(Path(tmp)/"journal.sqlite3"),
                        sleep=lambda _: None, max_polls=1)
        self.assertEqual(len(fake.submitted_posts()), 1)

    def test_fill_not_guaranteed_from_receipt(self):
        fake = FakeSandboxTransport(fill=False)
        code, reports = run_fake(fake)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.submitted_posts()), 1)
        self.assertEqual(reports[-1]["status"], "PENDING_BROKER_FOLLOWUP")
        self.assertEqual(reports[-1]["bracket_readiness"], "AWAITING_ENTRY")

    def test_workflow_contains_only_sandbox_permissions(self):
        text = (Path(__file__).resolve().parents[2] /
                ".github/workflows/tradier-single-approved-sandbox-test.yml").read_text()
        self.assertIn("secrets.TRADIER_SANDBOX_TOKEN", text)
        self.assertIn("SF_TRADIER_PAPER_ENABLE: SANDBOX_ONLY_APPROVED", text)
        self.assertIn("SF_ONE_SHARE_TRIAL_APPROVAL: SOFI-20261021-SANDBOX-ONE-SHARE-20USD", text)
        self.assertIn("contents: read", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertNotIn("secrets.TRADIER_PRODUCTION_TOKEN", text)
        self.assertNotIn("api.tradier.com/v1", text)

    def test_invalid_cli_args_cannot_arm_test(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([]), 2)
            self.assertEqual(main(["--execute-live-trade"]), 2)

if __name__ == "__main__":
    unittest.main()
