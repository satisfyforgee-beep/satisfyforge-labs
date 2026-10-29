"""All tests isolated to local temporary files; no quote/broker calls."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest

from zerocost_bot.paper_capital import PaperCapital
from zerocost_bot.paper_status import (
    get_virtual_snapshot, get_stock_virtual_snapshot,
    parse_monitor_log, parse_stock_qa_log, build_status,
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


def stock_book():
    checked = (T - timedelta(minutes=2)).isoformat()
    quoted = (T - timedelta(minutes=17)).isoformat()
    return {
        "version": 1, "initial_cash": "150.00", "cash": "139.47",
        "entries": 2,
        "positions": {
            "F": {
                "quantity": 1, "basis": "11.01", "entry_quote_at": quoted,
                "stop_bid": "10.78", "target_bid": "11.38",
            },
        },
        "events": [
            {
                "action": "BUY", "symbol": "AAL", "quantity": 1,
                "virtual_price": "10.00", "fee": "0.01",
                "virtual_debit": "10.01", "checked_at": checked,
                "quote_at": quoted, "simulated_not_broker_fill": True,
                "policy": "spread_liquidity_execution_QA_not_directional_signal",
            },
            {
                "action": "BUY", "symbol": "F", "quantity": 1,
                "virtual_price": "11.00", "fee": "0.01",
                "virtual_debit": "11.01", "checked_at": checked,
                "quote_at": quoted, "simulated_not_broker_fill": True,
                "policy": "spread_liquidity_execution_QA_not_directional_signal",
            },
            {
                "action": "SELL", "symbol": "AAL", "quantity": 1,
                "virtual_price": "10.50", "fee": "0.01",
                "realized_pnl": "0.48", "reason": "TARGET",
                "checked_at": checked, "quote_at": quoted,
                "simulated_not_broker_fill": True,
            },
        ],
    }


def completed_stock_book():
    checked = (T - timedelta(hours=3)).isoformat()
    quoted = (T - timedelta(hours=3, minutes=15)).isoformat()
    symbols = ("PFE", "T", "CLF", "CCL", "RIOT")
    events = []
    for symbol in symbols:
        events.append({
            "action": "BUY", "symbol": symbol, "quantity": 1,
            "virtual_price": "10.00", "fee": "0.01",
            "virtual_debit": "10.01", "checked_at": checked,
            "quote_at": quoted, "simulated_not_broker_fill": True,
            "policy": "spread_liquidity_execution_QA_not_directional_signal",
        })
    for symbol in symbols:
        events.append({
            "action": "SELL", "symbol": symbol, "quantity": 1,
            "virtual_price": "10.20", "fee": "0.01",
            "realized_pnl": "0.18", "reason": "SESSION_END",
            "checked_at": checked, "quote_at": quoted,
            "simulated_not_broker_fill": True,
        })
    return {
        "version": 1, "initial_cash": "150.00", "cash": "150.90",
        "entries": 5, "positions": {}, "events": events,
    }


def stock_record(**updates):
    row = {
        "state": "VIRTUAL_FORWARD_STEP", "broker_orders_sent": 0,
        "entries_total": 2, "positions_open": 1, "cash_virtual": "139.47",
        "realized_pnl_virtual": "0.48",
        "liquidation_equity_virtual_est": "150.11",
        "net_pnl_virtual_est": "0.11",
    }
    row.update(updates)
    return row


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
        stock_path = self.root / "forward_execution_qa.json"
        stock_path.write_text(json.dumps(stock_book()) + "\n")
        stock_log = self.root / "forward_qa_stdout.log"
        stock_log.write_text(json.dumps(stock_record()) + "\n")
        os.utime(stock_path, (T.timestamp(), T.timestamp()))
        os.utime(stock_log, (T.timestamp(), T.timestamp()))

    def test_current_virtual_report_keeps_accounts_independent(self):
        got = build_status(self.root, now=T)
        self.assertEqual(got["crypto_monitor"]["monitor_health"],
                         "HEALTHY_RECENT_CHECK")
        self.assertEqual(got["crypto_virtual_account"]["virtual_buys"], 3)
        self.assertEqual(got["crypto_virtual_account"]["virtual_sells"], 0)
        self.assertEqual(got["crypto_virtual_account"]["current_settled_virtual_cash"],
                         "141.00")
        stock = got["stock_virtual_qa"]
        self.assertEqual(stock["monitor_health"],
                         "HEALTHY_RECONCILED_RECENT_CHECK")
        self.assertEqual(stock["entries_lifetime"], 2)
        self.assertEqual(stock["virtual_sells"], 1)
        self.assertEqual(stock["realized_virtual_pnl"], "0.48")
        self.assertEqual(stock["current_virtual_cash"], "139.47")
        self.assertEqual([x["symbol"] for x in stock["open_positions"]], ["F"])
        self.assertFalse(stock["entry_cap_reached"])
        self.assertFalse(stock["merged_crypto_profits"])
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

    def test_truncated_and_missing_stock_log_fail_closed(self):
        bad = self.root / "bad.log"
        bad.write_text("garbage}\n")
        with self.assertRaises(ValueError):
            parse_stock_qa_log(bad)
        with self.assertRaises(ValueError):
            parse_stock_qa_log(self.root / "other.log")

    def test_completed_stock_pilot_reconciles_session_end_terminal(self):
        stock_path = self.root / "forward_execution_qa.json"
        stock_path.write_text(json.dumps(completed_stock_book()) + "\n")
        stock_log = self.root / "forward_qa_stdout.log"
        stock_log.write_text(json.dumps(stock_record(
            state="TRIAL_COMPLETE", entries_total=5,
            positions_open=None, cash_virtual=None,
            realized_pnl_virtual=None,
        )) + "\n")
        stale = (T - timedelta(hours=2)).timestamp()
        os.utime(stock_path, (stale, stale))
        os.utime(stock_log, (stale, stale))

        stock = build_status(self.root, now=T)["stock_virtual_qa"]
        self.assertEqual(stock["monitor_health"], "TRIAL_COMPLETE_RECONCILED")
        self.assertEqual(stock["entries_lifetime"], 5)
        self.assertEqual(stock["virtual_sells"], 5)
        self.assertEqual(stock["open_positions"], [])
        self.assertEqual(stock["current_virtual_cash"], "150.90")
        self.assertEqual(stock["realized_virtual_pnl"], "0.90")

    def test_terminal_log_mismatch_remains_fail_closed(self):
        stock_path = self.root / "forward_execution_qa.json"
        stock_path.write_text(json.dumps(completed_stock_book()) + "\n")
        stock_log = self.root / "forward_qa_stdout.log"
        stock_log.write_text(json.dumps(stock_record(
            state="TRIAL_COMPLETE", entries_total=4,
        )) + "\n")
        os.utime(stock_path, (T.timestamp(), T.timestamp()))
        os.utime(stock_log, (T.timestamp(), T.timestamp()))

        stock = build_status(self.root, now=T)["stock_virtual_qa"]
        self.assertEqual(
            stock["monitor_health"],
            "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE",
        )

    def test_stock_log_and_journal_mismatch_warns(self):
        log = self.root / "forward_qa_stdout.log"
        log.write_text(json.dumps(stock_record(positions_open=2)) + "\n")
        os.utime(log, (T.timestamp(), T.timestamp()))
        got = build_status(self.root, now=T)
        self.assertEqual(
            got["stock_virtual_qa"]["monitor_health"],
            "LOG_AND_LEDGER_COUNTS_OR_PNL_DIVERGE",
        )

    def test_stock_journal_tamper_fails_report(self):
        path = self.root / "forward_execution_qa.json"
        book = stock_book()
        book["cash"] = "150.00"
        path.write_text(json.dumps(book))
        with self.assertRaises(ValueError):
            get_stock_virtual_snapshot(path)

    def test_unknown_stock_exit_reason_remains_denied(self):
        path = self.root / "forward_execution_qa.json"
        book = stock_book()
        book["events"][-1]["reason"] = "EOD"
        path.write_text(json.dumps(book))
        with self.assertRaisesRegex(ValueError, "unsupported"):
            get_stock_virtual_snapshot(path)

    def test_stock_log_refuses_claimed_broker_order(self):
        path = self.root / "forward_qa_stdout.log"
        path.write_text(json.dumps(stock_record(broker_orders_sent=1)) + "\n")
        with self.assertRaises(ValueError):
            parse_stock_qa_log(path)

    def test_stock_journal_symlink_is_denied(self):
        target = self.root / "forward_execution_qa.json"
        link = self.root / "stock-link.json"
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            get_stock_virtual_snapshot(link)

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
