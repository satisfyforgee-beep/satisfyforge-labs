"""Tests the actual GitHub Actions entrypoint; never sends a broker request."""
import io
import json
import os
import unittest
from unittest.mock import patch
from decimal import Decimal

import tradier_paper_cli


class DummyClient:
    def __init__(self, quote=None, error=False):
        self.calls = []
        self.quote = quote or {
            "quotes": {"quote": {
                "symbol": "SOFI", "ask": 15.05,
            }}
        }
        self.error = error

    def _request(self, method, path, query=None):
        self.calls.append((method, path, query))
        if self.error:
            return {"quotes": None}
        return self.quote

    def state(self):
        return {"cash": Decimal("100000"), "positions": [],
                "orders": [], "pending": 0}

    def preview(self, symbol, price):
        self.calls.append(("POST_PREVIEW_ONLY", symbol, str(price)))
        return {"status": "PREVIEW_OK", "entry_limit": str(price),
                "simulated_only": True, "otoco_exits": True}


class PreviewSmokeTests(unittest.TestCase):
    def test_quote_price_is_delayed_research_only(self):
        client = DummyClient()
        self.assertEqual(tradier_paper_cli.quote_limit(client, "SOFI"),
                         Decimal("15.06"))
        self.assertEqual(client.calls[0][0], "GET")
        self.assertEqual(client.calls[0][1], "/markets/quotes")

    def test_missing_or_ambiguous_market_data_blocks(self):
        from zerocost_bot.tradier_paper import BrokerUncertain
        for quote in (
            {"quotes": None},
            {"quotes": {"quote": []}},
            {"quotes": {"quote": {"symbol": "AAL", "ask": 15.05}}},
            {"quotes": {"quote": {"symbol": "SOFI", "ask": "NaN"}}},
        ):
            with self.subTest(quote=quote):
                with self.assertRaises(BrokerUncertain):
                    tradier_paper_cli.quote_limit(DummyClient(quote), "SOFI")

    def test_quote_outside_bounded_price_window_blocks(self):
        from zerocost_bot.tradier_paper import PaperBlocked
        with self.assertRaises(PaperBlocked):
            tradier_paper_cli.quote_limit(DummyClient(
                {"quotes": {"quote": {"symbol": "SOFI", "ask": "25.01"}}}), "SOFI")

    def test_unconnected_secret_is_not_requested_or_logged(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stderr", new_callable=io.StringIO) as err:
                result = tradier_paper_cli.main(["--preview"])
        self.assertEqual(result, 2)
        self.assertNotIn("Bearer", err.getvalue())

    def test_invalid_instructions_cannot_submit(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                tradier_paper_cli.main(["--paper-submit"])

    def test_sanitized_error_stage_does_not_leak_credentials(self):
        from zerocost_bot.tradier_paper import BrokerUncertain
        class BrokenClient(DummyClient):
            last_stage = "orders"
            def state(self):
                raise BrokerUncertain("secret-should-not-appear")
        with patch("tradier_paper_cli.TradierSandbox", return_value=BrokenClient()):
            with self.assertRaises(tradier_paper_cli.SafeStageError) as e:
                tradier_paper_cli.inspect_or_preview("SOFI", True)
        self.assertEqual(str(e.exception), "orders")
        self.assertNotIn("secret-should-not-appear", str(e.exception))

    def test_sanitized_connected_preview_report(self):
        with patch("tradier_paper_cli.TradierSandbox", return_value=DummyClient()):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                result = tradier_paper_cli.inspect_or_preview("SOFI", True)
                print(json.dumps(result, sort_keys=True))
        self.assertTrue(result["paper_account_connected"])
        self.assertFalse(result["paper_order_created"])
        self.assertFalse(result["live_money_trade"])
        self.assertEqual(result["preview"]["status"], "PREVIEW_OK")
        self.assertNotIn("VA00001234", out.getvalue())
        self.assertNotIn("test-token", out.getvalue())


if __name__ == "__main__":
    unittest.main()
