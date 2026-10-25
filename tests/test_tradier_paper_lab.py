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


class BroadScannerTests(unittest.TestCase):
    def quote(self, symbol, now, **overrides):
        stamp = int((now - timedelta(minutes=16)).timestamp() * 1000)
        row = {"symbol": symbol, "type": "stock", "bid": "9.99", "ask": "10.00",
               "bid_date": stamp, "ask_date": stamp, "trade_date": stamp,
               "volume": 1_000_000, "average_volume": 2_000_000,
               "bidsize": 10, "asksize": 12}
        row.update(overrides)
        return row

    def test_universe_strict_bounded_and_file_safe(self):
        self.assertEqual(lab.symbols_from_text("sofi, aal"), ["SOFI", "AAL"])
        with self.assertRaises(ValueError):
            lab.symbols_from_text(",".join("S" + str(x) for x in range(501)))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "symbols.txt"
            good.write_text("# sectors\nSOFI,AAL\nF\n")
            self.assertEqual(lab.symbols_from_file(good), ["SOFI", "AAL", "F"])
            link = root / "link.txt"
            link.symlink_to(good)
            with self.assertRaisesRegex(ValueError, "non-symlinked"):
                lab.symbols_from_file(link)

    def test_123_symbols_are_batched_without_loss(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        symbols = [chr(65 + a) + chr(65 + b) + chr(65 + c)
                   for a in range(5) for b in range(5) for c in range(5)][:123]
        calls = []
        def get(path, token, params):
            batch = params["symbols"].split(",")
            calls.append(batch)
            return {"quotes": {"quote": [self.quote(s, now) for s in batch]}}
        rows = lab.screen_snapshot("SECRET", symbols, Decimal("30"), now=now, getter=get)
        self.assertEqual([len(x) for x in calls], [50, 50, 23])
        self.assertEqual([r["symbol"] for r in rows], symbols)
        self.assertTrue(all(r["eligible"] for r in rows))

    def test_liquidity_spread_staleness_and_missing_quote_fail_closed(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        stale = int((now - timedelta(hours=2)).timestamp() * 1000)
        def get(path, token, params):
            return {"quotes": {"quote": [
                self.quote("GOOD", now),
                self.quote("WIDE", now, bid="9.00"),
                self.quote("THIN", now, average_volume=10_000),
                self.quote("STALE", now, bid_date=stale),
            ]}}
        rows = lab.screen_snapshot("SECRET", ["GOOD", "WIDE", "THIN", "STALE", "MISS"],
                                   now=now, getter=get)
        by_symbol = {r["symbol"]: r for r in rows}
        self.assertTrue(by_symbol["GOOD"]["eligible"])
        self.assertIn("wide-spread", by_symbol["WIDE"]["flags"])
        self.assertIn("low-average-volume", by_symbol["THIN"]["flags"])
        self.assertIn("stale-or-invalid-time", by_symbol["STALE"]["flags"])
        self.assertIn("liquidity-unavailable", by_symbol["MISS"]["flags"])
        self.assertEqual([r["symbol"] for r in lab.rank_research_candidates(rows)], ["GOOD"])

    def test_ranking_is_deterministic_and_output_aggregated(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        def get(path, token, params):
            return {"quotes": {"quote": [
                self.quote("BBBB", now, bid="9.98", average_volume=9_000_000),
                self.quote("AAAA", now, bid="9.99", average_volume=1_000_000),
            ]}}
        rows = lab.screen_snapshot("SECRET", ["BBBB", "AAAA"], now=now, getter=get)
        self.assertEqual([r["symbol"] for r in lab.rank_research_candidates(rows)], ["AAAA", "BBBB"])
        out = io.StringIO()
        with redirect_stdout(out):
            lab.print_screen(rows, Decimal("30"), top=1)
        text = out.getvalue()
        self.assertIn("scanned=2 eligible=2 rejected=0", text)
        self.assertIn("predicts neither direction nor profit", text)
        self.assertNotIn("SECRET", text)

    def test_provider_duplicate_is_rejected(self):
        now = datetime(2026, 10, 20, 19, 0, tzinfo=timezone.utc)
        def get(path, token, params):
            return {"quotes": {"quote": [self.quote("SOFI", now), self.quote("SOFI", now)]}}
        with self.assertRaisesRegex(ValueError, "duplicate quote"):
            lab.screen_snapshot("SECRET", ["SOFI"], now=now, getter=get)

    def test_no_order_or_production_route(self):
        source = (SCRIPTS / "tradier_paper_lab.py").read_text()
        for forbidden in ("api.tradier.com", '"/orders"', "method=\"POST\"", "submit_order"):
            self.assertNotIn(forbidden, source)

    def write_rows(self, directory, rows):
        path = Path(directory) / "hypothetical.csv"
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "timestamp", "symbol", "action", "shares", "bid", "ask"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def example(self, action, shares, time="2026-10-20T15:00:00Z",
                bid="9.90", ask="10.00"):
        return {"timestamp": time, "symbol": "SOFI", "action": action,
                "shares": shares, "bid": bid, "ask": ask}

    def test_local_replay_buy_and_partial_exit(self):
        rows = [self.example("BUY", "2"),
                self.example("SELL", "1", "2026-10-20T15:15:00Z", "11", "11.10")]
        with tempfile.TemporaryDirectory() as tmp:
            result = lab.replay_hypothetical(self.write_rows(tmp, rows), Decimal("30"))
        self.assertEqual(result["equity"], Decimal("32"))
        self.assertEqual(result["net_pnl"], Decimal("2"))
        self.assertEqual(result["realized_pnl"], Decimal("1"))
        self.assertEqual(result["open_positions"], 1)

    def test_fee_changes_results(self):
        rows = [self.example("BUY", "2"),
                self.example("SELL", "1", "2026-10-20T15:15:00Z", "11", "11.10")]
        with tempfile.TemporaryDirectory() as tmp:
            result = lab.replay_hypothetical(
                self.write_rows(tmp, rows), fee=Decimal("1"))
        self.assertEqual(result["net_pnl"], Decimal("0"))

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
             self.example("SELL", "1", time="2026-10-20T15:00:00Z")],
        ]
        for rows in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    lab.replay_hypothetical(self.write_rows(tmp, rows))

    def test_no_token_needed_for_offline_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_rows(tmp, [self.example("BUY", "1")])
            with patch.dict(lab.os.environ, {}, clear=True):
                self.assertEqual(lab.replay_hypothetical(path)["trades"], 1)


if __name__ == "__main__":
    unittest.main()
