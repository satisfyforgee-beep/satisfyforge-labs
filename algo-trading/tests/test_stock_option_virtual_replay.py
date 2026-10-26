"""Offline tests for stock/option historical control, no broker writes."""
import io
import json
import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from zerocost_bot.stock_option_virtual_replay import (
    stock_bars, option_days, stock_control, option_control,
    sandbox_readonly, STOCK_NAMES, OCC_NAMES,
)

_ET=ZoneInfo("America/New_York")


class FakeOpen:
    def __init__(self, body):
        self.data = json.dumps(body).encode()
        self.request = None

    def __call__(self, request, timeout=9):
        self.request = request
        return io.BytesIO(self.data)


def stock_rows(price="10.00"):
    day = datetime(2026,10,26,9,30,tzinfo=_ET)
    out = []
    for i in range(78):
        t = day + timedelta(minutes=i*5)
        out.append((t, Decimal(price), Decimal("10.10"),
                    Decimal("9.95"), Decimal("10.05"), 10000))
    return out


def option_rows():
    start = date(2026, 10, 1)
    dates = []
    while len(dates)<18:
        if start.weekday()<5:
            dates.append(start)
        start+=timedelta(days=1)
    return [(d, Decimal(".20"), Decimal(".25"),
             Decimal(".10"), Decimal(".18")) for d in dates]


class HistoricalControlTests(unittest.TestCase):
    def test_only_sandbox_get_allowlist(self):
        with self.assertRaises(ValueError):
            sandbox_readonly("/accounts/A/orders", {},token="FAKE")
        fake = FakeOpen({"series":{"data":[]}})
        sandbox_readonly("/markets/timesales", {"symbol":"F"},
                         token="FAKE", opener=fake)
        self.assertEqual(fake.request.get_method(), "GET")
        self.assertIn("sandbox.tradier.com", fake.request.full_url)
        self.assertNotIn("FAKE",fake.request.full_url)
        self.assertNotIn("api.tradier.com",fake.request.full_url)

    def test_stock_parser_requires_full_and_regular_session(self):
        fake = FakeOpen({"series":{"data":[{
            "time": str(r[0].isoformat()),
            "open":str(r[1]),"high":str(r[2]),
            "low":str(r[3]),"close":str(r[4]),"volume":r[5],
        } for r in stock_rows()]}})
        got = stock_bars("F",token="FAKE",opener=fake)
        self.assertEqual(len(got),78)
        self.assertEqual(got[-1][0].minute,55)
        with self.assertRaises(ValueError):
            stock_bars("BTC",token="FAKE",opener=fake)

    def test_option_parser_checks_instrument_and_daily_prices(self):
        fake=FakeOpen({"history":{"day":[{
            "date":x[0].isoformat(),"open":str(x[1]),
            "high":str(x[2]),"low":str(x[3]),"close":str(x[4]),
        } for x in option_rows()]}})
        got=option_days(OCC_NAMES[0],token="FAKE",opener=fake)
        self.assertEqual(len(got),18)
        self.assertEqual(got[0][0],date(2026,10,1))
        with self.assertRaises(ValueError):
            option_days("NOT_AN_OPTION",token="FAKE",opener=fake)

    def test_three_stock_controls_and_no_margin_or_broker_order(self):
        inputs={s:stock_rows() for s in STOCK_NAMES}
        result=stock_control(inputs)
        self.assertEqual(result["virtual_completed_roundtrips"],3)
        self.assertEqual(result["broker_orders_sent"],0)
        self.assertEqual({x["symbol"] for x in result["events"]},set(STOCK_NAMES))
        self.assertEqual(Decimal(result["net_pnl_after_model_costs"]), Decimal("0.03"))
        self.assertTrue(all(x["model_not_broker_fill"] for x in result["events"]))
        self.assertGreaterEqual(Decimal(result["ending_cash"]),0)

    def test_options_model_contract_multiplier_and_t_plus_one(self):
        result=option_control({s:option_rows() for s in OCC_NAMES})
        self.assertGreaterEqual(result["virtual_completed_roundtrips"],6)
        self.assertEqual(result["broker_orders_sent"],0)
        self.assertTrue(all(x["multiplier"]==100 for x in result["events"]))
        self.assertTrue(all(Decimal(x["modeled_debit_with_fee"])<=30
                            for x in result["events"]))
        self.assertEqual(
            Decimal(result["end_cash_after_hypothetical_settlement"]),
            Decimal(result["end_cash_settled_at_final_observation"])
            +Decimal(result["unsettled_sale_proceeds_at_final_observation"]))
        self.assertTrue(all(x["model_not_broker_fill"] for x in result["events"]))

    def test_missing_stock_close_and_malformed_options_block(self):
        inputx={s:stock_rows() for s in STOCK_NAMES}
        inputx["CLF"]=inputx["CLF"][:-1]
        with self.assertRaisesRegex(ValueError, "historical 10:00"):
            stock_control({"CLF":inputx["CLF"][7:],
                           "F":inputx["F"],"AAL":inputx["AAL"]})
        with self.assertRaises(ValueError):
            option_control({s: [("BAD",)] for s in OCC_NAMES})


if __name__ == "__main__":
    unittest.main()
