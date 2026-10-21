import unittest
from evaluate_signals import evaluate

class SignalTests(unittest.TestCase):
    def test_cost_and_missing(self):
        s = [{"symbol":"ABC","signal_time":"2026-10-21T10:00:00-04:00","signal_price":"10"}]
        b = [{"symbol":"ABC","time":"2026-10-21T14:15:00Z","close":"11"}]
        result = evaluate(s,b)[0]
        self.assertEqual(result["15m_net_return_pct"], 9.8)
        self.assertIsNone(result["60m_net_return_pct"])

    def test_stale_bars_are_not_used(self):
        s = [{"symbol":"ABC","signal_time":"2026-10-21T14:00:00Z","signal_price":"10"}]
        b = [{"symbol":"ABC","time":"2026-10-21T14:21:00Z","close":"20"}]
        self.assertIsNone(evaluate(s,b)[0]["15m_net_return_pct"])

    def test_duplicates_rejected(self):
        s = [{"symbol":"ABC","signal_time":"2026-10-21T14:00:00Z","signal_price":"10"}]
        with self.assertRaises(ValueError):
            evaluate(s+s,[])

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([{"symbol":"ABC","signal_time":"2026-10-21T14:00:00","signal_price":"10"}],[])

if __name__ == "__main__":
    unittest.main()
