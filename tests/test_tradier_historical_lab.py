"""Deterministic tests: historical parsing, no-lookahead execution and fail-closed risk."""
import importlib.util
import math
from datetime import date, timedelta
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("tradier_historical_lab", SCRIPTS / "tradier_historical_lab.py")
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def bars(n=220, *, start=date(2025, 1, 2), level=12.0, drift=0.003):
    result = []
    for i in range(n):
        d = start + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        mid = level * (1 + drift * i) + 0.35 * math.sin(i / 4)
        o = mid * (1 + 0.006 * math.sin(i / 6))
        c = mid
        result.append(m.Bar(d, o, max(o,c) + 0.3, min(o,c) - 0.3, c, 1_000_000))
    return result


def enough(n=220):
    return bars(int(n * 7 / 5) + 15)[:n]


def response_from(data):
    return {"history": {"day": [
        {"date": x.day.isoformat(), "open": x.open, "high": x.high,
         "low": x.low, "close": x.close, "volume": x.volume} for x in data
    ]}}


class HistoryTests(unittest.TestCase):
    def test_daily_history_parsing(self):
        dataset = enough(190)
        parsed = m.parse_history(response_from(dataset), asof=dataset[-1].day)
        self.assertEqual(len(parsed), 190)
        self.assertEqual(parsed[0].day, dataset[0].day)

    def test_history_list_or_single_and_min_rows(self):
        dataset = enough(190)
        payload = response_from(dataset)
        payload["history"]["day"] = payload["history"]["day"][0]
        with self.assertRaises(ValueError):
            m.parse_history(payload, asof=dataset[-1].day)
        with self.assertRaises(ValueError):
            m.parse_history({}, asof=dataset[-1].day)

    def test_reject_unsorted_repeats_future_and_invalid_ohlc(self):
        data = enough(190)
        for changed in ("repeat", "future", "ohlc", "infinite", "negative_volume"):
            payload = response_from(data)
            row = payload["history"]["day"][-1]
            if changed == "repeat":
                row["date"] = payload["history"]["day"][-2]["date"]
            elif changed == "future":
                row["date"] = (data[-1].day + timedelta(days=1)).isoformat()
            elif changed == "ohlc":
                row["high"] = row["low"] - 0.1
            elif changed == "infinite":
                row["close"] = float("inf")
            else:
                row["volume"] = -1
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                m.parse_history(payload, asof=data[-1].day)

    def test_get_history_sandbox_only(self):
        data = enough(190)
        seen=[]
        def fake(path, token, params):
            seen.append((path, params))
            return response_from(data)
        got = m.sandbox_history("fake-key", "SOFI", data[0].day.isoformat(),
                                data[-1].day.isoformat(), getter=fake)
        self.assertEqual(len(got), 190)
        self.assertEqual(seen[0][0], "/markets/history")
        self.assertEqual(seen[0][1]["interval"], "daily")
        with self.assertRaises(ValueError):
            m.sandbox_history("fake", "SPY/../../orders", "2025-01-01", "2025-11-01", getter=fake)

    def test_prefix_invariance_prevents_future_data_leak(self):
        b = enough(250)
        split = 170
        mutated = b[:split] + [m.Bar(x.day, x.open * 0.5, x.high * 2,
                                      x.low * 0.5, x.close * 1.5, x.volume)
                                for x in b[split:]]
        for name in m.STRATEGIES:
            with self.subTest(name=name):
                self.assertEqual(m.signals_for(b, name)[:split],
                                 m.signals_for(mutated, name)[:split])

    def test_next_open_not_same_close(self):
        b = enough(90)
        state = [False] * len(b)
        state[60] = True
        state[61] = True
        result = m.simulate(b, state, 60, 62, budget=100,
                            cost_bps=0, fee=0, max_exposure=1)
        self.assertEqual(result["entries"], 1)
        self.assertEqual(result["exits"], 0)
        self.assertEqual(result["open_shares"], int(100 // b[61].open))
        no_prior = m.simulate(b, [False] * len(b), 60, 62, budget=100)
        self.assertEqual(no_prior["entries"], 0)

    def test_fee_slippage_and_no_borrow(self):
        b = enough(95)
        s = [True] * len(b)
        a = m.simulate(b, s, 60, 95, budget=30, fee=0, cost_bps=0)
        worse = m.simulate(b, s, 60, 95, budget=30, fee=0.35, cost_bps=60)
        self.assertLessEqual(worse["equity"], a["equity"] + 0.05)
        self.assertLessEqual(worse["open_shares"] * b[-1].close, 100)
        tiny = m.simulate(b, s, 60, 95, budget=5)
        self.assertEqual(tiny["entries"], 0)
        with self.assertRaises(ValueError):
            m.simulate(b, s, 60, 95, budget=-1)

    def test_holdout_is_always_separate(self):
        b = enough(240)
        r = m.analyze_symbol(b, budget=30)
        self.assertEqual(r["bars"], 240)
        self.assertLess(r["train_end"], r["holdout_start"])
        self.assertIn("buyhold_holdout", r)
        self.assertTrue(set(r["training"]) == set(m.STRATEGIES))
        self.assertTrue(r["selected"] is None or r["selected"] in m.STRATEGIES)
        if r["test"]:
            self.assertIn(r["test"]["gate"], (
                "INSUFFICIENT EVIDENCE", "FAIL", "RESEARCH ONLY - NOT VERIFIED EDGE"))

    def test_selection_not_changed_by_test_period_prices(self):
        b = enough(240)
        split = int(len(b) * .7)
        mutant = b[:split] + [m.Bar(x.day, x.open * 1.1, x.high * 3,
                                    x.low, x.close * 2.0, x.volume)
                              for x in b[split:]]
        original = m.analyze_symbol(b, budget=100)
        altered = m.analyze_symbol(mutant, budget=100)
        self.assertEqual(original["selected"], altered["selected"])
        self.assertEqual(original["training"], altered["training"])

    def test_refuses_small_history(self):
        with self.assertRaises(ValueError):
            m.analyze_symbol(enough(90))

    def test_null_and_nan_rejected(self):
        with self.assertRaises(ValueError):
            m.safe_number(None)
        with self.assertRaises(ValueError):
            m.safe_number(float("nan"))
        with self.assertRaises(ValueError):
            m.simulate(enough(95), [True] * 95, 60, 95, cost_bps=-1)

    def test_no_live_or_order_endpoints(self):
        source = (SCRIPTS / "tradier_historical_lab.py").read_text()
        self.assertNotIn("api.tradier.com", source)
        self.assertNotIn('"/orders"', source)
        self.assertNotIn("method=\"POST\"", source)
        self.assertIn('"/markets/history"', source)

    def test_zero_budget_does_not_select_investment(self):
        b = enough(230)
        r = m.analyze_symbol(b, budget=1)
        self.assertIsNone(r["selected"])
        self.assertIsNone(r["test"])


if __name__ == "__main__":
    unittest.main()
