import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from zerocost_bot.engine import Bar
from zerocost_bot.agents import Snapshot, ConsensusEngine, Decision
from zerocost_bot.risk_gate import RiskGate, RiskPolicy, BrokerState, Quote
from zerocost_bot.journal import OrderJournal, order_key

UTC = timezone.utc
NOW = datetime(2026, 10, 20, 14, 0, 30, tzinfo=UTC)


def make_bars():
    start = NOW - timedelta(minutes=20, seconds=30)
    rows = []
    for i in range(20):
        price = 10.0 if i < 19 else 10.12
        rows.append(Bar("TEST", start + timedelta(minutes=i),
                        price, price + .01, price - .01, price,
                        1000 if i < 19 else 15000))
    return rows


def snapshot(**kw):
    params = dict(symbol="TEST", bars=make_bars(), bid=10.12, ask=10.13,
                  quote_at=NOW-timedelta(seconds=1), evaluated_at=NOW)
    params.update(kw)
    return Snapshot(**params)


def state(**kw):
    params = dict(cash=Decimal("40"),equity=Decimal("40"),
                  day_start_equity=Decimal("40"),buying_power=Decimal("40"),
                  positions=0,pending_orders=0,entries_today=0,
                  market_open=True,trading_blocked=False)
    params.update(kw)
    return BrokerState(**params)


def quote(**kw):
    params = dict(bid=Decimal("10.12"), ask=Decimal("10.13"),
                  time=NOW-timedelta(seconds=1))
    params.update(kw)
    return Quote(**params)


class ConsensusTests(unittest.TestCase):
    def test_good_signal_requires_four_confirmations(self):
        d=ConsensusEngine().assess(snapshot())
        self.assertEqual(d.action,"candidate")
        self.assertGreaterEqual(d.support_count,4)
        self.assertEqual(d.entry_reference,10.13)
        self.assertNotIn("probability",str(d.as_report()).lower().replace("not a probability",""))
    def test_stale_quote_veto(self):
        d=ConsensusEngine().assess(snapshot(quote_at=NOW-timedelta(minutes=1)))
        self.assertEqual(d.action,"pass")
        self.assertEqual(d.votes[-1].verdict,"veto")
    def test_no_partially_formed_bar(self):
        d=ConsensusEngine().assess(snapshot(evaluated_at=NOW-timedelta(seconds=45)))
        self.assertEqual(d.action,"pass")
    def test_duplicate_bar(self):
        bars=make_bars()
        bars[-1]=Bar("TEST",bars[-2].time,10.12,10.13,10.11,10.12,15000)
        self.assertEqual(ConsensusEngine().assess(snapshot(bars=bars)).action,"pass")
    def test_wide_spread_veto(self):
        self.assertEqual(ConsensusEngine().assess(snapshot(ask=10.40)).action,"pass")
    def test_flat_data_no_hype(self):
        bars=make_bars()
        last=bars[-1]
        bars[-1]=Bar("TEST",last.time,10,10.01,9.99,10,15000)
        self.assertEqual(ConsensusEngine().assess(snapshot(bars=bars)).action,"pass")
    def test_bad_benchmark_veto(self):
        bm=[Bar("SPY",NOW-timedelta(minutes=7-i),100-i,100-i+.1,100-i-.1,100-i,1000) for i in range(6)]
        self.assertEqual(ConsensusEngine().assess(snapshot(benchmark=bm)).action,"pass")
    def test_future_quote_veto(self):
        self.assertEqual(ConsensusEngine().assess(snapshot(quote_at=NOW+timedelta(seconds=3))).action,"pass")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.candidate=ConsensusEngine().assess(snapshot())
        self.gate=RiskGate()
    def test_valid_preflight_no_broker_order(self):
        d=self.gate.check(self.candidate,state(),quote(),NOW)
        self.assertTrue(d.approved)
        self.assertEqual(d.qty,1)
        self.assertLessEqual(Decimal(d.notional),Decimal("20"))
        self.assertLessEqual(Decimal(d.planned_risk),Decimal("1"))
    def test_daily_loss_veto(self):
        d=self.gate.check(self.candidate,state(equity=Decimal("36.90")),quote(),NOW)
        self.assertFalse(d.approved)
        self.assertIn("loss",d.reason)
    def test_existing_order_veto(self):
        d=self.gate.check(self.candidate,state(pending_orders=1),quote(),NOW)
        self.assertFalse(d.approved)
        self.assertIn("pending",d.reason)
    def test_existing_position_veto(self):
        self.assertFalse(self.gate.check(self.candidate,state(positions=1),quote(),NOW).approved)
    def test_stale_quote_veto(self):
        self.assertFalse(self.gate.check(self.candidate,state(),quote(time=NOW-timedelta(seconds=30)),NOW).approved)
    def test_no_leverage(self):
        self.assertFalse(self.gate.check(self.candidate,state(cash=Decimal("5")),quote(),NOW).approved)
    def test_expensive_stock_not_forced(self):
        self.assertFalse(self.gate.check(self.candidate,state(),quote(bid=Decimal("25"),ask=Decimal("25.01")),NOW).approved)
    def test_approval_quorum_required(self):
        nope=Decision("TEST","pass",(),0,NOW.isoformat())
        self.assertFalse(self.gate.check(nope,state(),quote(),NOW).approved)
    def test_market_closed_veto(self):
        self.assertFalse(self.gate.check(self.candidate,state(market_open=False),quote(),NOW).approved)


class JournalTests(unittest.TestCase):
    def test_dedup_and_crash_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=os.path.join(tmp,"journal.sqlite3")
            first=OrderJournal(path)
            bar=NOW-timedelta(minutes=1)
            self.assertEqual(first.reserve("v02","TEST",bar)[0],True)
            # Simulate process restart / a network timeout.
            second=OrderJournal(path)
            reserved,key=second.reserve("v02","TEST",bar)
            self.assertFalse(reserved)
            self.assertEqual(second.status(key)["state"],"reserved")
            second.transition(key,"unknown")
            self.assertEqual(OrderJournal(path).reserve("v02","TEST",bar)[0],False)
            second.transition(key,"filled",broker_order_id="paper123")
            self.assertEqual(second.status(key)["broker_order_id"],"paper123")
            with self.assertRaises(ValueError):
                second.transition(key,"submitted")
    def test_key_stable_and_timezone_normalized(self):
        t=NOW
        self.assertEqual(order_key("v02","TEST",t),
                         order_key("v02","test",t.astimezone(timezone(timedelta(hours=-4)))))
    def test_bad_journal_path(self):
        with self.assertRaises(ValueError):
            OrderJournal(":memory:")


if __name__=="__main__":
    unittest.main()
