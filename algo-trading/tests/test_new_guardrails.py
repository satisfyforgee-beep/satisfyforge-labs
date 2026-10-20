import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from test_agents_and_risk import NOW, snapshot, quote, state, make_bars
from zerocost_bot.agents import ConsensusEngine, Snapshot
from zerocost_bot.risk_gate import RiskGate
from zerocost_bot.engine import Bar

class ExtraSafetyTests(unittest.TestCase):
    def test_risk_rejects_expired_signal_even_if_quote_fresh(self):
        d=ConsensusEngine().assess(snapshot())
        expired=replace(d,observed_at=(NOW-timedelta(seconds=30)).isoformat())
        result=RiskGate().check(expired,state(),quote(),NOW)
        self.assertFalse(result.approved)
        self.assertIn("stale",result.reason)
    def test_alpha_signals_all_required(self):
        bars=make_bars()
        last=bars[-1]
        bars[-1]=Bar("TEST",last.time,10.0,10.01,9.99,10.0,15000)
        d=ConsensusEngine().assess(snapshot(bars=bars))
        self.assertEqual(d.action,"pass")
    def test_nan_market_price_rejected(self):
        bars=make_bars()
        last=bars[-1]
        bars[-1]=Bar("TEST",last.time,float("nan"),float("nan"),9.99,float("nan"),15000)
        d=ConsensusEngine().assess(snapshot(bars=bars))
        self.assertEqual(d.action,"pass")
    def test_stale_spy_veto(self):
        bar_time=NOW-timedelta(minutes=18)
        benchmark=[Bar("SPY",bar_time+timedelta(minutes=i),100,100.02,99.98,100,20000) for i in range(6)]
        d=ConsensusEngine().assess(snapshot(benchmark=benchmark))
        self.assertEqual(d.action,"pass")
        self.assertTrue(any(v.verdict=="veto" for v in d.votes))

if __name__=="__main__":
    unittest.main()
