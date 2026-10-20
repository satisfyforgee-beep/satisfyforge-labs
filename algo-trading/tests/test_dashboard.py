"""Private dashboard tests: no live orders, no secret disclosure, no remote host."""
import http.client
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone

from dashboard_server import make_handler
from http.server import ThreadingHTTPServer
from zerocost_bot.dashboard_model import build_snapshot

NOW = datetime(2026, 10, 20, 17, 30, tzinfo=timezone.utc)


def report(mode="READ_ONLY_RESEARCH", timestamp=NOW):
    return {
        "mode": mode, "at_utc": timestamp.isoformat(),
        "secret_api_token": "SHOULD_NEVER_BE_EXPOSED",
        "account_number": "SHOULD_NEVER_BE_EXPOSED",
        "notes": ["SHOULD_NEVER_BE_EXPOSED"],
        "reports": [
            {"symbol": "SOFI", "source": "tradier_live",
             "asset": "stock", "coverage": "consolidated", "status": "DATA_READY",
             "bid": 14.60, "ask": 14.61,
             "api_key": "SHOULD_NEVER_BE_EXPOSED"},
            {"symbol": "BTC/USD", "source": "kraken_public",
             "asset": "crypto", "coverage": "single_venue", "status": "RESEARCH_ONLY",
             "bid": 82600, "ask": 82610},
        ]
    }


class SnapshotTests(unittest.TestCase):
    def _path(self, obj):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name, "feed.json")
        path.write_text(json.dumps(obj), encoding="utf-8")
        return str(path)

    def test_disconnected_is_truthfully_off(self):
        view = build_snapshot(now=NOW)
        self.assertEqual(view["market"]["status"], "NO_FEED")
        self.assertFalse(view["execution"]["live_enabled"])
        self.assertFalse(view["execution"]["broker_connected"])
        self.assertIsNone(view["performance"]["verified_net_pnl"])
        self.assertIsNone(view["performance"]["verified_win_rate_pct"])

    def test_live_report_sanitizes_secrets_and_does_not_arm_trading(self):
        view = build_snapshot(self._path(report()), now=NOW)
        serialized = json.dumps(view)
        self.assertNotIn("SHOULD_NEVER_BE_EXPOSED", serialized)
        self.assertNotIn("account_number", serialized)
        self.assertEqual(view["market"]["status"], "READ_ONLY")
        self.assertEqual(view["market"]["quotes"][0]["data_status"], "DATA_READY")
        self.assertFalse(view["execution"]["live_enabled"])
        self.assertFalse(view["market"]["quotes"][0]["live_order_authorized"])

    def test_synthetic_is_never_misrepresented_as_live(self):
        view = build_snapshot(self._path(report(mode="SYNTHETIC_TEST_ONLY")),
                              now=NOW)
        self.assertEqual(view["market"]["status"], "SYNTHETIC")
        self.assertTrue(view["market"]["is_synthetic"])
        self.assertTrue(all(q["data_status"] == "SYNTHETIC"
                            for q in view["market"]["quotes"]))

    def test_stale_and_future_report_fail_closed(self):
        too_old = report(timestamp=NOW - timedelta(seconds=16))
        view = build_snapshot(self._path(too_old), now=NOW)
        self.assertEqual(view["market"]["status"], "STALE")
        self.assertTrue(all(q["data_status"] == "STALE"
                            for q in view["market"]["quotes"]))
        future = report(timestamp=NOW + timedelta(seconds=1))
        view = build_snapshot(self._path(future), now=NOW)
        self.assertEqual(view["market"]["status"], "INVALID")

    def test_missing_malformed_and_oversized_fail_closed(self):
        self.assertEqual(build_snapshot(self._path({"mode": "LIVE_ENABLED"}),
                                        now=NOW)["market"]["status"], "INVALID")
        self.assertEqual(build_snapshot(self._path([1, 2]), now=NOW)
                         ["market"]["status"], "NO_FEED")
        big = report()
        big["padding"] = "x" * 300000
        self.assertEqual(build_snapshot(self._path(big), now=NOW)
                         ["market"]["status"], "NO_FEED")
        self.assertEqual(build_snapshot("/not/a/real/report.json", now=NOW)
                         ["market"]["status"], "NO_FEED")

    def test_invalid_prices_symbols_sources_are_omitted(self):
        bad = report()
        bad["reports"].extend([
            {"symbol": "<script>alert(1)</script>", "source": "tradier_live",
             "asset": "stock", "coverage": "consolidated",
             "status": "DATA_READY", "bid": 14, "ask": 14.01},
            {"symbol": "BAD", "source": "untrusted_free_data",
             "asset": "stock", "coverage": "consolidated",
             "status": "DATA_READY", "bid": 14, "ask": 14.01},
            {"symbol": "NAN", "source": "tradier_live",
             "asset": "stock", "coverage": "consolidated",
             "status": "DATA_READY", "bid": float("nan"), "ask": 14.01},
            {"symbol": "CROSSED", "source": "tradier_live",
             "asset": "stock", "coverage": "consolidated",
             "status": "DATA_READY", "bid": 16, "ask": 14},
        ])
        view = build_snapshot(self._path(bad), now=NOW)
        self.assertEqual(len(view["market"]["quotes"]), 2)
        self.assertNotIn("<script>", json.dumps(view))


class PrivatePaperMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _paper_path(self, *, state="MONITORING", broker="AWAITING_ENTRY",
                    at=NOW, **overrides):
        obj = {
            "schema_version": 1,
            "environment": "TRADIER_SANDBOX_ONLY",
            "supervisor_state": state, "brokerage_state": broker,
            "checked_at_utc": at.isoformat(),
            "paper_order_submission_enabled": False,
            "live_order_enabled": False, "can_trade": False,
            "user_account": "PRIVATE-NOT-FOR-DASHBOARD",
            "order_id": "PRIVATE-NOT-FOR-DASHBOARD",
            "secret_api_key": "PRIVATE-NOT-FOR-DASHBOARD",
            "reason": "PRIVATE-NOT-FOR-DASHBOARD",
        }
        obj.update(overrides)
        f = self.root / "paper-status.json"
        f.write_text(json.dumps(obj))
        return str(f)

    def test_absent_monitor_is_not_connected(self):
        d = build_snapshot(now=NOW)
        self.assertEqual(d["paper_monitor"]["status"], "NOT_CONNECTED")
        self.assertFalse(d["paper_monitor"]["live_order_enabled"])

    def test_fresh_readonly_monitor_is_sanitized(self):
        d = build_snapshot(
            now=NOW, monitor_report_path=self._paper_path())
        item = d["paper_monitor"]
        self.assertEqual(item["status"], "MONITORING")
        self.assertEqual(item["brokerage_state"], "AWAITING_ENTRY")
        self.assertFalse(item["can_trade"])
        self.assertNotIn("PRIVATE-NOT-FOR-DASHBOARD", json.dumps(d))
        self.assertNotIn("user_account", json.dumps(d))

    def test_stale_monitor_never_appears_active(self):
        older = NOW - timedelta(seconds=31)
        d = build_snapshot(now=NOW,
            monitor_report_path=self._paper_path(at=older))
        self.assertEqual(d["paper_monitor"]["status"], "STALE")
        self.assertFalse(d["paper_monitor"]["live_order_enabled"])

    def test_halted_monitor_preserves_halt(self):
        d = build_snapshot(now=NOW,
            monitor_report_path=self._paper_path(
                state="HALTED", broker="HALT_AND_RECONCILE"))
        self.assertEqual(d["paper_monitor"]["status"], "HALTED")
        self.assertIn("manual", d["paper_monitor"]["message"].lower())

    def test_invalid_mode_or_execution_flag_rejected(self):
        variations = (
            {"environment": "PRODUCTION"},
            {"live_order_enabled": True},
            {"paper_order_submission_enabled": True},
            {"can_trade": True},
            {"supervisor_state": ["MONITORING"]},
            {"brokerage_state": {"status": "AWAITING_ENTRY"}},
            {"schema_version": True},
            {"supervisor_state": "STOPPED"},
        )
        for k in variations:
            with self.subTest(k=k):
                path = self._paper_path(**k)
                self.assertEqual(
                    build_snapshot(now=NOW,monitor_report_path=path)
                    ["paper_monitor"]["status"], "INVALID")

class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(report_path=None))
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1",
                                          self.server.server_address[1],
                                          timeout=3)
        conn.request(method, path, headers=headers or {})
        response = conn.getresponse()
        status, hdrs, body = response.status, response.headers, response.read()
        conn.close()
        return status, hdrs, body

    def test_health_route_no_secrets(self):
        status, headers, body = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertIn(b"local_read_only", body)
        self.assertEqual(headers.get("Cache-Control"), "no-store, max-age=0")

    def test_api_reports_disabled_and_protects_content(self):
        status, headers, body = self.request("GET", "/api/status")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertFalse(payload["execution"]["live_enabled"])
        self.assertFalse(payload["execution"]["paper_enabled"])
        self.assertIsNone(payload["performance"]["verified_net_pnl"])
        self.assertIn("frame-ancestors 'none'",
                      headers.get("Content-Security-Policy"))

    def test_assets_stay_allowlisted(self):
        for path, expected in [("/", b"SatisfyForge Trading"),
                               ("/styles.css", b".app-shell"),
                               ("/app.js", b"function refresh")]:
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(expected, body)
        for path in ("/private.env", "/anything-else", "/../README.md"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)

    def test_mutations_are_never_supported(self):
        for method in ("POST", "PUT", "DELETE"):
            with self.subTest(method=method):
                status, _, body = self.request(method, "/api/status")
                self.assertEqual(status, 405)
                self.assertIn(b"Read-only", body)

    def test_rejects_host_header_rebinding(self):
        status, _, _ = self.request(
            "GET", "/api/status", headers={"Host": "evil.example"})
        self.assertEqual(status, 403)

    def test_head_has_no_body(self):
        status, _, body = self.request("HEAD", "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")


if __name__ == "__main__":
    unittest.main()
