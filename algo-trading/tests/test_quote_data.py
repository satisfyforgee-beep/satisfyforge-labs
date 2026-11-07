import unittest
from datetime import datetime, timedelta, timezone

from zerocost_bot.alpaca import latest_equity_quotes, validate_option_snapshot_pages


NOW = datetime(2026, 11, 7, 15, 0, tzinfo=timezone.utc)
CALL = "AAPL261120C00200000"
PUT = "MSFT261120P00300000"


def snapshot(symbol, timestamp="2026-11-07T14:59:55Z", bid="1.00", ask="1.05"):
    return {symbol: {"latestQuote": {"bp": bid, "ap": ask, "t": timestamp}}}


class OptionSnapshotPageTests(unittest.TestCase):
    def test_complete_multi_page_opra_chain_is_execution_eligible(self):
        pages = [
            {"request_page_token": None, "snapshots": snapshot(CALL),
             "next_page_token": "page-2"},
            {"request_page_token": "page-2", "snapshots": snapshot(PUT),
             "next_page_token": None},
        ]
        rows = validate_option_snapshot_pages([CALL, PUT], pages, NOW, feed="opra")
        self.assertEqual([row["symbol"] for row in rows], [CALL, PUT])
        self.assertTrue(all(row["execution_eligible"] for row in rows))
        self.assertTrue(all(not row["delayed_or_modified"] for row in rows))

    def test_indicative_feed_is_never_execution_eligible(self):
        rows = validate_option_snapshot_pages(
            [CALL], [{"request_page_token": None, "snapshots": snapshot(CALL),
                      "next_page_token": None}], NOW, feed="indicative")
        self.assertFalse(rows[0]["execution_eligible"])
        self.assertTrue(rows[0]["delayed_or_modified"])
        self.assertEqual(rows[0]["source"], "ALPACA_INDICATIVE")

    def test_missing_symbol_and_incomplete_chain_fail_closed(self):
        cases = [
            [{"request_page_token": None, "snapshots": snapshot(CALL),
              "next_page_token": None}],
            [{"request_page_token": None, "snapshots": snapshot(CALL),
              "next_page_token": "missing"}],
        ]
        for pages in cases:
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                validate_option_snapshot_pages([CALL, PUT], pages, NOW, feed="opra")

    def test_cycles_duplicate_snapshots_and_orphan_pages_fail_closed(self):
        cases = [
            [{"request_page_token": None, "snapshots": {}, "next_page_token": "p2"},
             {"request_page_token": "p2", "snapshots": snapshot(CALL),
              "next_page_token": "p2"}],
            [{"request_page_token": None, "snapshots": snapshot(CALL),
              "next_page_token": "p2"},
             {"request_page_token": "p2", "snapshots": snapshot(CALL),
              "next_page_token": None}],
            [{"request_page_token": None, "snapshots": snapshot(CALL),
              "next_page_token": None},
             {"request_page_token": "orphan", "snapshots": {},
              "next_page_token": None}],
        ]
        for pages in cases:
            with self.subTest(pages=pages), self.assertRaises(ValueError):
                validate_option_snapshot_pages([CALL], pages, NOW, feed="opra")

    def test_stale_future_crossed_and_malformed_quotes_fail_closed(self):
        payloads = [
            snapshot(CALL, (NOW - timedelta(seconds=16)).isoformat()),
            snapshot(CALL, (NOW + timedelta(seconds=1)).isoformat()),
            snapshot(CALL, bid="1.10", ask="1.00"),
            {CALL: {"latestQuote": {"bp": "NaN", "ap": "1.00",
                                    "t": "2026-11-07T14:59:55Z"}}},
            {CALL: {}},
        ]
        for payload in payloads:
            pages = [{"request_page_token": None, "snapshots": payload,
                      "next_page_token": None}]
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_option_snapshot_pages([CALL], pages, NOW, feed="opra")

    def test_duplicate_requested_symbols_and_bad_feed_fail_closed(self):
        pages = [{"request_page_token": None, "snapshots": snapshot(CALL),
                  "next_page_token": None}]
        with self.assertRaises(ValueError):
            validate_option_snapshot_pages([CALL, CALL], pages, NOW, feed="opra")
        with self.assertRaises(ValueError):
            validate_option_snapshot_pages([CALL], pages, NOW, feed="unknown")


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
