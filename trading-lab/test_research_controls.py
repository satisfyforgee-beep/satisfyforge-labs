import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research_controls import size_long, rank_markets, compare_equity, journal_report, risk_matched_hold

class ResearchControlsTests(unittest.TestCase):
    def args(self):
        return dict(equity=500,cash=500,exposure=0,symbol_exposure=0,reserved_cash=0,
                    price=100,stop_distance=5,quantity_step=".01",inventory_verified=True)
    def test_risk_budget(self):
        r=size_long(**self.args())
        self.assertGreater(Decimal(r["quantity"]),0)
        self.assertLessEqual(Decimal(r["modeled_risk"]),Decimal("2.5"))
        self.assertFalse(r["broker_submit_allowed"])
    def test_unknown_inventory_and_loss(self):
        for change in [dict(inventory_verified=False),dict(daily_loss=5),dict(weekly_loss=15),
                       dict(drawdown=".05"),dict(cash=1000),dict(price="NaN"),dict(reserved_cash=501)]:
            self.assertEqual(size_long(**(self.args()|change))["quantity"],"0")
    def test_exposure_and_reservations(self):
        r=size_long(**(self.args()|dict(cash=100,exposure=400,symbol_exposure=250)))
        self.assertEqual(r["quantity"],"0")
        r=size_long(**(self.args()|dict(reserved_cash=499)))
        self.assertLessEqual(Decimal(r.get("modeled_debit",0)),1)
    def test_scan(self):
        now=datetime(2026,1,1,tzinfo=timezone.utc)
        bars=[]
        for i in range(101):
            t=now-timedelta(days=100-i)
            p=100+i+(i%3)*.2
            bars.append(dict(close_at=t,available_at=t,open=p,high=p+1,low=p-1,close=p))
        result=rank_markets([dict(symbol="AAA",verified=True,source="fixture",bars=bars),
                             dict(symbol="BBB",verified=False,source="fixture",bars=bars)],cutoff=now)
        self.assertEqual(result["ranked"][0]["symbol"],"AAA")
        self.assertEqual(len(result["rejected"]),1)
        self.assertFalse(result["broker_submit_allowed"])
        bars[-1]["available_at"]=now+timedelta(seconds=1)
        self.assertFalse(rank_markets([dict(symbol="AAA",verified=True,source="fixture",bars=bars)],cutoff=now)["ranked"])
    def test_compare(self):
        rows=[dict(time="2026-01-01T00:00:00Z",equity=500,hold_equity=500),
              dict(time="2026-01-02T00:00:00Z",equity=550,hold_equity=600),
              dict(time="2026-01-03T00:00:00Z",equity=495,hold_equity=500)]
        r=compare_equity(rows)
        self.assertEqual(Decimal(r["strategy"]["drawdown"]),Decimal(".1"))
        self.assertEqual(Decimal(r["cash"]["return"]),0)
        self.assertEqual(Decimal(r["allocation_matched_hold"]["drawdown"]),Decimal(1)-Decimal(500)/550)
        with self.assertRaises(ValueError): compare_equity(rows+[rows[-1]])
    def test_frozen_calibration(self):
        t=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=[dict(time=t+timedelta(days=i),equity=e,hold_equity=h) for i,(e,h) in enumerate(
              [(500,500),(510,530),(505,510),(520,550),(515,540),(530,590)])]
        r=risk_matched_hold(rows,3)
        self.assertEqual(r["start"],rows[3]["time"].isoformat())
        self.assertLessEqual(Decimal(r["allocation"]),1)
        rows[-1]["equity"]=300
        self.assertEqual(risk_matched_hold(rows,3)["allocation"],r["allocation"])
    def test_journal(self):
        class Engine:
            def orders(self):
                return [dict(client_id="one",status="FILLED",fee="1",realized_pnl="3"),
                        dict(client_id="two",status="REJECTED",reason="cash")]
        r=journal_report(Engine(),[])
        self.assertEqual(r["fees"],"1")
        self.assertEqual(r["realized_pnl"],"3")
        self.assertIsNone(r["valuation_report"])
        self.assertEqual(len(r["rejected_orders"]),1)

if __name__=="__main__":
    unittest.main()
