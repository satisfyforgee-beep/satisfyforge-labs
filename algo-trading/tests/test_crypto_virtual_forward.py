"""Offline unit tests: virtual Kraken fills are not brokerage executions."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from zerocost_bot.crypto_virtual_forward import (
    VirtualCryptoTrial, SYMBOLS, _MODE,
)
from zerocost_bot.market_coverage import AssetClass, MarketQuote
from zerocost_bot.paper_capital import CapitalBlocked

T = datetime(2026, 10, 26, 22, 0, tzinfo=timezone.utc)


def books(when, *, btc=80000, eth=2300, sol=100, stale=0):
    prices = {"BTC/USD": btc, "ETH/USD": eth, "SOL/USD": sol}
    out = {}
    for symbol, price in prices.items():
        ref = when - timedelta(seconds=stale)
        out[symbol] = MarketQuote(
            "kraken_public", AssetClass.CRYPTO, symbol,
            float(price) * 0.99999, float(price),
            ref, ref, ref, entitlement_verified=True)
    return out


class VirtualTrialTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = str(Path(folder.name) / "private" / "virtual.sqlite3")
        self.trial = VirtualCryptoTrial(self.path)

    def test_three_immediate_virtual_buys_use_real_quotes_but_no_broker(self):
        result = self.trial.start_three(books(T), T)
        self.assertEqual(result["state"], "THREE_VIRTUAL_ENTRIES_RECORDED")
        self.assertEqual(result["virtual_buys_this_call"], 3)
        self.assertEqual(result["broker_orders_sent"], 0)
        self.assertEqual(result["account"]["realized_virtual_pnl"], "0.00")
        self.assertEqual(result["account"]["virtual_entry_event_count"], 3)
        self.assertEqual({x["symbol"] for x in result["virtual_buys"]}, set(SYMBOLS))
        self.assertEqual(len(result["account"]["virtual_positions"]), 3)
        spent = Decimal("150") - Decimal(result["account"]["settled_virtual_cash"])
        posted = sum((Decimal(p["virtual_debit_including_fee"])
                      for p in result["virtual_buys"]), Decimal(0))
        self.assertEqual(spent, posted)
        self.assertGreater(spent, Decimal("40"))
        self.assertLessEqual(spent, Decimal("45"))
        for x in result["virtual_buys"]:
            self.assertLessEqual(Decimal(x["virtual_debit_including_fee"]), 15)

    def test_restarted_run_does_not_submit_duplicate_virtual_entry(self):
        self.trial.start_three(books(T), T)
        again = VirtualCryptoTrial(self.path)
        out = again.start_three(books(T + timedelta(minutes=1)),
                                T + timedelta(minutes=1))
        self.assertEqual(out["virtual_buys_this_call"], 0)
        self.assertEqual(out["account"]["virtual_entry_event_count"], 3)

    def test_stop_and_target_use_future_observed_quotes_only(self):
        self.trial.start_three(books(T), T)
        later = T + timedelta(hours=1)
        outcome = self.trial.evaluate_exits(
            books(later, btc=76000, eth=2400, sol=100), later)
        self.assertEqual(outcome["virtual_exits_this_call"], 2)
        self.assertEqual({x["symbol"] for x in outcome["exits"]},
                         {"BTC/USD", "ETH/USD"})
        self.assertEqual({x["reason"] for x in outcome["exits"]},
                         {"STOP_OBSERVED", "TARGET_OBSERVED"})
        self.assertEqual(outcome["account"]["virtual_exit_event_count"], 2)
        prior = outcome["account"]["realized_virtual_pnl"]
        again = self.trial.evaluate_exits(
            books(later, btc=76000, eth=2400, sol=100), later)
        self.assertEqual(again["virtual_exits_this_call"], 0)
        self.assertEqual(again["account"]["realized_virtual_pnl"], prior)
        self.assertTrue(all(x["model_not_exchange_fill"] for x in outcome["exits"]))

    def test_time_exit_after_24_hours_and_realized_losses(self):
        self.trial.start_three(books(T), T)
        t2 = T + timedelta(hours=25)
        report = self.trial.evaluate_exits(books(t2), t2)
        self.assertEqual(report["virtual_exits_this_call"], 3)
        self.assertTrue(all(x["reason"] == "MAX_24H_HOLD" for x in report["exits"]))
        self.assertLess(Decimal(report["account"]["realized_virtual_pnl"]), 0)
        self.assertEqual(report["account"]["virtual_positions"], [])
        self.assertEqual(report["account"]["virtual_exit_event_count"], 3)

    def test_stale_book_denied_before_writing_any_entry(self):
        with self.assertRaises(CapitalBlocked):
            self.trial.start_three(books(T, stale=30), T)
        self.assertEqual(self.trial.ledger.snapshot()["positions"], [])
        self.assertEqual(self.trial.ledger.snapshot()["settled_cash"], "150.00")

    def test_incomplete_book_denied_without_partial_open(self):
        bad = books(T)
        del bad["SOL/USD"]
        with self.assertRaises(CapitalBlocked):
            self.trial.start_three(bad, T)
        self.assertEqual(self.trial.ledger.snapshot()["positions"], [])

    def test_unfinished_reservation_fail_closed(self):
        self.trial.ledger.reserve_buy("abandoned", "crypto",
                                      "BTC/USD", ".0001",
                                      "80000", 0, when=T)
        with self.assertRaises(CapitalBlocked):
            self.trial.start_three(books(T), T)

    def test_no_actions_when_flat_and_unstarted(self):
        report = self.trial.evaluate_exits(books(T), T)
        self.assertEqual(report["virtual_exits_this_call"], 0)
        self.assertEqual(report["account"]["opening_virtual_cash"], "150.00")


if __name__ == "__main__":
    unittest.main()
