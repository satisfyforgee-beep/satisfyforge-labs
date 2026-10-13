import tempfile
import unittest
from pathlib import Path

from normalize import build_payload, normalize_csv, summarize


class AnalyticsNormalizeTests(unittest.TestCase):
    def make_csv(self, text):
        tmp = tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='', suffix='.csv', delete=False)
        tmp.write(text)
        tmp.close()
        return Path(tmp.name)

    def test_aliases_and_currency_parse(self):
        path = self.make_csv('Video ID,Video title,Video views,Likes,Comments,Shares,Estimated revenue\nabc,Test clip,"1,200",120,12,8,$4.50\n')
        rows = normalize_csv(path, 'youtube', observed_at='2026-10-13T00:00:00+00:00')
        self.assertEqual(rows[0].content_id, 'abc')
        self.assertEqual(rows[0].views, 1200)
        self.assertEqual(rows[0].revenue, 4.5)

    def test_summary_uses_observed_metrics_only(self):
        path = self.make_csv('id,title,views,likes,comments,shares,saves,clicks,revenue\na,A,1000,100,10,20,5,25,10\nb,B,500,20,5,5,0,5,20\n')
        rows = normalize_csv(path, 'tiktok', observed_at='2026-10-13T00:00:00+00:00')
        summary = summarize(rows)
        self.assertEqual(summary['totals']['views'], 1500)
        self.assertEqual(summary['totals']['revenue'], 30.0)
        self.assertEqual(summary['leaders']['revenue']['title'], 'B')
        self.assertEqual(summary['leaders']['views']['title'], 'A')

    def test_payload_schema(self):
        path = self.make_csv('id,title,views\na,A,100\n')
        payload = build_payload(normalize_csv(path, 'instagram', observed_at='2026-10-13T00:00:00+00:00'))
        self.assertEqual(payload['schema'], 'satisfyforge.analytics.v1')
        self.assertEqual(len(payload['items']), 1)


if __name__ == '__main__':
    unittest.main()
