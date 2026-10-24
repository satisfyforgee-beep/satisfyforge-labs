import unittest
from datetime import datetime,timezone,timedelta
from zerocost_bot.engine import Bar,Settings,PaperEngine
from paper_executor import choose_signal


class HandoffTests(unittest.TestCase):
    def test_complete_history_issues_signal(self):
        start=datetime(2026,10,20,13,30,tzinfo=timezone.utc)
        data=[Bar("SOFI",start+timedelta(minutes=i),10,10,10,10,100)
              for i in range(13)]
        data.append(Bar("SOFI",start+timedelta(minutes=13),11,11,11,11,10000))
        data.append(Bar("SOFI",start+timedelta(minutes=14),11.1,11.1,11.1,11.1,10000))
        self.assertIsNotNone(choose_signal(data))
    def test_lack_of_history_fails_closed(self):
        start=datetime(2026,10,20,13,30,tzinfo=timezone.utc)
        b=Bar("SOFI",start,10,10,10,10,100)
        self.assertIsNone(choose_signal([b]))
    def test_at_most_one_entry_after_repeat_feed(self):
        start=datetime(2026,10,20,13,30,tzinfo=timezone.utc)
        e=PaperEngine(Settings(lookback=2,min_history_bars=3,min_volume=10))
        for i in range(3):
            e.on_bar(Bar("TEST",start+timedelta(minutes=i),10,10,10,10,100))
        e.on_bar(Bar("TEST",start+timedelta(minutes=3),11,11,11,11,10000))
        incoming=Bar("TEST",start+timedelta(minutes=4),11.2,11.2,11.2,11.2,10000)
        e.on_bar(incoming)
        e.on_bar(incoming)
        self.assertLessEqual(e.entries_today,1)


if __name__=="__main__":
    unittest.main()
