"""Review gate: short replay profitability cannot turn on broker orders."""
import unittest
from zerocost_bot.replay_lessons import review_crypto_trial


def sample_report():
    results = {}
    for method in ("control", "breakout", "reversal"):
        def stage(net, closes=10, wins=2, fees="1.00"):
            return {
                "strategy": method,
                "virtual_closes": closes,
                "wins": wins,
                "losses_or_flats": closes - wins,
                "net_pnl_after_estimated_costs": net,
                "estimated_fees": fees,
                "max_drawdown_pct": "1.00",
                "return_pct": net,
            }
        results[method] = {
            "development": stage("0.50"),
            "holdout": stage("-1.00"),
        }
    return {
        "mode": "HISTORICAL_OFFLINE_REPLAY_NO_BROKER_ORDERS",
        "source": "KRAKEN_PUBLIC_OHLC_15MIN_LAST_CANDLE_EXCLUDED",
        "paper_broker_orders_sent": 0, "live_money_orders_sent": 0,
        "results": results,
    }


class LessonsTests(unittest.TestCase):
    def test_negative_after_costs_stops_promotion(self):
        report = review_crypto_trial(sample_report())
        self.assertFalse(report["broker_paper_execution_authorized"])
        self.assertFalse(report["live_money_execution_authorized"])
        self.assertEqual(report["outcome"],
                         "NO_STRATEGY_READY_FOR_PAPER_BROKER_EXECUTION")
        for data in report["strategies"].values():
            self.assertEqual(data["research_grade"], "REJECT")
            self.assertIn("NONPOSITIVE_HOLDOUT_NET_PNL", data["why"])
            self.assertIn("INSUFFICIENT_HOLDOUT_SAMPLE_30_TRADES", data["why"])

    def test_positive_but_small_holdout_never_authorizes_order(self):
        r = sample_report()
        for strategy in r["results"].values():
            strategy["holdout"]["net_pnl_after_estimated_costs"] = "3.00"
        result = review_crypto_trial(r)
        self.assertFalse(result["broker_paper_execution_authorized"])
        self.assertTrue(all(x["research_grade"] == "REJECT"
                            for x in result["strategies"].values()))

    def test_larger_positive_only_needs_more_evidence(self):
        r = sample_report()
        for strategy in r["results"].values():
            strategy["holdout"].update(
                virtual_closes=35, wins=25, losses_or_flats=10,
                net_pnl_after_estimated_costs="5.00")
        result = review_crypto_trial(r)
        self.assertTrue(all(x["research_grade"] == "NEEDS_MORE_FORWARD_DATA"
                            for x in result["strategies"].values()))
        self.assertFalse(result["broker_paper_execution_authorized"])

    def test_bad_or_fabricated_source_halts(self):
        r = sample_report()
        r["mode"] = "LIVE_BROKER_BENEFIT"
        with self.assertRaises(ValueError):
            review_crypto_trial(r)
        r = sample_report()
        r["results"]["control"]["holdout"]["wins"] = 100
        with self.assertRaises(ValueError):
            review_crypto_trial(r)


if __name__ == "__main__":
    unittest.main()
