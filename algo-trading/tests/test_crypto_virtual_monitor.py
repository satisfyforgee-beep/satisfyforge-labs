"""Unit tests for the installed virtual-only crypto LaunchAgent tick.

No public market requests, brokerage tokens or actual private ledger writes.
"""
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock
import io
import json
import os
import stat
import unittest

import crypto_virtual_monitor_once as monitor


def good_report():
    return {
        "mode": monitor.EXPECTED_MODE, "state": "VIRTUAL_EXIT_CHECK_COMPLETE",
        "broker_orders_sent": 0, "virtual_exits_this_call": 0,
        "account": {
            "mode": monitor.EXPECTED_MODE,
            "broker_orders_sent": 0,
            "real_money_orders_sent": 0,
            "virtual_entry_event_count": 3,
            "virtual_exit_event_count": 0,
            "virtual_positions": [
                {"asset": "crypto", "symbol": s}
                for s in ("BTC/USD", "ETH/USD", "SOL/USD")
            ],
            "settled_virtual_cash": "105.09",
            "realized_virtual_pnl": "0.00",
            "estimated_total_liquidation_value": "149.50",
        },
    }


class VirtualOnlyMonitorTests(unittest.TestCase):
    def test_only_safe_check_is_invoked_for_live_virtual_ledger(self):
        with TemporaryDirectory() as td:
            book = Path(td) / "book.sqlite3"
            book.write_bytes(b"fake-ledger-mocked")
            trial = MagicMock()
            trial.ledger.snapshot.return_value = {
                "mode": "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE",
                "positions": [{"symbol": s}
                              for s in ("BTC/USD", "ETH/USD", "SOL/USD")],
            }
            trial._history.return_value = [
                ("buy:" + str(n), "buy") for n in range(3)
            ]
            def one_check(args):
                self.assertEqual(args, ["--check"])
                print(json.dumps(good_report()))
            with patch.object(monitor, "BOOK", book), \
                 patch.object(monitor, "VirtualCryptoTrial", return_value=trial), \
                 patch.object(monitor, "virtual_runner_main",
                              side_effect=one_check) as execute:
                report = monitor.run_once()
            self.assertEqual(report["state"], "CHECK_COMPLETE")
            self.assertEqual(report["open_virtual_positions"], 3)
            self.assertEqual(execute.call_count, 1)

    def test_completed_trial_skips_network_and_reentry(self):
        with TemporaryDirectory() as td:
            book = Path(td) / "book.sqlite3"
            book.write_bytes(b"fake-ledger-mocked")
            trial = MagicMock()
            trial.ledger.snapshot.return_value = {
                "mode": "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE",
                "positions": [], "settled_cash": "148.00",
                "realized_net_pnl": "-2.00",
            }
            trial._history.return_value = (
                [("buy:" + str(n), "buy") for n in range(3)] +
                [("sell:" + str(n), "sell") for n in range(3)]
            )
            with patch.object(monitor, "BOOK", book), \
                 patch.object(monitor, "VirtualCryptoTrial", return_value=trial), \
                 patch.object(monitor, "virtual_runner_main") as execute:
                report = monitor.run_once()
            self.assertEqual(report["state"], "TRIAL_COMPLETED_NO_NEW_QUOTES_OR_BUYS")
            execute.assert_not_called()

    def test_missing_book_or_unexpected_entry_count_refused(self):
        with TemporaryDirectory() as td:
            book = Path(td) / "no-book.sqlite3"
            with patch.object(monitor, "BOOK", book):
                with self.assertRaises(RuntimeError):
                    monitor.run_once()
                self.assertFalse(book.exists())
            book.write_bytes(b"fake-ledger-mocked")
            trial = MagicMock()
            trial.ledger.snapshot.return_value = {
                "mode": "OFFLINE_PAPER_REPLAY_NOT_BROKER_EVIDENCE",
                "positions": [],
            }
            trial._history.return_value = [("buy:one", "buy")]
            with patch.object(monitor, "BOOK", book), \
                 patch.object(monitor, "VirtualCryptoTrial", return_value=trial), \
                 patch.object(monitor, "virtual_runner_main") as execute:
                with self.assertRaises(ValueError):
                    monitor.run_once()
            execute.assert_not_called()

    def test_malformed_broker_evidence_cannot_pass(self):
        report = good_report()
        self.assertEqual(monitor._validate_report(report)["virtual_cash"], "105.09")
        report["broker_orders_sent"] = 1
        with self.assertRaises(ValueError):
            monitor._validate_report(report)
        report = good_report()
        report["account"]["virtual_exit_event_count"] = 2
        with self.assertRaises(ValueError):
            monitor._validate_report(report)

    def test_log_is_private_and_bounded(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            path = root / "status.jsonl"
            with patch.object(monitor, "DIR", root):
                monitor._record({"state": "TEST_ONLY"}, path=path)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertEqual(json.loads(path.read_text())["state"], "TEST_ONLY")
                # Pretend the log has filled: old messages are discarded.
                with path.open("ab") as f:
                    f.write(b" " * (monitor.MAX_LOG_BYTES + 1))
                monitor._record({"state": "ROTATED"}, path=path)
                self.assertEqual(len(path.read_text().splitlines()), 1)
                self.assertEqual(json.loads(path.read_text())["state"], "ROTATED")


if __name__ == "__main__":
    unittest.main()
