import unittest
from datetime import timezone
from urllib.parse import parse_qs, urlsplit

from zerocost_bot.alpaca import get_historical_bars, latest_equity_quotes


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


class HistoricalBarPaginationTests(unittest.TestCase):
    @staticmethod
    def bar(timestamp):
        return {"t": timestamp, "o": 10, "h": 11, "l": 9, "c": 10.5,
                "v": 1000}

    def test_exhausts_all_pages_before_returning(self):
        requests = []

        def transport(request):
            requests.append(request)
            token = parse_qs(urlsplit(request.full_url).query).get("page_token")
            if token is None:
                return {"symbol": "SOFI",
                        "bars": [self.bar("2026-11-05T14:30:00.123456789Z")],
                        "next_page_token": "page-2"}
            self.assertEqual(token, ["page-2"])
            return {"symbol": "SOFI",
                    "bars": [self.bar("2026-11-05T14:31:00Z")],
                    "next_page_token": None}

        rows = get_historical_bars(
            "sofi", "2026-11-05T14:30:00Z", "2026-11-05T14:32:00Z",
            "test", "test", transport)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(requests), 2)
        self.assertTrue(all(request.get_method() == "GET" for request in requests))
        first_query = parse_qs(urlsplit(requests[0].full_url).query)
        self.assertEqual(first_query["feed"], ["iex"])
        self.assertEqual(first_query["adjustment"], ["split"])

    def test_repeated_pagination_token_fails_closed(self):
        def transport(_request):
            return {"symbol": "SOFI", "bars": [],
                    "next_page_token": "same-token"}

        with self.assertRaisesRegex(ValueError, "token repeated"):
            get_historical_bars("SOFI", "2026-11-05", "2026-11-06",
                                "test", "test", transport)

    def test_duplicate_or_nonmonotonic_bars_fail_closed(self):
        cases = [
            [self.bar("2026-11-05T14:30:00Z"),
             self.bar("2026-11-05T14:30:00Z")],
            [self.bar("2026-11-05T14:31:00Z"),
             self.bar("2026-11-05T14:30:00Z")],
        ]
        for bars in cases:
            with self.subTest(bars=bars):
                with self.assertRaises(ValueError):
                    get_historical_bars(
                        "SOFI", "2026-11-05", "2026-11-06", "test", "test",
                        lambda _request, rows=bars: {
                            "symbol": "SOFI", "bars": rows,
                            "next_page_token": None})

    def test_malformed_page_or_symbol_mismatch_fails_closed(self):
        payloads = [
            {},
            {"symbol": "SOFI", "bars": {}, "next_page_token": None},
            {"symbol": "AAPL", "bars": [], "next_page_token": None},
            {"symbol": "SOFI", "bars": [], "next_page_token": ""},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    get_historical_bars(
                        "SOFI", "2026-11-05", "2026-11-06", "test", "test",
                        lambda _request, result=payload: result)


if __name__ == "__main__":
    unittest.main()
