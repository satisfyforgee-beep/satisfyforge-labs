import unittest
from datetime import datetime,timezone,timedelta
from zerocost_bot.engine import Settings, PaperEngine, Bar
from cli import demo_data,replay


BASE=datetime(2026,10,20,13,30,tzinfo=timezone.utc)


def b(n,price,high=None,low=None,vol=10000,symbol="TEST"):
    return Bar(symbol,BASE+timedelta(minutes=n),price,high or price,low or price,price,vol)


class TradingTests(unittest.TestCase):
    def test_replay_deterministic(self):
        r1=replay(demo_data(),Settings())["summary"]
        r2=replay(demo_data(),Settings())["summary"]
        self.assertEqual(r1,r2)
        self.assertIn("round_trips",r1)
    def test_duplicate_bar_fails_closed(self):
        e=PaperEngine(Settings())
        row=b(0,10)
        e.on_bar(row)
        self.assertEqual(e.on_bar(row),[])
        self.assertEqual(len(e.bars["TEST"]),1)
    def test_invalid_bars(self):
        e=PaperEngine(Settings())
        with self.assertRaises(ValueError):
            e.on_bar(Bar("TEST",BASE,10,9,8,10,100))
        with self.assertRaises(ValueError):
            e.on_bar(Bar("TEST",BASE,10,10,9,10,-1))
    def test_no_lookahead_and_next_open_only(self):
        s=Settings(lookback=2,min_history_bars=3,min_volume=10,
                   start_cash=500,max_position_fraction=.2)
        e=PaperEngine(s)
        e.on_bar(b(0,10,vol=100))
        e.on_bar(b(1,10,vol=100))
        e.on_bar(b(2,10,vol=100))
        self.assertEqual(len(e.positions),0)
        e.on_bar(b(3,10.5,vol=1000))
        self.assertEqual(len(e.positions),0)
        self.assertEqual(len(e.pending),1)
        e.on_bar(b(4,10.6,vol=1000))
        self.assertEqual(len(e.positions),1)
        self.assertTrue(any(x["action"]=="buy" and x["time"]==b(4,10.6).time.isoformat() for x in e.events))
    def test_stop_and_gap_down(self):
        s=Settings(lookback=2,min_history_bars=3,min_volume=10,
                   start_cash=500,max_position_fraction=.2)
        e=PaperEngine(s)
        for n in range(3):e.on_bar(b(n,10))
        e.on_bar(b(3,11,vol=100000))
        e.on_bar(b(4,11.05))
        self.assertEqual(len(e.positions),1)
        e.on_bar(b(5,10.2,high=10.3,low=10.1))
        self.assertEqual(len(e.positions),0)
        self.assertEqual(e.events[-1]["reason"],"gap_stop")
        self.assertLess(e.events[-1]["price"],11)
    def test_no_overspend_small_account(self):
        s=Settings(start_cash=39.41,max_position_fraction=.20,lookback=2,min_history_bars=3,min_volume=10)
        e=PaperEngine(s)
        for n in range(3):e.on_bar(b(n,14))
        e.on_bar(b(3,15,vol=10000))
        e.on_bar(b(4,15.1,vol=10000))
        self.assertEqual(len(e.positions),0)
        self.assertEqual(e.cash,39.41)
    def test_no_multiple_same_minute_entries(self):
        e=PaperEngine(Settings())
        for n in range(80):e.on_bar(demo_data()[n])
        allbuys=[x for x in e.events if x["action"]=="buy"]
        self.assertEqual(len({x["time"] for x in allbuys}),len(allbuys))
    def test_settings_bad(self):
        with self.assertRaises(ValueError):
            PaperEngine(Settings(stop_loss_fraction=-.1))


if __name__=="__main__":
    unittest.main()
