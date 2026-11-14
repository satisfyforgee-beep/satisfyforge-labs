import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from pathlib import Path

from fill_stress import AdverseFillAssumptions, stress_cash_buy
from paper_engine import Instrument, PaperEngine, PaperOrder, Quote, RiskPolicy


NOW = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
STOCK = Instrument("EXAMPLE", "equity")
OPTION = Instrument("EXAMPLE261120C00010000", "option", D("100"))


class AdverseFillStressTests(unittest.TestCase):
    def assumptions(self, **updates):
        values = {
            "latency_ms": 800,
            "slippage_bps": D("10"),
            "displayed_size_fraction": D("0.5"),
            "fixed_fee": D("0.01"),
            "fee_per_unit": D("0.005"),
            "max_quote_age_seconds": 15,
        }
        values.update(updates)
        return AdverseFillAssumptions(**values)

    def order(self, instrument=STOCK, quantity="4", limit="10.05"):
        return PaperOrder("stress-1", instrument, "buy", D(quantity), D(limit))

    def quote(self, instrument=STOCK, bid="9.98", ask="10", age_seconds=1,
              delayed=False):
        return Quote(instrument, D(bid), D(ask),
                     NOW - timedelta(seconds=age_seconds),
                     "UNIT_TEST_SYNTHETIC_BOOK", delayed)

    def test_partial_fill_is_capped_by_haircut_displayed_size(self):
        result = stress_cash_buy(
            order=self.order(), quote=self.quote(), displayed_ask_size=D("4"),
            cash_before=D("100"), decision_at=NOW,
            assumptions=self.assumptions())
        self.assertEqual(result["status"], "PARTIAL_FILL")
        self.assertEqual(D(result["filled_quantity"]), D("2"))
        self.assertEqual(D(result["fill_price"]), D("10.010"))
        self.assertEqual(D(result["fee"]), D("0.020"))
        self.assertEqual(D(result["cash_after"]), D("79.960"))
        self.assertFalse(result["execution_evidence"])

    def test_adverse_price_limit_and_latency_can_produce_no_fill(self):
        cases = [
            (self.quote(ask="10.05"), self.assumptions(), "adverse price"),
            (self.quote(age_seconds=15), self.assumptions(latency_ms=1), "expired"),
            (self.quote(delayed=True), self.assumptions(), "Delayed"),
        ]
        for idx, (quote, assumptions, reason) in enumerate(cases):
            with self.subTest(idx=idx):
                order = PaperOrder(f"stress-{idx}", STOCK, "buy", D("4"), D("10.05"))
                result = stress_cash_buy(
                    order=order, quote=quote, displayed_ask_size=D("4"),
                    cash_before=D("100"), decision_at=NOW,
                    assumptions=assumptions)
                self.assertEqual(result["status"], "NO_FILL")
                self.assertIn(reason.lower(), result["reason"].lower())
                self.assertEqual(D(result["cash_after"]), D("100"))

    def test_option_multiplier_fees_and_cash_never_go_negative(self):
        order = self.order(OPTION, quantity="1", limit="0.26")
        result = stress_cash_buy(
            order=order, quote=self.quote(OPTION, bid="0.24", ask="0.25"),
            displayed_ask_size=D("5"), cash_before=D("20"),
            decision_at=NOW, assumptions=self.assumptions())
        self.assertEqual(result["status"], "NO_FILL")
        self.assertIn("cash-only", result["reason"].lower())
        self.assertEqual(D(result["cash_after"]), D("20"))

    def test_pure_fixture_does_not_mutate_existing_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = PaperEngine(Path(tmp) / "paper.sqlite3", D("100"),
                                 RiskPolicy(D("70"), D("100"), D("100")))
            before = (engine.snapshot(), engine.orders())
            first = stress_cash_buy(
                order=self.order(), quote=self.quote(), displayed_ask_size=D("4"),
                cash_before=D("100"), decision_at=NOW,
                assumptions=self.assumptions())
            second = stress_cash_buy(
                order=self.order(), quote=self.quote(), displayed_ask_size=D("4"),
                cash_before=D("100"), decision_at=NOW,
                assumptions=self.assumptions())
            self.assertEqual(first, second)
            self.assertEqual((engine.snapshot(), engine.orders()), before)

    def test_invalid_or_optimistic_assumptions_fail_closed(self):
        with self.assertRaises(ValueError):
            self.assumptions(displayed_size_fraction=D("1.01"))
        with self.assertRaises(ValueError):
            self.assumptions(slippage_bps=-D("1"))
        with self.assertRaises(ValueError):
            self.assumptions(fixed_fee=0.01)


if __name__ == "__main__":
    unittest.main()
