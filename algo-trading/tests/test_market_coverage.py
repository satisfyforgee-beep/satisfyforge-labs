"""Never confuse a single venue or indicative price with consolidated NBBO."""
import io
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from zerocost_bot.market_coverage import (
    AssetClass, Coverage, CoverageGate, MarketQuote,
)
from zerocost_bot.read_only_feeds import (
    alpaca_iex_quote, tradier_quote, tradier_stream_quote,
    fetch_tradier_live_quotes,
)

NOW = datetime(2026, 10, 20, 14, 35, 20, tzinfo=timezone.utc)
OCC = "SOFI261023C00015000"


def ms(t):
    return int(t.timestamp() * 1000)


def make(source="alpaca_iex", symbol="SOFI", asset=AssetClass.STOCK,
         bid=14.6, ask=14.61, now=NOW, verified=True, age=1,
         skew=0):
    return MarketQuote(source, asset, symbol, bid, ask,
                       now - timedelta(seconds=age),
                       now - timedelta(seconds=age + skew),
                       now - timedelta(milliseconds=100),
                       entitlement_verified=verified)


def tradier_raw(symbol="SOFI", bid=14.60, ask=14.61, at=NOW):
    return {"symbol": symbol,
            "bid": bid, "ask": ask, "type": "stock",
            "bid_date": ms(at - timedelta(seconds=1)),
            "ask_date": ms(at - timedelta(seconds=1))}


class ProviderIntegrityTests(unittest.TestCase):
    def test_entitlement_is_not_default(self):
        q = MarketQuote("tradier_live", AssetClass.STOCK, "SOFI",
                        14.60, 14.61, NOW, NOW, NOW)
        self.assertFalse(q.entitlement_verified)
        g = CoverageGate()
        g.ingest(q)
        self.assertEqual(g.assess("SOFI", AssetClass.STOCK, NOW).status, "BLOCKED")

    def test_free_iex_only_research(self):
        g = CoverageGate()
        g.ingest(make())
        a = g.assess("SOFI", AssetClass.STOCK, NOW)
        self.assertEqual((a.status, a.coverage, a.live_order_authorized),
                         ("RESEARCH_ONLY", "single_venue", False))

    def test_tradier_verified_live_consolidated(self):
        g = CoverageGate()
        g.ingest(make("tradier_live"))
        a = g.assess("SOFI", AssetClass.STOCK, NOW)
        self.assertEqual((a.status, a.source), ("DATA_READY", "tradier_live"))
        self.assertFalse(a.as_report()["live_order_authorized"])

    def test_prefers_consolidated_when_two_agree(self):
        g = CoverageGate()
        g.ingest(make())
        g.ingest(make("tradier_live", bid=14.59, ask=14.61))
        self.assertEqual(g.assess("SOFI", AssetClass.STOCK, NOW).source,
                         "tradier_live")

    def test_stale_consolidated_fallback_is_not_live_ready(self):
        g = CoverageGate()
        g.ingest(make("tradier_live", age=8))
        g.ingest(make())
        a = g.assess("SOFI", AssetClass.STOCK, NOW)
        self.assertEqual(a.status, "RESEARCH_ONLY")
        self.assertEqual(a.source, "alpaca_iex")

    def test_market_conflict_stops_everything(self):
        g = CoverageGate()
        g.ingest(make())
        g.ingest(make("tradier_live", bid=15.40, ask=15.42))
        self.assertEqual(g.assess("SOFI", AssetClass.STOCK, NOW).status,
                         "BLOCKED")

    def test_bad_source_and_asset_fails(self):
        with self.assertRaises(ValueError):
            make("user_supplied_super_feed").validate()
        with self.assertRaises(ValueError):
            make("tradier_live", asset=AssetClass.CRYPTO).validate()

    def test_options_require_real_occ_identifier(self):
        with self.assertRaises(ValueError):
            make("tradier_live", asset=AssetClass.OPTION).validate()
        q = make("tradier_live", symbol=OCC, asset=AssetClass.OPTION)
        q.validate()
        g = CoverageGate()
        g.ingest(q)
        self.assertEqual(g.assess(OCC, AssetClass.OPTION, NOW).status, "DATA_READY")

    def test_indicative_option_never_execution_ready(self):
        g = CoverageGate()
        g.ingest(make("alpaca_options_indicative", OCC, AssetClass.OPTION,
                      0.199, 0.20))
        self.assertEqual(g.assess(OCC, AssetClass.OPTION, NOW).status,
                         "RESEARCH_ONLY")

    def test_both_sides_require_freshness(self):
        with self.assertRaisesRegex(ValueError, "timestamps too far"):
            make(skew=10).validate()

    def test_crossed_nonfinite_and_older_late_messages(self):
        for bid, ask in [(float("nan"), 14.62),
                         (float("inf"), 14.62), (15, 14),
                         (0, 14)]:
            with self.assertRaises(ValueError):
                make(bid=bid, ask=ask).validate()
        g = CoverageGate()
        self.assertTrue(g.ingest(make()))
        self.assertFalse(g.ingest(make(age=2)))
        self.assertFalse(g.ingest(make()))

    def test_future_or_missing_timestamps(self):
        q = make(age=-10)
        with self.assertRaisesRegex(ValueError, "newer"):
            q.validate()
        bad = MarketQuote("tradier_live", AssetClass.STOCK, "SOFI",
                          10, 10.01, NOW.replace(tzinfo=None), NOW, NOW, True)
        with self.assertRaises(ValueError):
            bad.validate()

    def test_wide_spread_blocks(self):
        g = CoverageGate()
        g.ingest(make(bid=14.0, ask=14.9))
        self.assertEqual(g.assess("SOFI", AssetClass.STOCK, NOW).status,
                         "BLOCKED")

    def test_all_quotes_expired_blocks(self):
        g = CoverageGate()
        g.ingest(make(age=5))
        self.assertEqual(g.assess("SOFI", AssetClass.STOCK, NOW).status,
                         "BLOCKED")


class AdapterTests(unittest.TestCase):
    def test_iex_quote_is_never_consolidated(self):
        raw = {"T": "q", "S": "SOFI", "bp": 14.6, "ap": 14.61,
               "t": NOW.isoformat()}
        q = alpaca_iex_quote(raw, NOW, authenticated=True)
        self.assertEqual(q.coverage, Coverage.SINGLE_VENUE)
        self.assertTrue(q.entitlement_verified)

    def test_tradier_rest_is_consolidated_only_with_live_entitlement(self):
        data = tradier_raw()
        self.assertEqual(tradier_quote(data, NOW, authenticated_live=True).coverage,
                         Coverage.CONSOLIDATED)
        offline = tradier_quote(data, NOW, authenticated_live=False)
        self.assertEqual(offline.coverage, Coverage.DELAYED)
        self.assertFalse(offline.entitlement_verified)

    def test_tradier_stream_quotes_millisecond_timestamps(self):
        event = {"type": "quote", "symbol": "SOFI", "bid": 14.6,
                 "ask": 14.61,
                 "biddate": str(ms(NOW - timedelta(seconds=1))),
                 "askdate": str(ms(NOW - timedelta(seconds=1)))}
        q = tradier_stream_quote(event, NOW, authenticated_live=True)
        self.assertEqual(q.symbol, "SOFI")
        self.assertEqual(q.bid_at, NOW - timedelta(seconds=1))

    def test_tradier_catches_stale_one_sided_and_option_mismatch(self):
        bad = tradier_raw()
        bad["ask_date"] -= 20000
        with self.assertRaises(ValueError):
            tradier_quote(bad, NOW, authenticated_live=True)
        bad = tradier_raw()
        bad["type"] = "option"
        with self.assertRaises(ValueError):
            tradier_quote(bad, NOW, authenticated_live=True)

    def test_fetch_requires_two_explicit_enrollment_gates(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                fetch_tradier_live_quotes(["SOFI"],
                                          opener=lambda *a, **k: self.fail("network"))
        with patch.dict(os.environ, {"SF_TRADIER_DATA_ENABLE": "READ_ONLY_APPROVED"}, clear=True):
            with self.assertRaises(RuntimeError):
                fetch_tradier_live_quotes(["SOFI"],
                                          opener=lambda *a, **k: self.fail("network"))

    def test_fetch_reads_only_market_quotes(self):
        reqs = []
        class Context(io.StringIO):
            pass
        def fake_opener(req, timeout):
            reqs.append(req)
            self.assertEqual(timeout, 5)
            return Context(json.dumps({"quotes": {"quote": tradier_raw()}}))
        with patch.dict(os.environ, {
                "SF_TRADIER_DATA_ENABLE": "READ_ONLY_APPROVED",
                "TRADIER_LIVE_DATA_TOKEN": "test-token-not-real"}, clear=True):
            result = fetch_tradier_live_quotes(["SOFI", "SOFI"],
                                               opener=fake_opener, now=NOW)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].entitlement_verified)
        self.assertIn("/markets/quotes", reqs[0].full_url)
        self.assertNotIn("/orders", reqs[0].full_url)
        self.assertEqual(reqs[0].get_method(), "GET")

    def test_empty_tradier_response_fails_closed(self):
        with patch.dict(os.environ, {
                "SF_TRADIER_DATA_ENABLE": "READ_ONLY_APPROVED",
                "TRADIER_LIVE_DATA_TOKEN": "test-token-not-real"}, clear=True):
            with self.assertRaises(ValueError):
                fetch_tradier_live_quotes(["SOFI"],
                    opener=lambda *a, **k: io.StringIO('{"quotes":{"quote":[]}}'),
                    now=NOW)


if __name__ == "__main__":
    unittest.main()


class FreeCryptoCoverageTests(unittest.TestCase):
    def example_book(self):
        stamp = (NOW - timedelta(seconds=1)).isoformat()
        return {"error": [], "result": {"symbol": "BTC/USD",
                "bids": [{"price": "65000", "publication_ts": stamp},
                         {"price": "64999", "publication_ts": stamp}],
                "asks": [{"price": "65001", "publication_ts": stamp},
                         {"price": "65002", "publication_ts": stamp}]}}

    def test_public_crypto_quote_is_free_but_venue_only(self):
        from zerocost_bot.read_only_feeds import kraken_public_book
        q = kraken_public_book(self.example_book(), NOW, "BTC/USD")
        self.assertEqual(q.coverage, Coverage.SINGLE_VENUE)
        self.assertEqual(q.bid, 65000)
        gate = CoverageGate()
        gate.ingest(q)
        a = gate.assess("BTC/USD", AssetClass.CRYPTO, NOW)
        self.assertEqual(a.status, "RESEARCH_ONLY")
        self.assertFalse(a.live_order_authorized)

    def test_crypto_wrong_pair_fails(self):
        from zerocost_bot.read_only_feeds import kraken_public_book
        with self.assertRaises(ValueError):
            kraken_public_book(self.example_book(), NOW, "ETH/USD")

    def test_crypto_resting_order_age_is_not_snapshot_age(self):
        from zerocost_bot.read_only_feeds import kraken_public_book
        q = kraken_public_book(self.example_book(), NOW + timedelta(seconds=20),
                               "BTC/USD")
        gate = CoverageGate()
        gate.ingest(q)
        self.assertEqual(gate.assess("BTC/USD", AssetClass.CRYPTO,
                                     NOW + timedelta(seconds=20)).status,
                         "RESEARCH_ONLY")
        self.assertEqual(gate.assess("BTC/USD", AssetClass.CRYPTO,
                                     NOW + timedelta(seconds=25)).status,
                         "BLOCKED")

    def test_free_public_fetch_never_sends_api_credentials(self):
        from zerocost_bot.read_only_feeds import fetch_kraken_public_book
        seen = []
        def fake_opener(req, timeout):
            seen.append(req)
            self.assertEqual(timeout, 5)
            return io.StringIO(json.dumps(self.example_book()))
        q = fetch_kraken_public_book("BTC/USD", opener=fake_opener, now=NOW)
        self.assertEqual(q.symbol, "BTC/USD")
        self.assertEqual(seen[0].get_method(), "GET")
        self.assertIn("/public/PreTrade", seen[0].full_url)
        self.assertNotIn("/private/", seen[0].full_url)
        self.assertIsNone(seen[0].get_header("Authorization"))

    def test_crypto_rejects_unsafe_pairs(self):
        from zerocost_bot.read_only_feeds import fetch_kraken_public_book
        for symbol in ("BTC/EUR", "BTC-USD", "../private/AddOrder", ""):
            with self.assertRaises(ValueError):
                fetch_kraken_public_book(
                    symbol, opener=lambda *a, **k: self.fail("network"))
