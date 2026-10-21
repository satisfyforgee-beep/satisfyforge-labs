"""Offline contract tests: no credentials, network or simulated broker POSTs."""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tradier_auto.runner import (Plan, Journal, TradierSandbox, Runner,
                                 Halt, ARM_TOKEN, SANDBOX_HOST)

NY=ZoneInfo("America/New_York")


def plan_data():
    # Keep tests independent of expiring sample option; use a future OCC date.
    future=(datetime.now(NY).date()+timedelta(days=30)).strftime("%y%m%d")
    return {"enabled":False,"underlying":"T","option_symbol":f"T{future}P00021500",
            "direction":"down","underlying_trigger":"21.80", "quantity":2,
            "entry_limit":"0.22", "profit_limit":"0.27", "stop_trigger":"0.17",
            "max_spread":"0.03", "max_cost":"60.00","min_underlying_volume":100000}


class FakeTransport:
    def __init__(self,plan,now):
        self.plan=plan
        self.now=now
        self.calls=[]
        self.orders=[]
        self.positions=[]
        self.total_cash=Decimal("100")
        self.option_bp=Decimal("100")
        self.close_pl=Decimal("0")
        self.last=Decimal("21.75")
        self.bid=Decimal("0.20")
        self.ask=Decimal("0.22")
        self.stale_seconds=900
        self.broker_preview_result={"order":{"status":"ok","result":True,"cost":44.08,"fees":0.08,"commission":0}}
        self.fail_submit=False
        self.submitted=False

    def __call__(self,method,path,params):
        self.calls.append((method,path,dict(params)))
        if path=="/user/profile":
            return {"profile":{"account":{"account_number":"DEMO01","status":"active","option_level":3}}}
        if path.endswith("/balances"):
            return {"balances":{"total_cash":str(self.total_cash),"option_buying_power":str(self.option_bp),
                                "close_pl":str(self.close_pl),"pending_orders_count":0}}
        if path.endswith("/positions"):
            return {"positions":{"position":copy.deepcopy(self.positions)} if self.positions else None}
        if method=="GET" and path.endswith("/orders"):
            return {"orders":{"order":copy.deepcopy(self.orders)} if self.orders else None}
        if method=="GET" and "/orders/" in path:
            matching=[o for o in self.orders if str(o.get("id"))==path.rsplit("/",1)[-1]]
            return {"order":copy.deepcopy(matching[0])} if matching else {"order":None}
        if path=="/markets/quotes":
            stamp=int((self.now.timestamp()-self.stale_seconds)*1000)
            return {"quotes":{"quote":[
                {"symbol":"T","type":"stock","last":str(self.last),"volume":1000000,
                 "bid_date":stamp,"ask_date":stamp},
                {"symbol":self.plan.option_symbol,"type":"option","bid":str(self.bid),
                 "ask":str(self.ask),"bid_date":stamp,"ask_date":stamp}
                ]}}
        if method=="POST" and path.endswith("/orders"):
            if params.get("preview")=="true":
                return self.broker_preview_result
            if self.fail_submit:
                raise TimeoutError("connection dropped after write")
            self.submitted=True
            order={"id":1234,"status":"ok","tag":params["tag"]}
            self.orders.append(order)
            return {"order":order}
        raise AssertionError("unexpected fake route")


class BotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now=datetime.now(NY).replace(hour=11,minute=45,second=0,microsecond=0).astimezone(timezone.utc)
        # If run on weekend, use the known Wednesday session instead.
        if self.now.astimezone(NY).weekday()>=5:
            self.now=datetime(2026,10,21,11,45,tzinfo=NY).astimezone(timezone.utc)
        self.plan=Plan.from_dict(plan_data())
        self.fake=FakeTransport(self.plan,self.now)
        self.api=TradierSandbox("TEST_SANDBOX_TOKEN","DEMO01",transport=self.fake)
        self.journal=Journal(Path(self.temp.name)/"journal.db")

    def bot(self,armed=False,enabled=False):
        data=plan_data();data["enabled"]=enabled
        plan=Plan.from_dict(data)
        self.fake.plan=plan
        return Runner(self.api,self.journal,plan,paper_submit=armed,clock=lambda:self.now)

    def test_quote_signal_dry_run_never_posts(self):
        result=self.bot().run_once()
        self.assertEqual(result["action"],"paper_proposal_only")
        self.assertEqual(result["estimated_premium"],"44.00")
        self.assertFalse(any(m=="POST" for m,_,_ in self.fake.calls))

    def test_price_not_triggered(self):
        self.fake.last=Decimal("21.90")
        self.assertEqual(self.bot().run_once()["action"],"watch")

    def test_spread_rejection(self):
        self.fake.bid=Decimal("0.15")
        result=self.bot().run_once()
        self.assertEqual(result["action"],"blocked")

    def test_stale_quote_fails_closed(self):
        self.fake.stale_seconds=1300
        with self.assertRaisesRegex(Halt,"quote too old"):
            self.bot().run_once()

    def test_prevent_order_when_unarmed_even_with_switch(self):
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            self.assertEqual(self.bot(armed=True,enabled=False).run_once()["action"],"paper_proposal_only")
        self.assertFalse(any(m=="POST" for m,_,_ in self.fake.calls))

    def test_armed_preview_then_post_once(self):
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            result=self.bot(armed=True,enabled=True).run_once()
            again=self.bot(armed=True,enabled=True).run_once()
        self.assertEqual(result["action"],"submitted_to_sandbox")
        self.assertEqual(result["order_id"],"1234")
        self.assertFalse(result["filled"])
        self.assertEqual(again["action"],"broker_order_status")
        self.assertIn("ok",again["statuses"])
        post=[p for m,_,p in self.fake.calls if m=="POST"]
        self.assertEqual(len(post),2)
        self.assertEqual([x["preview"] for x in post],["true","false"])
        self.assertEqual({k:v for k,v in post[0].items() if k!="preview"},
                         {k:v for k,v in post[1].items() if k!="preview"})
        self.assertEqual(post[1]["class"],"otoco")
        self.assertEqual(post[1]["side[0]"],"buy_to_open")
        self.assertEqual(post[1]["side[1]"],"sell_to_close")
        self.assertEqual(post[1]["side[2]"],"sell_to_close")
        self.assertEqual(post[1]["stop[2]"],"0.17")
        self.assertEqual(post[1]["price[1]"],"0.27")

    def test_no_retry_after_ambiguous_broker_timeout(self):
        self.fake.fail_submit=True
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            with self.assertRaisesRegex(Halt,"uncertain"):
                self.bot(armed=True,enabled=True).run_once()
            self.assertEqual(self.bot(armed=True,enabled=True).run_once()["action"],"needs_manual_reconciliation")
        post=[x for x in self.fake.calls if x[0]=="POST" and x[2].get("preview")=="false"]
        self.assertEqual(len(post),1)

    def test_uncertain_recovers_broker_id_by_tag_without_post(self):
        self.fake.fail_submit=True
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            with self.assertRaisesRegex(Halt,"uncertain"):
                self.bot(armed=True,enabled=True).run_once()
            tag=self.plan.key(self.now.astimezone(NY).date())
            self.fake.orders=[{"tag":tag,"status":"filled","id":9876}]
            result=self.bot(armed=True,enabled=True).run_once()
        self.assertEqual(result["order_id"],"9876")
        self.assertEqual(result["statuses"],["filled"])
        self.assertEqual(len([x for x in self.fake.calls if x[0]=="POST" and x[2].get("preview")=="false"]),1)

    def test_reconcile_only_reports_broker_status(self):
        tag=self.plan.key(self.now.astimezone(NY).date())
        self.journal.reserve(tag,self.now)
        self.journal.status(tag,"submitted","321")
        self.fake.orders=[{"tag":tag,"id":321,"status":"partially_filled"}]
        result=self.bot().run_once()
        self.assertEqual(result["action"],"broker_order_status")
        self.assertEqual(result["statuses"],["partially_filled"])
        self.assertFalse(any(x[0]=="POST" for x in self.fake.calls))

    def test_reject_preview_bad_result(self):
        self.fake.broker_preview_result={"order":{"status":"rejected","result":False,"cost":44,"fees":0}}
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            with self.assertRaisesRegex(Halt,"preview rejected"):
                self.bot(armed=True,enabled=True).run_once()
        self.assertEqual(len([x for x in self.fake.calls if x[2].get("preview")=="false"]),0)

    def test_reject_preview_cost_exceeds_maximum(self):
        self.fake.broker_preview_result={"order":{"status":"ok","result":True,"cost":62,"fees":0.08}}
        with patch.dict(os.environ,{"SF_TRADIER_PAPER_ORDER_ENABLE":ARM_TOKEN}):
            with self.assertRaisesRegex(Halt,"exceeds max budget"):
                self.bot(armed=True,enabled=True).run_once()
        self.assertFalse(self.fake.submitted)

    def test_reject_open_positions_or_orders(self):
        self.fake.positions=[{"symbol":"T","quantity":1}]
        with self.assertRaisesRegex(Halt,"positions"):
            self.bot().run_once()
        self.fake.positions=[]
        self.fake.orders=[{"tag":"another-order","status":"open"}]
        with self.assertRaisesRegex(Halt,"open paper order"):
            self.bot().run_once()

    def test_broker_tag_duplicate(self):
        tag=self.plan.key(self.now.astimezone(NY).date())
        self.fake.orders=[{"tag":tag,"status":"filled"}]
        with self.assertRaisesRegex(Halt,"prevent duplicate"):
            self.bot().run_once()

    def test_limit_and_daily_loss(self):
        self.fake.total_cash=Decimal("39.00")
        with self.assertRaisesRegex(Halt,"cash"):
            self.bot().run_once()
        self.fake.total_cash=Decimal("100.00")
        self.fake.close_pl=Decimal("-11")
        with self.assertRaisesRegex(Halt,"daily loss cap"):
            self.bot().run_once()

    def test_no_external_hostname(self):
        self.assertEqual(SANDBOX_HOST,"https://sandbox.tradier.com/v1")
        with self.assertRaisesRegex(Halt,"unsupported sandbox"):
            self.api._http("POST","https://example.com/order",{})
        self.assertEqual(self.fake.calls,[])

    def test_risk_configuration(self):
        original=plan_data()
        for key,val in (("max_cost","61"),("quantity",6),("profit_limit","0.20"),
                        ("option_symbol","AAPL300101C00021000"),("direction","up"),
                        ("enabled","true")):
            bad=dict(original);bad[key]=val
            with self.subTest(key=key):
                with self.assertRaises(Halt):
                    Plan.from_dict(bad)

    def test_foreground_session_only(self):
        self.now=datetime(2026,10,21,15,5,tzinfo=NY).astimezone(timezone.utc)
        self.fake.now=self.now
        result=self.bot().run_once()
        self.assertEqual(result["action"],"blocked")
        self.assertEqual(self.fake.calls,[])


if __name__=="__main__":
    unittest.main()
