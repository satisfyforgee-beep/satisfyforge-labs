"""Tests for non-trading Tradier sandbox scanner and local paper ledger."""
import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("tradier_paper_lab", SCRIPTS / "tradier_paper_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class PaperLabTests(unittest.TestCase):
    def test_symbols_strict_and_bounded(self):
        self.assertEqual(lab.symbols_from_text("sofi, aal"), ["SOFI", "AAL"])
        for val in ("SOFI,SOFI", "SPY;rm", "SPY, A,B,C,D,E,F", "AAPL220617C00270000", ""):
            with self.subTest(val=val), self.assertRaises(ValueError):
                lab.symbols_from_text(val)

    def test_pure_getter_and_cash_sizing(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        ts = int((now - timedelta(minutes=16)).timestamp() * 1000)
        seen = []
        def get(path, token, params):
            seen.append((path, token, params))
            return {"quotes": {"quote": [
                {"symbol": "SOFI", "type": "stock", "bid": 14.20, "ask": 14.25,
                 "bid_date": ts, "ask_date": ts, "trade_date": ts},
                {"symbol": "SPY", "type": "etf", "bid": 600, "ask": 601,
                 "bid_date": ts, "ask_date": ts, "trade_date": ts}
            ]}}
        rows = lab.screen_snapshot("DO-NOT-PRINT", ["SOFI", "SPY"],
                                   Decimal("30"), now=now, getter=get)
        self.assertEqual(seen, [("/markets/quotes", "DO-NOT-PRINT",
                                 {"symbols": "SOFI,SPY", "greeks": "false"})])
        self.assertEqual(rows[0]["shares"], 2)
        self.assertEqual(rows[1]["shares"], 0)
        self.assertIn("over-budget-for-whole-share", rows[1]["flags"])
        out = io.StringIO()
        with redirect_stdout(out):
            lab.print_screen(rows, Decimal("30"))
        self.assertNotIn("DO-NOT-PRINT", out.getvalue())
        self.assertIn("delayed", out.getvalue().lower())

    def test_stale_and_missing_quote_rejected_as_flags(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        ts = int((now - timedelta(hours=2)).timestamp() * 1000)
        def get(path, token, params):
            return {"quotes": {"quote": {"symbol": "F", "type": "stock",
                                           "bid": 12, "ask": 11, "trade_date": ts}}}
        rows = lab.screen_snapshot("TEST", ["F", "AAL"], now=now, getter=get)
        self.assertIn("invalid-or-missing-bid-ask", rows[0]["flags"])
        self.assertIn("stale-or-invalid-time", rows[0]["flags"])
        self.assertIn("timestamp-unavailable", rows[1]["flags"])

    def write_rows(self, directory, rows):
        path = Path(directory) / "hypothetical.csv"
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "symbol", "action",
                                                   "shares", "bid", "ask"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def example(self, action, shares, time="2026-10-20T15:00:00Z", bid="9.90", ask="10.00"):
        return {"timestamp": time, "symbol": "SOFI", "action": action,
                "shares": shares, "bid": bid, "ask": ask}

    def test_local_replay_buy_and_partial_exit(self):
        rows = [self.example("BUY", "2"),
                self.example("SELL", "1", "2026-10-20T15:15:00Z", "11", "11.10")]
        with tempfile.TemporaryDirectory() as tmp:
            result = lab.replay_hypothetical(self.write_rows(tmp, rows), Decimal("30"))
        self.assertEqual(result["equity"], Decimal("32"))
        self.assertEqual(result["cash"], Decimal("21"))
        self.assertEqual(result["net_pnl"], Decimal("2"))
        self.assertEqual(result["realized_pnl"], Decimal("1"))
        self.assertEqual(result["unrealized_pnl"], Decimal("1"))
        self.assertEqual(result["open_positions"], 1)

    def test_fee_changes_results(self):
        rows = [self.example("BUY", "2"),
                self.example("SELL", "1", "2026-10-20T15:15:00Z", "11", "11.10")]
        with tempfile.TemporaryDirectory() as tmp:
            result = lab.replay_hypothetical(self.write_rows(tmp, rows), fee=Decimal("1"))
        self.assertEqual(result["net_pnl"], Decimal("0"))
        self.assertEqual(result["equity"], Decimal("30"))

    def test_short_margin_and_bad_data_rejected(self):
        cases = [
            [self.example("SELL", "1")],
            [self.example("BUY", "4")],
            [self.example("BUY", "1", bid="12", ask="11")],
            [self.example("BUY", "0")],
            [self.example("BUY", "1.5")],
            [self.example("BUY", "1", time="2026-10-20T15:00:00")],
            [self.example("BUY", "1", bid="NaN")],
            [self.example("BUY", "1", time="2026-10-20T16:00:00Z"),
             self.example("SELL", "1", time="2026-10-20T15:00:00Z")]
        ]
        for rows in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    lab.replay_hypothetical(self.write_rows(tmp, rows))

    def test_no_sandbox_token_needed_for_offline_ledger(self):
        rows = [self.example("BUY", "1")]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_rows(tmp, rows)
            with patch.dict(lab.os.environ, {}, clear=True):
                self.assertEqual(lab.replay_hypothetical(path)["trades"], 1)

    def test_no_orders_or_live_hostnames_in_lab(self):
        src = (SCRIPTS / "tradier_paper_lab.py").read_text()
        self.assertNotIn("api.tradier.com", src)
        self.assertNotIn("/orders", src)
        self.assertNotIn("method=\"POST\"", src)
        self.assertEqual(lab.fetch_json.__module__, "tradier_sandbox_check")


if __name__ == "__main__":
    unittest.main()
