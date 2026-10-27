import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from zerocost_bot.engine import Bar, Settings
from zerocost_bot.evaluation import evaluate_holdout


BASE = datetime(2026, 10, 19, 13, 30, tzinfo=timezone.utc)


def sample(n=100):
    return [Bar("DEMO", BASE + timedelta(minutes=i), 10 + i / 100,
                10.01 + i / 100, 9.99 + i / 100, 10 + i / 100, 5000)
            for i in range(n)]


class HistoricalHoldoutTests(unittest.TestCase):
    def test_deterministic_untuned_split_and_metrics(self):
        a = evaluate_holdout(sample())
        b = evaluate_holdout(sample())
        self.assertEqual(a, b)
        self.assertEqual(a["mode"], "OFFLINE_HISTORICAL_HOLDOUT")
        self.assertEqual(a["train"]["bars"], 70)
        self.assertEqual(a["holdout"]["bars"], 30)
        self.assertEqual(a["holdout"]["strategy"]["start_cash"], 1000)
        self.assertIn("max_mark_to_market_drawdown_pct", a["holdout"])
        self.assertTrue(a["paper_only"])

    def test_bad_and_insufficient_data_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate_holdout(sample(20))
        with self.assertRaises(ValueError):
            evaluate_holdout(sample(), train_fraction=.91)
        rows = sample()
        rows[-1] = replace(rows[-1], time=rows[-2].time)
        with self.assertRaisesRegex(ValueError, "nonduplicated"):
            evaluate_holdout(rows)
        rows = sample()
        rows[5] = replace(rows[5], symbol="OTHER")
        with self.assertRaisesRegex(ValueError, "single instrument"):
            evaluate_holdout(rows)
        rows = sample()
        rows[5] = replace(rows[5], close=float("nan"))
        with self.assertRaises(ValueError):
            evaluate_holdout(rows)

    def test_fixed_settings_are_not_modified(self):
        settings = Settings(start_cash=500, fee_per_order=1.25)
        original = settings.__dict__.copy()
        evaluate_holdout(sample(), settings)
        self.assertEqual(settings.__dict__, original)


if __name__ == "__main__":
    unittest.main()
