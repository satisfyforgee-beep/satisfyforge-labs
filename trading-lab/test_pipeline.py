import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path
from unittest import mock

from paper_engine import Instrument, PaperEngine, Quote, RiskPolicy
from pipeline import Bar, evaluate_equity_breakout, safety_readiness, stable_signal_id


START = datetime(2026, 10, 27, 13, 30, tzinfo=timezone.utc)


def breakout_bars(symbol="DEMO"):
    bars = [Bar(symbol, START + timedelta(minutes=i), 10, 10, 10, 10, 100)
            for i in range(13)]
    bars.append(Bar(symbol, START + timedelta(minutes=13), 11, 11, 11, 11, 10000))
    bars.append(Bar(symbol, START + timedelta(minutes=14), 11.1, 11.1, 11.1, 11.1, 10000))
    return bars


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "journal.sqlite"
        self.journal = PaperEngine(self.path, D("500"), RiskPolicy(D("70"), D("150"), D("150")))
        self.now = START + timedelta(minutes=15, seconds=10)
        self.instrument = Instrument("DEMO", "equity")
        self.quote = Quote(self.instrument, D("11.09"), D("11.12"),
                           self.now - timedelta(seconds=2), "TEST_IEX")

    def test_completed_signal_is_persisted_once_with_provenance(self):
        first = evaluate_equity_breakout(self.journal, breakout_bars(), self.quote, self.now)
        second = evaluate_equity_breakout(self.journal, breakout_bars(), self.quote, self.now)
        self.assertEqual(first, second)
        self.assertEqual(first["action"], "PAPER_FILLED")
        self.assertEqual(len(self.journal.orders()), 1)
        record = self.journal.orders()[0]
        self.assertEqual(record["quote_source"], "TEST_IEX")
        self.assertEqual(record["quote_bid"], "11.09")
        self.assertEqual(record["quote_ask"], "11.12")
        self.assertEqual(record["signal_id"], first["signal_id"])
        self.assertEqual(record["quote_delayed"], 0)
        self.assertTrue(record["quote_asof"].startswith("2026-10-27T13:45"))

    def test_changed_limit_on_same_signal_fails_closed(self):
        evaluate_equity_breakout(self.journal, breakout_bars(), self.quote, self.now)
        moved = Quote(self.instrument, D("11.10"), D("11.13"), self.now, "TEST_IEX")
        with self.assertRaisesRegex(ValueError, "Client ID reused"):
            evaluate_equity_breakout(self.journal, breakout_bars(), moved, self.now)
        self.assertEqual(len(self.journal.orders()), 1)

    def test_delayed_quote_is_recorded_as_rejected_not_filled(self):
        delayed = Quote(self.instrument, D("11.09"), D("11.12"), self.now, "TEST_DELAYED", True)
        result = evaluate_equity_breakout(self.journal, breakout_bars(), delayed, self.now)
        self.assertEqual(result["action"], "PAPER_REJECTED")
        self.assertEqual(self.journal.orders()[0]["quote_delayed"], 1)
        self.assertEqual(self.journal.snapshot()["positions"], [])

    def test_no_signal_or_stale_bar_causes_no_order(self):
        flat = breakout_bars()
        flat[-2] = Bar("DEMO", flat[-2].time, 10, 10, 10, 10, 100)
        flat[-1] = Bar("DEMO", flat[-1].time, 10, 10, 10, 10, 100)
        a = evaluate_equity_breakout(self.journal, flat, self.quote, self.now)
        b = evaluate_equity_breakout(self.journal, breakout_bars(), self.quote,
                                     self.now + timedelta(minutes=4))
        self.assertEqual((a["action"], b["action"]), ("SKIP", "SKIP"))
        self.assertEqual(self.journal.orders(), [])

    def test_unclosed_bar_or_old_quote_causes_no_order(self):
        too_early = START + timedelta(minutes=14, seconds=20)
        early_quote = Quote(self.instrument, D("11.09"), D("11.12"), too_early, "TEST_IEX")
        a = evaluate_equity_breakout(self.journal, breakout_bars(), early_quote, too_early)
        b = evaluate_equity_breakout(self.journal, breakout_bars(), early_quote, self.now)
        self.assertEqual(a["action"], "SKIP")
        self.assertEqual(b["action"], "SKIP")
        self.assertEqual(self.journal.orders(), [])

    def test_emergency_pause_blocks_paper_order(self):
        with mock.patch.dict(os.environ, {"SF_TRADING_PAUSED": "true"}):
            result = evaluate_equity_breakout(self.journal, breakout_bars(), self.quote, self.now)
            health = safety_readiness()
        self.assertEqual(result["action"], "SKIP")
        self.assertTrue(health["emergency_pause"])
        self.assertFalse(health["broker_order_submission_enabled"])
        self.assertFalse(health["live_money_enabled"])

    def test_insufficient_budget_and_mixed_symbol_do_not_trade(self):
        tight = PaperEngine(Path(self.path.parent) / "tight.sqlite", D("500"),
                            RiskPolicy(D("1"), D("10"), D("10")))
        a = evaluate_equity_breakout(tight, breakout_bars(), self.quote, self.now)
        mixed = breakout_bars()
        mixed[3] = Bar("OTHER", mixed[3].time, 10, 10, 10, 10, 100)
        b = evaluate_equity_breakout(self.journal, mixed, self.quote, self.now)
        self.assertEqual(a["action"], "SKIP")
        self.assertEqual(b["action"], "SKIP")

    def test_signal_identity_is_timezone_invariant(self):
        from datetime import timedelta as td, timezone as tz
        a = stable_signal_id("DEMO", START)
        b = stable_signal_id("demo", START.astimezone(tz(td(hours=-4))))
        self.assertEqual(a, b)

    def test_existing_v01_database_is_migrated_without_erasure(self):
        legacy = Path(self.path.parent) / "legacy.sqlite"
        with sqlite3.connect(legacy) as conn:
            conn.execute("""CREATE TABLE orders (
                client_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL,
                timestamp TEXT NOT NULL, symbol TEXT NOT NULL, asset TEXT NOT NULL,
                side TEXT NOT NULL, quantity TEXT NOT NULL, status TEXT NOT NULL,
                reason TEXT NOT NULL, fill_price TEXT, fee TEXT,
                realized_pnl TEXT NOT NULL DEFAULT '0')""")
            conn.execute("INSERT INTO orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                         ("previous", "hash", START.isoformat(), "DEMO", "equity",
                          "buy", "1", "NOT_FILLED", "old", None, "0", "0"))
        upgraded = PaperEngine(legacy, D("100"), self.journal.policy)
        self.assertEqual(upgraded.orders()[0]["client_id"], "previous")
        self.assertIn("quote_source", upgraded.orders()[0])


if __name__ == "__main__":
    unittest.main()
