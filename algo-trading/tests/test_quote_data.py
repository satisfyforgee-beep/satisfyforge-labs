import unittest
from datetime import timezone

from zerocost_bot.alpaca import latest_equity_quotes


class QuoteDataTests(unittest.TestCase):
    def test_iex_quote_read_only_schema(self):
        called = []

        def fake_request(req):
            called.append(req)
            return {"quotes": {"SOFI": {"bp": 14.53, "ap": 14.55,
                                        "t": "2026-10-27T13:40:00Z"}}}

        rows = latest_equity_quotes(["sofi"], "paper-test-key", "paper-test-secret", fake_request)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source"], "ALPACA_IEX")
        self.assertEqual(rows[0]["bid"], "14.53")
        self.assertEqual(rows[0]["asof"].tzinfo, timezone.utc)
        self.assertIn("feed=iex", called[0].full_url)
        self.assertEqual(called[0].get_method(), "GET")

    def test_missing_credentials_and_bad_symbols_fail_closed(self):
        with self.assertRaises(RuntimeError):
            latest_equity_quotes(["SOFI"], "", "", transport=lambda request: {})
        with self.assertRaises(ValueError):
            latest_equity_quotes(["SOFI/USD"], "test", "test", lambda request: {})

    def test_iex_nanosecond_timestamp_is_supported_on_python_39(self):
        rows = latest_equity_quotes(["SOFI"], "test", "test", lambda request: {
            "quotes": {"SOFI": {"bp": 14.53, "ap": 14.55,
                                "t": "2026-10-28T18:23:58.009248866Z"}}})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["asof"].microsecond, 9248)
        self.assertEqual(rows[0]["asof"].tzinfo, timezone.utc)

    def test_bad_quote_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            latest_equity_quotes(["SOFI"], "test", "test", lambda request: {
                "quotes": {"SOFI": {"bp": 10, "ap": 10.1, "t": "2026-10-27T13:40:00"}}})


if __name__ == "__main__":
    unittest.main()
