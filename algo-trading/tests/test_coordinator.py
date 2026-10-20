import os
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import patch

from test_agents_and_risk import NOW, snapshot, quote
from zerocost_bot.agents import ConsensusEngine
from zerocost_bot.coordinator import PaperCoordinator, PreparedPaper
from zerocost_bot.journal import OrderJournal
from zerocost_bot.paper_broker import PaperBroker


class FakePaperBroker(PaperBroker):
    def __init__(self):
        super().__init__("paper_key_for_mock","paper_secret_for_mock",
                         transport=lambda *args:None)
        self.sent=[]
        self.fail=False
        self.active_orders=[]
    def snapshot(self):
        return {
            "account":{"status":"ACTIVE","cash":"40","equity":"40",
                       "buying_power":"40","last_equity":"40",
                       "trading_blocked":False},
            "clock":{"is_open":True},
            "positions":[], "open_orders":self.active_orders, "today_orders":[]
        }
    def validate(self,*args,**kwargs):
        return 1
    def paper_submit(self,payload,explicitly_armed=False):
        if not explicitly_armed:
            raise RuntimeError("never send unarmed")
        self.sent.append(payload)
        if self.fail:
            raise OSError("simulated ambiguous transport failure")
        return {"status":"submitted_to_paper_broker",
                "order":{"id":"paper-order-001"}}


class PaperCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.broker=FakePaperBroker()
        self.journal=OrderJournal(os.path.join(self.temp.name,"orders.sqlite3"))
        self.c=PaperCoordinator(self.broker,self.journal)
        self.decision=ConsensusEngine().assess(snapshot())
        self.bar=NOW-timedelta(minutes=1,seconds=30)
    def prep(self):
        return self.c.prepare(self.decision,quote(),self.bar,NOW)
    def test_dry_run_does_not_call_submit_or_write_journal(self):
        obj=self.prep()
        self.assertIsInstance(obj,PreparedPaper)
        self.assertEqual(obj.payload["order_class"],"bracket")
        self.assertEqual(obj.payload["side"],"buy")
        self.assertEqual(len(self.broker.sent),0)
        self.assertIsNone(self.journal.status(obj.reservation_id))
    def test_both_arming_gates_required(self):
        proposal=self.prep()
        with patch.dict(os.environ,{"SF_PAPER_ORDER_ENABLE":""}):
            with self.assertRaises(RuntimeError):
                self.c.submit(proposal,explicitly_armed=True,now=NOW)
        with patch.dict(os.environ,{"SF_PAPER_ORDER_ENABLE":"PAPER_ONLY_APPROVED"}):
            with self.assertRaises(RuntimeError):
                self.c.submit(proposal,explicitly_armed=False,now=NOW)
        self.assertEqual(self.broker.sent,[])
        self.assertIsNone(self.journal.status(proposal.reservation_id))
    def test_one_paper_order_only_even_after_restart(self):
        p=self.prep()
        with patch.dict(os.environ,{"SF_PAPER_ORDER_ENABLE":"PAPER_ONLY_APPROVED"}):
            result=self.c.submit(p,explicitly_armed=True,now=NOW)
            self.assertEqual(result["status"],"submitted_to_paper_broker")
            c2=PaperCoordinator(self.broker,OrderJournal(self.journal.path))
            d=c2.submit(p,explicitly_armed=True,now=NOW)
        self.assertEqual(d["status"],"duplicate_blocked")
        self.assertEqual(len(self.broker.sent),1)
    def test_unknown_result_never_resubmits(self):
        p=self.prep()
        self.broker.fail=True
        with patch.dict(os.environ,{"SF_PAPER_ORDER_ENABLE":"PAPER_ONLY_APPROVED"}):
            first=self.c.submit(p,explicitly_armed=True,now=NOW)
            again=self.c.submit(p,explicitly_armed=True,now=NOW)
        self.assertEqual(first["status"],"unknown_needs_reconciliation")
        self.assertEqual(again["status"],"duplicate_blocked")
        self.assertEqual(len(self.broker.sent),1)
        self.assertEqual(self.journal.status(p.reservation_id)["state"],"unknown")
    def test_new_open_order_blocks_paper_execution(self):
        p=self.prep()
        self.broker.active_orders.append({"id":"other-trade"})
        with patch.dict(os.environ,{"SF_PAPER_ORDER_ENABLE":"PAPER_ONLY_APPROVED"}):
            result=self.c.submit(p,explicitly_armed=True,now=NOW)
        self.assertEqual(result["status"],"skip")
        self.assertEqual(self.broker.sent,[])
    def test_invalid_broker_snapshot_no_proposal(self):
        self.broker.snapshot=lambda:{"account":{},"clock":{}}
        with self.assertRaises(ValueError):
            self.prep()
    def test_cannot_supply_live_broker_adapter(self):
        with self.assertRaises(TypeError):
            PaperCoordinator(object(),self.journal)


if __name__=="__main__":
    unittest.main()
