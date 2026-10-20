import unittest
from datetime import datetime, timedelta, timezone
from zerocost_bot.streaming import parse_market_message, LiveResearch, timestamp

NOW = datetime(2026, 10, 20, 14, 0, 30, tzinfo=timezone.utc)
START = NOW - timedelta(minutes=20, seconds=30)

def bar(ticker, i, last=False):
    price = 10.12 if last else 10.0
    return dict(T="b", S=ticker, o=price, h=price+.01, l=price-.01,
                c=price, v=15000 if last else 1000,
                t=(START+timedelta(minutes=i)).isoformat())


class StreamTests(unittest.TestCase):
    def test_bar_parser(self):
        kind, b=parse_market_message(bar("SOFI", 0))
        self.assertEqual(kind, "bar")
        self.assertEqual(b.symbol, "SOFI")
    def test_quote_parser(self):
        kind, (s,b,a,t)=parse_market_message(
            dict(T="q",S="SOFI",bp=10.12,ap=10.13,t=NOW.isoformat()))
        self.assertEqual((kind,s,b,a),("quote","SOFI",10.12,10.13))
        self.assertEqual(t,NOW)
    def test_bad_feed_values_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_market_message(dict(T="q",S="SOFI",bp=10.5,ap=10.1,t=NOW.isoformat()))
        with self.assertRaises(ValueError):
            timestamp("2026-10-20T14:00:00")
        self.assertIsNone(parse_market_message(dict(T="success",msg="authenticated")))
    def test_needs_benchmark_and_history(self):
        runner=LiveResearch(symbols=["SOFI","SPY"])
        for i in range(20):
            runner.ingest(bar("SOFI",i,last=(i==19)),NOW)
        q=dict(T="q",S="SOFI",bp=10.12,ap=10.13,t=(NOW-timedelta(seconds=1)).isoformat())
        self.assertIsNone(runner.ingest(q,NOW))
    def test_single_decision_per_completed_minute(self):
        runner=LiveResearch(symbols=["SOFI","SPY"])
        for i in range(6):
            runner.ingest(bar("SPY",i+14),NOW)
        for i in range(20):
            runner.ingest(bar("SOFI",i,last=(i==19)),NOW)
        q=dict(T="q",S="SOFI",bp=10.12,ap=10.13,t=(NOW-timedelta(seconds=1)).isoformat())
        report=runner.ingest(q,NOW)
        self.assertIsNotNone(report)
        self.assertEqual(report["action"],"candidate")
        self.assertEqual(report["symbol"],"SOFI")
        self.assertEqual(report["market_data"]["coverage"], "single_venue")
        self.assertFalse(report["market_data"]["live_order_authorized"])
        self.assertIsNone(runner.ingest(q,NOW))
        self.assertIsNone(runner.ingest(bar("SOFI",19,last=True),NOW))
    def test_max_free_symbols(self):
        with self.assertRaises(ValueError):
            LiveResearch(symbols=["SOFI","AAL"])
        with self.assertRaises(ValueError):
            LiveResearch(symbols=["SPY"]+[f"SYM{i}" for i in range(30)])
    def test_quote_before_bar_close_does_not_poison(self):
        runner=LiveResearch(symbols=["SOFI","SPY"])
        for i in range(6):runner.ingest(bar("SPY",i+14),NOW)
        for i in range(20):runner.ingest(bar("SOFI",i,last=(i==19)),NOW)
        early=NOW-timedelta(seconds=40)
        # At this point the final bar has not closed.
        q=dict(T="q",S="SOFI",bp=10.12,ap=10.13,t=early.isoformat())
        self.assertIsNone(runner.ingest(q,early))
        q["t"]=(NOW-timedelta(seconds=1)).isoformat()
        self.assertEqual(runner.ingest(q,NOW)["action"],"candidate")


if __name__=="__main__":
    unittest.main()
