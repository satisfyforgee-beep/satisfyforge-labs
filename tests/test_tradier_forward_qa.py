"""Offline contract tests for virtual-only forward paper execution QA."""
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tradier_forward_qa as qa

T0 = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)


def row(symbol, now=T0, *, bid="9.99", ask="10.00",
        age=16, eligible=True):
    return {
        "symbol": symbol, "bid": Decimal(bid), "ask": Decimal(ask),
        "spread_pct": Decimal("0.1"), "spread_cost": Decimal("0.01"),
        "average_volume": 2_000_000, "eligible": eligible,
        "flags": [] if eligible else ["wide-spread"],
        "asof_utc": (now - timedelta(minutes=age)).isoformat(),
    }


class ForwardQATests(unittest.TestCase):
    def test_default_is_private_virtual_150_budget(self):
        book = qa.empty_book()
        self.assertEqual(qa.validate_book(book), book)
        self.assertEqual(book["cash"], "150.00")
        self.assertEqual(book["entries"], 0)
        source = (SCRIPTS / "tradier_forward_qa.py").read_text()
        self.assertNotIn("/orders", source)
        self.assertNotIn("method=\"POST\"", source)
        self.assertNotIn("api.tradier.com", source)

    def test_opens_five_one_share_positions_deterministically_at_ask_plus_costs(self):
        symbols = ["AAL", "F", "CLF", "PLTR", "SOFI", "ABC", "XYZ"]
        book = qa.empty_book()
        result = qa.virtual_step(book, [row(s) for s in symbols], T0,
                                 market_open=True)
        self.assertEqual(result["opened"], 5)
        self.assertEqual(result["closed"], 0)
        self.assertEqual(result["broker_orders_sent"], 0)
        self.assertEqual(book["entries"], 5)
        self.assertEqual(set(book["positions"]), {"AAL", "F", "CLF", "PLTR", "ABC"})
        self.assertNotIn("SOFI", book["positions"])
        self.assertEqual(Decimal(book["cash"]), Decimal("99.90"))
        self.assertEqual(result["liquidation_equity_virtual_est"], "149.75")
        self.assertEqual(result["net_pnl_virtual_est"], "-0.25")
        self.assertTrue(all(e["simulated_not_broker_fill"] for e in book["events"]))
        self.assertEqual(qa.virtual_step(book, [row(s) for s in symbols], T0,
                                         market_open=True)["opened"], 0)
        self.assertEqual(len(book["events"]), 5)

    def test_missing_market_clock_weekend_and_entry_window_fail_closed(self):
        rows = [row("AAL")]
        for now, isopen in ((T0, False),
                            (datetime(2026, 10, 25, 15, tzinfo=timezone.utc), True),
                            (datetime(2026, 10, 26, 19, tzinfo=timezone.utc), True)):
            book = qa.empty_book()
            result = qa.virtual_step(book, rows, now, market_open=isopen)
            self.assertEqual(result["opened"], 0)
            self.assertEqual(book["cash"], "150.00")

    def test_cap_stale_wide_cheap_and_negative_inputs(self):
        book = qa.empty_book()
        candidates = [
            row("BIG", bid="29.99", ask="30.00"),
            row("OVER", bid="30.01", ask="30.02"),
            row("STALE", age=45),
            row("WIDE", eligible=False),
            row("SOFI"),
        ]
        result = qa.virtual_step(book, candidates, T0, market_open=True)
        self.assertEqual(result["opened"], 0)
        self.assertEqual(book["entries"], 0)
        self.assertEqual(book["cash"], "150.00")

    def test_stop_exit_uses_bid_less_slippage_and_fee(self):
        book = qa.empty_book()
        qa.virtual_step(book, [row("AAL")], T0, market_open=True)
        next_time = T0 + timedelta(minutes=45)
        after = qa.virtual_step(book, [row("AAL", next_time, bid="9.50", ask="9.51")],
                                next_time, market_open=True)
        self.assertEqual(after["closed"], 1)
        self.assertEqual(after["opened"], 0)
        self.assertEqual(book["entries"], 1)
        self.assertEqual(book["positions"], {})
        self.assertEqual(Decimal(book["cash"]), Decimal("149.46"))
        self.assertEqual(book["events"][-1]["reason"], "STOP")
        self.assertEqual(book["events"][-1]["virtual_price"], "9.49")
        self.assertEqual(Decimal(book["events"][-1]["realized_pnl"]), Decimal("-0.54"))

    def test_target_only_on_later_snapshot_and_no_reentry(self):
        book = qa.empty_book()
        qa.virtual_step(book, [row("AAL")], T0, market_open=True)
        same = qa.virtual_step(book, [row("AAL", T0, bid="12.00", ask="12.01")],
                               T0, market_open=True)
        self.assertEqual(same["closed"], 0)
        next_time = T0 + timedelta(minutes=40)
        result = qa.virtual_step(book, [row("AAL", next_time, bid="10.50", ask="10.51")],
                                 next_time, market_open=True)
        self.assertEqual(result["closed"], 1)
        self.assertEqual(result["opened"], 0)
        self.assertEqual(book["entries"], 1)
        self.assertEqual(book["events"][-1]["reason"], "TARGET")

    def test_reject_malformed_or_duplicate_quotes_without_mutation(self):
        book = qa.empty_book()
        with self.assertRaises(ValueError):
            qa.virtual_step(book, [row("AAL"), row("AAL")], T0, market_open=True)
        self.assertEqual(book, qa.empty_book())

    def test_ledger_tampering_rejected(self):
        book = qa.empty_book()
        book["entries"] = 1
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            qa.validate_book(book)
        book["entries"] = 0
        book["cash"] = "-1"
        with self.assertRaisesRegex(ValueError, "cash"):
            qa.validate_book(book)

    def test_clock_and_quote_reads_only_atomic_private_journal_and_replay(self):
        with tempfile.TemporaryDirectory() as home:
            path = Path(home) / "trading" / "qa.json"
            symbols = ["AAL", "CLF", "F", "PLTR", "SOFI", "XYZ"]
            calls = []
            def fake(pathpart, token, params=None):
                self.assertEqual(token, "FAKE_SECRET")
                calls.append(pathpart)
                if pathpart == "/markets/clock":
                    return {"clock": {"state": "open", "date": "2026-10-26"}}
                if pathpart == "/markets/quotes":
                    syms = params["symbols"].split(",")
                    stamped = int((T0 - timedelta(minutes=16)).timestamp() * 1000)
                    return {"quotes": {"quote": [
                        {"symbol": s, "type": "stock", "bid": "9.99",
                         "ask": "10.00", "average_volume": 2_000_000,
                         "volume": 1_000_000, "bidsize": 100,
                         "asksize": 100, "bid_date": stamped,
                         "ask_date": stamped, "trade_date": stamped}
                        for s in syms]}}
                raise AssertionError("Unexpected route")
            first = qa.run_once(path, "FAKE_SECRET", symbols, T0, getter=fake)
            self.assertEqual(first["opened"], 5)
            self.assertEqual(first["broker_orders_sent"], 0)
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            self.assertEqual(path.parent.stat().st_mode & 0o077, 0)
            self.assertNotIn("FAKE_SECRET", path.read_text())
            before = path.read_bytes()
            again = qa.run_once(path, "FAKE_SECRET", symbols, T0, getter=fake)
            self.assertEqual(again["opened"], 0)
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(calls, ["/markets/clock", "/markets/quotes",
                                     "/markets/clock", "/markets/quotes"])

    def test_broker_clock_closed_does_not_touch_existing_file(self):
        with tempfile.TemporaryDirectory() as home:
            path = Path(home) / "trading" / "state.json"
            def fake(route, token, params=None):
                self.assertEqual(route, "/markets/clock")
                return {"clock": {"state": "closed", "date": "2026-10-26"}}
            result = qa.run_once(path, "FAKE_SECRET", ["AAL"], T0, getter=fake)
            self.assertEqual(result["state"], "MARKET_CLOSED_OR_UNVERIFIED")
            self.assertFalse(path.exists())

    def test_symlink_existing_journal_blocked(self):
        with tempfile.TemporaryDirectory() as home:
            root = Path(home) / "private"
            root.mkdir(mode=0o700)
            victim = Path(home) / "victim.json"
            victim.write_text("{}")
            path = root / "qa.json"
            path.symlink_to(victim)
            with self.assertRaisesRegex(ValueError, "Symlink"):
                qa.run_once(path, "FAKE", ["AAL"], T0)
            self.assertEqual(victim.read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
