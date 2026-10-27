"""All tests isolated to local temporary files; no quote/broker calls."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from zerocost_bot.paper_capital import PaperCapital
from zerocost_bot.paper_status import (
    get_virtual_snapshot, parse_monitor_log, parse_stock_qa_log,
    build_status,
)

T = datetime(2026, 10, 27, 10, 20, tzinfo=timezone.utc)


def record(ts=T, *, state="CHECK_COMPLETE", positions=3, liquidation="149.33"):
    return {
        "utc": ts.isoformat(), "mode": "OFFLINE_FORWARD_VIRTUAL_CRYPTO_NOT_BROKER_FILLED",
        "actual_broker_orders": 0, "actual_money_trades": 0,
        "state": state, "open_virtual_positions": positions,
        "estimated_virtual_liquidation": liquidation,
        "virtual_realized_pnl": "0.00", "virtual_cash": "105.09",
    }


class PaperDailyHealthTests(unittest.TestCase):
    def setUp(self):
        d = TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name)
        p = self.root / "crypto_virtual_forward.sqlite3"
        l = PaperCapital(str(p))
        for i, symbol in enumerate(("BTC/USD", "ETH/USD", "SOL/USD")):
            key = "trial20261026:" + symbol.replace("/", "")
            l.reserve_buy(key, "crypto", symbol, ".001", "3000", 0, when=T)
            l.buy_fill(key + ":entry", key, "crypto", symbol,
                       ".001", "3000", 0, when=T)
            l.release_terminal_reservation(key + ":filled", key, when=T)
        (self.root / "crypto_virtual_monitor.jsonl").write_text(
            json.dumps(record(T - timedelta(minutes=15))) + "\n" +
            json.dumps(record(T - timedelta(minutes=1))) + "\n"
        )
        (self.root / "forward_qa_stdout.log").write_text(
            json.dumps({"state": "OUTSIDE_PAPER_SESSION",
                        "broker_orders_sent": 0})+"\n")

    def test_current_virtual_report_keeps_accounts_independent(self):
        got = build_status(self.root, now=T)
        self.assertEqual(got["crypto_monitor"]["monitor_health"],
                         "HEALTHY_RECENT_CHECK")
        self.assertEqual(got["crypto_virtual_account"]["virtual_buys"], 3)
        self.assertEqual(got["crypto_virtual_account"]["virtual_sells"], 0)
        self.assertEqual(got["crypto_virtual_account"]["current_settled_virtual_cash"],
                         "141.00")
        self.assertEqual(got["stock_virtual_qa"]["status"], "OUTSIDE_PAPER_SESSION")
        self.assertFalse(got["stock_virtual_qa"]["merged_crypto_profits"])
        self.assertEqual(got["broker_orders_placed_by_this_report"], 0)

    def test_different_realized_pnl_log_and_ledger_warns(self):
        log = self.root / "crypto_virtual_monitor.jsonl"
        mismatch = record(T - timedelta(minutes=1))
        mismatch["virtual_realized_pnl"] = "1.00"
        log.write_text(json.dumps(mismatch) + "\n")
        got = build_status(self.root, now=T)
        self.assertEqual(got["crypto_monitor"]["monitor_health"],
                         "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE")

    def test_stale_log_causes_explicit_warning(self):
        got = parse_monitor_log(self.root / "crypto_virtual_monitor.jsonl",
                                T + timedelta(hours=2))
        self.assertEqual(got["monitor_health"], "HALTED_OR_STALE")

    def test_future_clock_refused(self):
        with self.assertRaises(ValueError):
            parse_monitor_log(self.root / "crypto_virtual_monitor.jsonl",
                              T-timedelta(days=1))

    def test_wrong_mode_or_live_order_claim_refused(self):
        path = self.root / "crypto_virtual_monitor.jsonl"
        m = record()
        m["actual_broker_orders"] = 1
        path.write_text(json.dumps(m) + "\n")
        with self.assertRaises(ValueError):
            parse_monitor_log(path, T)

    def test_unexpected_ledger_entry_denied(self):
        l = PaperCapital(str(self.root / "crypto_virtual_forward.sqlite3"))
        key = "unexpected"
        l.reserve_buy(key, "stock", "SOFI", "1", "10.00", "0", when=T)
        l.buy_fill(key+":entry", key, "stock", "SOFI", "1", "10.00", "0", when=T)
        l.release_terminal_reservation(key+":filled", key, when=T)
        with self.assertRaises(ValueError):
            get_virtual_snapshot(self.root / "crypto_virtual_forward.sqlite3")

    def test_missing_book_never_created(self):
        p = self.root / "missing.sqlite3"
        with self.assertRaises(ValueError):
            get_virtual_snapshot(p)
        self.assertFalse(p.exists())

    def test_truncated_and_missing_stock_log_are_flagged(self):
        bad = self.root / "bad.log"
        bad.write_text("garbage}\n")
        self.assertEqual(parse_stock_qa_log(bad)["status"],
                         "MALFORMED_STOCK_QA_LOG")
        self.assertEqual(parse_stock_qa_log(self.root / "other.log")["status"],
                         "LOG_UNAVAILABLE")

    def test_symlinked_monitor_log_denied(self):
        target = self.root / "crypto_virtual_monitor.jsonl"
        link = self.root / "symbolic.jsonl"
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            parse_monitor_log(link, T)

    def test_successful_sell_readback_counts(self):
        path = self.root / "crypto_virtual_forward.sqlite3"
        l = PaperCapital(str(path))
        l.sell_fill("oneexit", "crypto", "BTC/USD",
                    ".001", "3100", 0, when=T)
        l.confirm_settlement("onecompleted", "oneexit", when=T)
        parsed = get_virtual_snapshot(path)
        self.assertEqual(parsed["virtual_sells"], 1)
        self.assertEqual(len(parsed["snapshot"]["positions"]), 2)


if __name__ == "__main__":
    unittest.main()
