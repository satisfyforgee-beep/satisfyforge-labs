"""Proof the local sandbox monitor fails closed and writes no secrets."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

import tradier_watch
from zerocost_bot.paper_supervisor import (
    PaperSupervisor, SupervisorReport, append_private_journal,
    verify_private_journal, write_private_report,
)
from zerocost_bot.tradier_paper import BrokerUncertain

NOW = datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc)


def response(readiness="AWAITING_ENTRY", **changes):
    obj = {
        "environment": "TRADIER_SANDBOX_ONLY",
        "readiness": readiness,
        "live_order_enabled": False,
        "order_action": "DO_NOT_TRADE",
    }
    obj.update(changes)
    return obj


class SupervisorStateTests(unittest.TestCase):
    def test_awating_entry_stays_under_research_watch(self):
        sup = PaperSupervisor(lambda: response(), clock=lambda: NOW)
        msg = sup.poll()
        self.assertEqual(msg.state, "MONITORING")
        self.assertFalse(msg.as_dict()["can_trade"])
        self.assertFalse(msg.as_dict()["live_order_enabled"])
        self.assertFalse(sup.halted)

    def test_protected_position_is_not_order_authorization(self):
        sup = PaperSupervisor(
            lambda: response("PROTECTED_PAPER_POSITION"), clock=lambda: NOW)
        out = sup.poll().as_dict()
        self.assertEqual(out["supervisor_state"], "MONITORING")
        self.assertFalse(out["paper_order_submission_enabled"])
        self.assertNotIn("profit", json.dumps(out).lower())

    def test_incomplete_protective_exits_halt_permanently(self):
        sup = PaperSupervisor(
            lambda: response("HALT_AND_RECONCILE"),
            clock=lambda: NOW)
        result = sup.poll()
        self.assertEqual(result.state, "HALTED")
        self.assertTrue(sup.halted)
        with self.assertRaises(RuntimeError):
            sup.poll()

    def test_closed_position_stops_monitoring(self):
        sup = PaperSupervisor(
            lambda: response("CLOSED_PAPER_POSITION"), clock=lambda: NOW)
        self.assertEqual(sup.poll().state, "STOPPED")
        with self.assertRaises(RuntimeError):
            sup.poll()

    def test_rejected_entry_stops_monitoring(self):
        sup = PaperSupervisor(
            lambda: response("ENTRY_NOT_FILLED"), clock=lambda: NOW)
        self.assertEqual(sup.poll().state, "STOPPED")

    def test_any_broker_timeout_stops_and_redacts_secrets(self):
        def broken():
            raise BrokerUncertain("SECRET=example-credential")
        sup = PaperSupervisor(broken, clock=lambda: NOW)
        result = sup.poll()
        self.assertEqual(result.state, "HALTED")
        self.assertNotIn("example-credential", json.dumps(result.as_dict()))

    def test_unknown_broker_exception_also_halts_safely(self):
        def broken():
            raise RuntimeError("sensitive-broker-diagnostic")
        sup = PaperSupervisor(broken, clock=lambda: NOW)
        result = sup.poll().as_dict()
        self.assertEqual(result["supervisor_state"], "HALTED")
        self.assertNotIn("sensitive-broker-diagnostic", json.dumps(result))

    def test_untrusted_response_cannot_set_order_action(self):
        for obj in (
            response("AWAITING_ENTRY", order_action="BUY"),
            response("AWAITING_ENTRY", live_order_enabled=True),
            response("AWAITING_ENTRY", environment="PRODUCTION"),
            response("BUY_EVERYTHING"),
            {},
            None,
        ):
            with self.subTest(raw=obj):
                self.assertEqual(
                    PaperSupervisor(lambda: obj, clock=lambda: NOW
                                    ).poll().state, "HALTED")

    def test_missing_timezone_fails_closed(self):
        sup = PaperSupervisor(
            lambda: response(), clock=lambda: NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            sup.poll()
        self.assertTrue(sup.halted)

    def test_market_data_does_not_override_broker_safety(self):
        raw = response("HALT_AND_RECONCILE", signal="BUY", confidence=100)
        out = PaperSupervisor(lambda: raw, clock=lambda: NOW).poll().as_dict()
        self.assertEqual(out["supervisor_state"], "HALTED")
        self.assertNotIn("signal", json.dumps(out))


class PrivateStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "owner-private"

    def test_atomic_status_contains_only_allowlisted_fields(self):
        msg = SupervisorReport(
            "MONITORING", "AWAITING_ENTRY", "No orders authorized",
            NOW.isoformat())
        path = write_private_report(msg, directory=self.root)
        self.assertTrue(path.exists())
        obj = json.loads(path.read_text())
        self.assertEqual(obj["supervisor_state"], "MONITORING")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o700)
        self.assertNotIn("account_number", path.read_text())
        self.assertNotIn("order_id", path.read_text())

    def test_status_overwrite_is_atomic(self):
        path = write_private_report(
            SupervisorReport("MONITORING", "AWAITING_ENTRY", "First",
                             NOW.isoformat()),
            directory=self.root)
        write_private_report(
            SupervisorReport("HALTED", "UNKNOWN", "Second",
                             NOW.isoformat()),
            directory=self.root)
        self.assertEqual(json.loads(path.read_text())["supervisor_state"],
                         "HALTED")

    def test_symlink_destination_is_rejected(self):
        self.root.mkdir()
        outside = Path(self.tmp.name)/"outside"
        outside.write_text("keep")
        (self.root/"paper_order_status.json").symlink_to(outside)
        with self.assertRaises(ValueError):
            write_private_report(SupervisorReport(
                "MONITORING", "AWAITING_ENTRY", "No trade", NOW.isoformat()),
                directory=self.root)
        self.assertEqual(outside.read_text(), "keep")

    def test_symlink_directory_is_rejected(self):
        other = Path(self.tmp.name)/"other"
        other.mkdir()
        self.root.symlink_to(other, target_is_directory=True)
        with self.assertRaises(ValueError):
            write_private_report(SupervisorReport(
                "MONITORING", "AWAITING_ENTRY", "No trade", NOW.isoformat()),
                directory=self.root)


class WatchCLIStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"private"

    def test_once_does_not_repeat_poll_or_write_broker(self):
        calls = []
        def fetch():
            calls.append(1)
            return response()
        result = tradier_watch.run_watch(
            "92120", "SOFI", read_function=fetch, report_dir=self.root)
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 1)
        obj = json.loads((self.root/"paper_order_status.json").read_text())
        self.assertFalse(obj["paper_order_submission_enabled"])

    def test_watcher_stops_after_broker_closes_order(self):
        seq = iter((response(), response("PROTECTED_PAPER_POSITION"),
                    response("CLOSED_PAPER_POSITION")))
        slept = []
        result = tradier_watch.run_watch(
            "92120", "SOFI", read_function=lambda: next(seq),
            report_dir=self.root, watch=True, interval_seconds=10,
            max_polls=10, sleep=lambda s: slept.append(s))
        self.assertEqual(result, 0)
        self.assertEqual(slept, [10, 10])
        obj = json.loads((self.root/"paper_order_status.json").read_text())
        self.assertEqual(obj["supervisor_state"], "STOPPED")
        audit = verify_private_journal(directory=self.root)
        self.assertTrue(audit["valid"])
        self.assertEqual(audit["entries"], 3)

    def test_watch_halts_on_first_broker_uncertainty(self):
        count = []
        def failed():
            count.append(1)
            raise BrokerUncertain("simulated error")
        code = tradier_watch.run_watch(
            "92120", "SOFI", read_function=failed,
            report_dir=self.root, watch=True, interval_seconds=10,
            max_polls=10, sleep=lambda x: self.fail("should never sleep"))
        self.assertEqual(code, 1)
        self.assertEqual(len(count), 1)

    def test_invalid_order_identifiers_refused_before_network(self):
        for bad in ("", "0", "-1", "123abc", "123/../../", "1"*22):
            with self.subTest(order_id=bad):
                with self.assertRaises(ValueError):
                    tradier_watch.run_watch(
                        bad, "SOFI", read_function=lambda: self.fail("network"),
                        report_dir=self.root)
        self.assertFalse(self.root.exists())

    def test_invalid_symbol_refused(self):
        for bad in ("btc/usd", "SOFI;", "", "F"*10):
            with self.assertRaises(ValueError):
                tradier_watch.run_watch(
                    "92120", bad, read_function=lambda: self.fail("network"),
                    report_dir=self.root)

    def test_fast_polling_not_permitted(self):
        with self.assertRaises(ValueError):
            tradier_watch.run_watch(
                "92120", "SOFI", read_function=lambda: response(),
                report_dir=self.root, watch=True, interval_seconds=1)

    def test_finite_watch_has_configured_stop(self):
        called = []
        ret = tradier_watch.run_watch(
            "92120", "SOFI",
            read_function=lambda: (called.append(1), response())[1],
            report_dir=self.root, watch=True, interval_seconds=10,
            max_polls=3, sleep=lambda _ : None)
        self.assertEqual(ret, 0)
        self.assertEqual(len(called), 3)



class DurableJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"private"

    def report(self, state="MONITORING", brokerage="AWAITING_ENTRY",
               note="Verified read-only sandbox status; no orders allowed",
               errors=0):
        return SupervisorReport(
            state, brokerage, note, NOW.isoformat(), errors)

    def test_hash_chain_preserves_sanitized_lifecycle(self):
        append_private_journal(self.report(), directory=self.root)
        append_private_journal(self.report(
            brokerage="PROTECTED_PAPER_POSITION"), directory=self.root)
        result = verify_private_journal(directory=self.root)
        self.assertTrue(result["valid"])
        self.assertEqual(result["entries"], 2)
        self.assertRegex(result["tail_hash"], r"^[0-9a-f]{64}$")
        path = self.root/"paper_order_journal.jsonl"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        rows = [json.loads(x) for x in path.read_text().splitlines()]
        self.assertEqual([x["sequence"] for x in rows], [1, 2])
        self.assertEqual(rows[1]["previous_hash"], rows[0]["event_hash"])
        serialized = path.read_text().lower()
        for forbidden in ("order_id", "account_number", "api_token", "client_tag"):
            self.assertNotIn(forbidden, serialized)

    def test_tampering_blocks_verify_and_future_append(self):
        append_private_journal(self.report(), directory=self.root)
        path = self.root/"paper_order_journal.jsonl"
        row = json.loads(path.read_text())
        row["event"]["brokerage_state"] = "CLOSED_PAPER_POSITION"
        path.write_text(json.dumps(row, sort_keys=True)+"\n")
        path.chmod(0o600)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            verify_private_journal(directory=self.root)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            append_private_journal(self.report(), directory=self.root)

    def test_truncated_or_symlinked_journal_is_refused(self):
        self.root.mkdir(mode=0o700)
        path = self.root/"paper_order_journal.jsonl"
        path.write_text('{"sequence":1}')
        path.chmod(0o600)
        with self.assertRaisesRegex(ValueError, "truncated"):
            verify_private_journal(directory=self.root)
        path.unlink()
        outside = Path(self.tmp.name)/"outside"
        outside.write_text("keep")
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlinked"):
            append_private_journal(self.report(), directory=self.root)
        self.assertEqual(outside.read_text(), "keep")
        outside.unlink()
        with self.assertRaisesRegex(ValueError, "symlinked"):
            verify_private_journal(directory=self.root)

    def test_unsanitized_reason_never_enters_journal(self):
        report = self.report(note="SECRET=should-not-be-stored")
        with self.assertRaisesRegex(ValueError, "not sanitized"):
            append_private_journal(report, directory=self.root)
        self.assertFalse((self.root/"paper_order_journal.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
