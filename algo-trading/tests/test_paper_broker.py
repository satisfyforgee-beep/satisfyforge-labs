import unittest
from datetime import datetime,timezone
from unittest.mock import patch
from zerocost_bot.paper_broker import PaperBroker,make_bracket
from paper_executor import proposed_order


class SafeBrokerTests(unittest.TestCase):
    def test_bracket_has_stops_and_paper_id(self):
        o=make_bracket("SOFI",2,10,client_id="sf-paper-v01-202610201400-SOFI")
        self.assertEqual(o["order_class"],"bracket")
        self.assertEqual(o["take_profit"]["limit_price"],"10.35")
        self.assertEqual(o["stop_loss"]["stop_price"],"9.80")
    def test_reject_invalid_symbol_or_quantity(self):
        with self.assertRaises(ValueError):
            make_bracket("BTC/USD",1,10,client_id="sf-paper-v01-test")
        with self.assertRaises(ValueError):
            make_bracket("SOFI",0,10,client_id="sf-paper-v01-test")
    def test_paper_order_disabled_without_two_gates(self):
        calls=[]
        broker=PaperBroker("fakekey","fakesecret",
                           transport=lambda *args:calls.append(args))
        order=make_bracket("SOFI",1,10,client_id="sf-paper-v01-202610201400-SOFI")
        with self.assertRaises(RuntimeError):
            broker.paper_submit(order,explicitly_armed=False)
        with patch.dict("os.environ",{"SF_PAPER_ORDER_ENABLE":""}):
            with self.assertRaises(RuntimeError):
                broker.paper_submit(order,explicitly_armed=True)
        self.assertEqual(calls,[])
    def test_stale_data_blocks_order(self):
        broker=PaperBroker("a","b",transport=lambda *a:None)
        snapshot={"account":{"status":"ACTIVE","trading_blocked":False,
                             "equity":"1000","buying_power":"1000"},
                  "clock":{"is_open":True},"positions":[],"open_orders":[],
                  "today_orders":[]}
        with self.assertRaises(RuntimeError):
            broker.validate(snapshot,"SOFI",datetime(2020,1,1,tzinfo=timezone.utc),10)
    def test_duplicate_position_blocks_order(self):
        broker=PaperBroker("a","b",transport=lambda *a:None)
        snapshot={"account":{"status":"ACTIVE","equity":"1000","buying_power":"1000"},
                  "clock":{"is_open":True},"positions":[{"symbol":"SOFI"}],
                  "open_orders":[],"today_orders":[]}
        with self.assertRaises(RuntimeError):
            broker.validate(snapshot,"SOFI",datetime.now(timezone.utc),10)
    def test_daily_loss_cap_blocks_new_entry(self):
        broker=PaperBroker("a","b",transport=lambda *a:None)
        snapshot={"account":{"status":"ACTIVE","equity":"960","last_equity":"1000",
                             "buying_power":"960"},
                  "clock":{"is_open":True},"positions":[],"open_orders":[],
                  "today_orders":[]}
        with self.assertRaisesRegex(RuntimeError,"daily loss limit"):
            broker.validate(snapshot,"SOFI",datetime.now(timezone.utc),10)

    def test_missing_daily_risk_baseline_fails_closed(self):
        broker=PaperBroker("a","b",transport=lambda *a:None)
        snapshot={"account":{"status":"ACTIVE","equity":"1000",
                             "buying_power":"1000"},
                  "clock":{"is_open":True},"positions":[],"open_orders":[],
                  "today_orders":[]}
        with self.assertRaisesRegex(RuntimeError,"daily loss limit"):
            broker.validate(snapshot,"SOFI",datetime.now(timezone.utc),10)

    def test_empty_price_data_never_calls_broker(self):
        class Bomb:
            def snapshot(self):
                raise AssertionError("should not call")
        self.assertEqual(proposed_order(Bomb(),[])["action"],"skip")


if __name__=="__main__":
    unittest.main()
