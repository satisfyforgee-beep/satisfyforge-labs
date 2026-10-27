import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

from paper_engine import Instrument, PaperEngine, PaperOrder, Quote, RiskPolicy, amount


NOW = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)
STOCK = Instrument("EXAMPLE", "equity")
OPTION = Instrument("EXAMPLE261030C00020000", "option", D("100"))
CRYPTO = Instrument("DEMO/USD", "crypto")


class PaperEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "paper.sqlite3"
        self.policy = RiskPolicy(D("70"), D("100"), D("100"),
                                 max_spread_fraction=D("0.15"))
        self.engine = PaperEngine(self.path, D("100"), self.policy)

    def quote(self, inst=STOCK, bid="10", ask="10.02", asof=NOW, delayed=False):
        return Quote(inst, D(bid), D(ask), asof, "UNIT_TEST_SYNTHETIC", delayed)

    def order(self, client_id="order-1", inst=STOCK, side="buy", qty="1", limit="11"):
        return PaperOrder(client_id, inst, side, D(qty), D(limit))

    def test_stock_fill_uses_ask_not_last_and_is_cash_only(self):
        result = self.engine.submit(self.order(), self.quote(), NOW)
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(result["fill_price"], "10.02")
        self.assertEqual(D(self.engine.snapshot()["cash"]), D("89.98"))

    def test_replay_same_order_has_no_second_effect(self):
        first = self.engine.submit(self.order(), self.quote(), NOW)
        second_engine = PaperEngine(self.path, D("9999"), self.policy)
        second = second_engine.submit(self.order(), self.quote(), NOW)
        self.assertEqual(first, second)
        self.assertEqual(len(second_engine.orders()), 1)
        self.assertEqual(D(second_engine.snapshot()["cash"]), D("89.98"))

    def test_client_id_reuse_with_modified_order_is_rejected(self):
        self.engine.submit(self.order(), self.quote(), NOW)
        with self.assertRaisesRegex(ValueError, "Client ID reused"):
            self.engine.submit(self.order(qty="2"), self.quote(), NOW)

    def test_non_executable_limit_is_not_queued(self):
        result = self.engine.submit(self.order(limit="9"), self.quote(), NOW)
        self.assertEqual(result["status"], "NOT_FILLED")
        self.assertEqual(self.engine.snapshot()["positions"], [])

    def test_delayed_stale_and_future_quotes_are_rejected(self):
        quotes = [self.quote(delayed=True),
                  self.quote(asof=NOW - timedelta(seconds=16)),
                  self.quote(asof=NOW + timedelta(seconds=1))]
        for idx, quote in enumerate(quotes):
            result = self.engine.submit(self.order(client_id=f"quote-{idx}"), quote, NOW)
            self.assertEqual(result["status"], "REJECTED")

    def test_wide_spread_is_rejected(self):
        result = self.engine.submit(self.order(), self.quote(bid="8", ask="10"), NOW)
        self.assertIn("spread", result["reason"])

    def test_cash_and_order_risk_limits(self):
        self.assertIn("Per-order", self.engine.submit(
            self.order(qty="8", limit="11"), self.quote(), NOW)["reason"])
        tiny = PaperEngine(Path(self.tmp.name) / "tiny.sqlite3", D("5"), self.policy)
        self.assertIn("Cash-only", tiny.submit(self.order(), self.quote(), NOW)["reason"])

    def test_exposure_budget_counts_existing_positions(self):
        engine = PaperEngine(Path(self.tmp.name) / "exposure.sqlite3", D("300"), self.policy)
        engine.submit(self.order("one", qty="6"), self.quote(), NOW)
        result = engine.submit(self.order("two", qty="5"), self.quote(), NOW)
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("exposure", result["reason"])

    def test_option_premium_and_fees_use_contract_multiplier(self):
        order = self.order(inst=OPTION, limit="0.50")
        result = self.engine.submit(order, self.quote(OPTION, bid="0.48", ask="0.50"), NOW)
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(D(self.engine.snapshot()["cash"]), D("49.35"))
        sell = self.order("exit", OPTION, "sell", limit="0.40")
        closed = self.engine.submit(sell, self.quote(OPTION, bid="0.40", ask="0.42"), NOW)
        self.assertEqual(closed["status"], "FILLED")
        self.assertEqual(D(closed["realized_pnl"]), D("-11.30"))
        self.assertEqual(D(self.engine.snapshot()["cash"]), D("88.70"))
        summary = self.engine.performance()
        self.assertEqual(summary["closed_exits"], 1)
        self.assertEqual(D(summary["realized_pnl"]), D("-11.30"))
        self.assertEqual(summary["win_rate"], "0")

    def test_fractional_crypto_and_no_shorting(self):
        order = self.order(inst=CRYPTO, qty="0.05", limit="500")
        self.assertEqual(self.engine.submit(order, self.quote(CRYPTO, "499", "500"), NOW)["status"], "FILLED")
        sell_too_much = self.order("sell-too-much", CRYPTO, "sell", qty="0.06", limit="499")
        result = self.engine.submit(sell_too_much, self.quote(CRYPTO, "499", "500"), NOW)
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(D(self.engine.snapshot()["positions"][0]["quantity"]), D("0.05"))

    def test_loss_budget_blocks_new_risk_after_loss(self):
        strict = RiskPolicy(D("70"), D("100"), D("50"))
        engine = PaperEngine(Path(self.tmp.name) / "strict.sqlite3", D("100"), strict)
        engine.submit(self.order("in", qty="4"), self.quote(), NOW)
        engine.submit(self.order("out", side="sell", qty="4", limit="8"),
                      self.quote(bid="8", ask="8.02"), NOW)
        result = engine.submit(self.order("another", qty="5"), self.quote(), NOW)
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("daily risk", result["reason"])

    def test_invalid_prices_quantities_multiplier_and_timestamps(self):
        with self.assertRaises(ValueError):
            amount(float("nan"))
        with self.assertRaises(ValueError):
            amount("Infinity")
        with self.assertRaises(ValueError):
            Instrument("INVALID", "option", D("10"))
        with self.assertRaises(ValueError):
            self.order(qty="0.5")
        with self.assertRaises(ValueError):
            self.quote(asof=datetime(2026, 10, 27))


if __name__ == "__main__":
    unittest.main()
