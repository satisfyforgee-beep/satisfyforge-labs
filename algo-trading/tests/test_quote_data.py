import unittest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from zerocost_bot.alpaca import (classify_overnight_market_data,
                                 latest_equity_quotes)

NY = ZoneInfo("America/New_York")


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

    def _overnight(self, observed_at, **changes):
        values = {
            "observed_at": observed_at,
            "data_asof": observed_at,
            "feed": "overnight",
            "data_kind": "quote",
            "trade_date": date(2026, 11, 17),
            "market_calendar_verified": True,
            "trade_date_is_holiday": False,
            "account_overnight_enabled": True,
            "account_data_entitlement_verified": True,
            "asset_overnight_tradable": True,
            "asset_overnight_halted": False,
            "quote_is_indicative": True,
        }
        values.update(changes)
        return classify_overnight_market_data(**values)

    def test_overnight_boundaries_and_dst_are_eastern_time(self):
        winter_open = datetime(2026, 11, 16, 20, 0, tzinfo=NY)
        summer_open = datetime(2026, 7, 6, 20, 0, tzinfo=NY)
        winter_close = datetime(2026, 11, 17, 4, 0, tzinfo=NY)
        self.assertTrue(self._overnight(winter_open)["research_usable"])
        self.assertTrue(self._overnight(
            summer_open, trade_date=date(2026, 7, 7))["research_usable"])
        self.assertIn("OUTSIDE_OVERNIGHT_SESSION",
                      self._overnight(winter_close)["blockers"])

    def test_trade_date_rolls_after_8pm_and_rejects_mismatch(self):
        evening = datetime(2026, 11, 16, 20, 1, tzinfo=NY)
        result = self._overnight(evening, trade_date=date(2026, 11, 16))
        self.assertEqual(result["expected_trade_date"], "2026-11-17")
        self.assertIn("TRADE_DATE_UNVERIFIED", result["blockers"])

    def test_weekend_and_holiday_fail_closed_but_half_day_needs_no_override(self):
        friday_evening = datetime(2026, 11, 20, 20, 1, tzinfo=NY)
        holiday_eve = datetime(2026, 11, 25, 20, 1, tzinfo=NY)
        self.assertIn("OUTSIDE_OVERNIGHT_SESSION", self._overnight(
            friday_evening, trade_date=date(2026, 11, 21))["blockers"])
        self.assertIn("MARKET_HOLIDAY", self._overnight(
            holiday_eve, trade_date=date(2026, 11, 26),
            trade_date_is_holiday=True)["blockers"])
        half_day_eve = datetime(2026, 11, 26, 20, 1, tzinfo=NY)
        self.assertTrue(self._overnight(
            half_day_eve, trade_date=date(2026, 11, 27))["research_usable"])

    def test_stale_and_future_data_fail_closed(self):
        observed = datetime(2026, 11, 16, 20, 5, tzinfo=NY)
        stale = self._overnight(
            observed, data_asof=datetime(2026, 11, 16, 20, 4, tzinfo=NY))
        future = self._overnight(
            observed, data_asof=datetime(2026, 11, 16, 20, 6, tzinfo=NY))
        self.assertIn("STALE_DATA", stale["blockers"])
        self.assertIn("FUTURE_DATA", future["blockers"])

    def test_indicative_and_delayed_feeds_never_become_execution_evidence(self):
        observed = datetime(2026, 11, 16, 20, 5, tzinfo=NY)
        indicative = self._overnight(observed)
        delayed = self._overnight(
            observed, feed="boats", data_kind="trade", delayed_minutes=15,
            data_asof=observed - timedelta(minutes=15),
            quote_is_indicative=None)
        for result in (indicative, delayed):
            self.assertEqual(result["state"], "RESEARCH_ONLY")
            self.assertFalse(result["execution_price_usable"])
            self.assertFalse(result["fill_evidence"])
            self.assertFalse(result["broker_submission_enabled"])

    def test_missing_provider_permissions_and_asset_flags_fail_closed(self):
        observed = datetime(2026, 11, 16, 20, 5, tzinfo=NY)
        cases = [
            ({"account_overnight_enabled": None}, "ACCOUNT_OVERNIGHT_UNVERIFIED"),
            ({"account_data_entitlement_verified": None}, "DATA_ENTITLEMENT_UNVERIFIED"),
            ({"asset_overnight_tradable": False}, "ASSET_NOT_OVERNIGHT_TRADABLE"),
            ({"asset_overnight_halted": True}, "ASSET_HALT_UNVERIFIED"),
            ({"market_calendar_verified": False}, "MARKET_CALENDAR_UNVERIFIED"),
        ]
        for changes, blocker in cases:
            with self.subTest(blocker=blocker):
                self.assertIn(blocker, self._overnight(observed, **changes)["blockers"])

    def test_unsupported_or_mislabelled_provenance_halts(self):
        observed = datetime(2026, 11, 16, 20, 5, tzinfo=NY)
        self.assertIn("INDICATIVE_PROVENANCE_UNVERIFIED", self._overnight(
            observed, quote_is_indicative=False)["blockers"])
        self.assertIn("DELAY_PROVENANCE_UNVERIFIED", self._overnight(
            observed, feed="boats", data_kind="trade", delayed_minutes=0,
            quote_is_indicative=None)["blockers"])
        self.assertIn("STALE_DATA", self._overnight(
            observed, feed="boats", data_kind="trade", delayed_minutes=15,
            data_asof=observed - timedelta(minutes=16),
            quote_is_indicative=None)["blockers"])
        self.assertIn("UNSUPPORTED_DATA_PROVENANCE", self._overnight(
            observed, feed="iex")["blockers"])

    def test_classifier_is_deterministic_and_does_not_mutate_inputs(self):
        observed = datetime(2026, 11, 16, 20, 5, tzinfo=NY)
        first = self._overnight(observed)
        second = self._overnight(observed)
        self.assertEqual(first, second)
        self.assertIsInstance(first["blockers"], tuple)


if __name__ == "__main__":
    unittest.main()
