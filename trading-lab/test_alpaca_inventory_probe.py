import io
import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from unittest import mock

from alpaca_inventory_probe import check_alpaca_inventory


class AlpacaInventoryProbeTests(unittest.TestCase):
    START = datetime(2026, 11, 28, 10, 0, tzinfo=timezone.utc)

    @staticmethod
    def account(*, multiplier="1"):
        return {
            "id": "private-account-id",
            "account_number": "private-account-number",
            "status": "ACTIVE",
            "crypto_status": "ACTIVE",
            "trading_blocked": False,
            "account_blocked": False,
            "trade_suspended_by_user": False,
            "multiplier": multiplier,
            "cash": "543.21",
            "buying_power": "543.21",
            "equity": "543.21",
            "last_equity": "543.21",
        }

    def clock(self):
        ticks = iter(
            self.START + timedelta(milliseconds=250 * index)
            for index in range(9)
        )
        return lambda: next(ticks)

    def test_no_network_mode_reads_no_credentials_or_provider(self):
        with mock.patch("alpaca_inventory_probe.load_credentials") as load:
            result = check_alpaca_inventory(
                network=False,
                allow_keychain=True,
                transport=lambda request: self.fail("unexpected GET"),
            )
        load.assert_not_called()
        self.assertEqual(result["inventory_status"], "NOT_ATTEMPTED")
        self.assertFalse(result["network_attempted"])
        self.assertFalse(result["keychain_opted_in"])
        self.assertFalse(result["broker_order_submission_enabled"])

    def test_missing_or_partial_credentials_make_no_provider_request(self):
        cases = (
            (None, None, "MISSING_CREDENTIAL"),
            ("key", None, "INCOMPLETE_CREDENTIAL_PAIR"),
            (None, "secret", "INCOMPLETE_CREDENTIAL_PAIR"),
        )
        for key, secret, expected in cases:
            with self.subTest(expected=expected), mock.patch(
                    "alpaca_inventory_probe.load_credentials",
                    return_value={
                        "TRADIER_SANDBOX_TOKEN": None,
                        "ALPACA_PAPER_KEY": key,
                        "ALPACA_PAPER_SECRET": secret,
                    }):
                result = check_alpaca_inventory(
                    network=True,
                    transport=lambda request: self.fail("unexpected GET"),
                )
            self.assertEqual(result["inventory_status"], expected)

    def test_fenced_report_exposes_only_counts_and_safety_state(self):
        requests = []
        account = self.account()
        positions = [{
            "symbol": "PRIVATE-SYMBOL",
            "asset_class": "us_equity",
            "side": "long",
            "qty": "1",
            "cost_basis": "100",
            "asset_id": "private-asset-id",
        }]
        orders = [{
            "id": "private-order-id",
            "client_order_id": "private-client-order-id",
            "symbol": "PRIVATE-ORDER-SYMBOL",
            "asset_class": "us_equity",
            "side": "buy",
            "status": "new",
            "type": "limit",
            "qty": "1",
            "notional": None,
            "limit_price": "876.54",
        }]

        def transport(request):
            requests.append(request)
            if request.full_url.endswith("/v2/positions"):
                return positions
            if "/v2/orders?" in request.full_url:
                return orders
            return account

        credentials = {
            "TRADIER_SANDBOX_TOKEN": None,
            "ALPACA_PAPER_KEY": "private-key",
            "ALPACA_PAPER_SECRET": "private-secret",
        }
        with mock.patch(
                "alpaca_inventory_probe.load_credentials",
                return_value=credentials):
            result = check_alpaca_inventory(
                network=True,
                allow_keychain=True,
                transport=transport,
                clock=self.clock(),
            )

        self.assertEqual(result["inventory_status"], "FENCED")
        self.assertEqual(result["cash_only_eligibility"], "REVIEW_REQUIRED")
        self.assertEqual(result["position_count"], 1)
        self.assertEqual(result["open_order_count"], 1)
        self.assertEqual(len(requests), 4)
        self.assertTrue(all(request.get_method() == "GET" for request in requests))
        self.assertTrue(all(
            request.full_url.startswith("https://paper-api.alpaca.markets/")
            for request in requests
        ))
        printed = json.dumps(result)
        for private in (
                "private-key", "private-secret", "private-account-id",
                "private-account-number", "PRIVATE-SYMBOL",
                "private-order-id", "private-client-order-id", "543.21",
                "876.54"):
            self.assertNotIn(private, printed)
        self.assertFalse(result["raw_provider_data_displayed"])
        self.assertFalse(result["live_money_enabled"])

    def test_margin_or_short_exposure_blocks_cash_only_eligibility(self):
        for multiplier, side in (("4", "long"), ("1", "short")):
            with self.subTest(multiplier=multiplier, side=side):
                account = self.account(multiplier=multiplier)

                def transport(request):
                    if request.full_url.endswith("/v2/positions"):
                        return [{
                            "symbol": "PRIVATE", "asset_class": "us_equity",
                            "side": side, "qty": "1", "cost_basis": "100",
                        }]
                    if "/v2/orders?" in request.full_url:
                        return []
                    return account

                with mock.patch(
                        "alpaca_inventory_probe.load_credentials",
                        return_value={
                            "TRADIER_SANDBOX_TOKEN": None,
                            "ALPACA_PAPER_KEY": "key",
                            "ALPACA_PAPER_SECRET": "secret",
                        }):
                    result = check_alpaca_inventory(
                        network=True,
                        transport=transport,
                        clock=self.clock(),
                    )
                self.assertEqual(result["inventory_status"], "FENCED")
                self.assertEqual(result["cash_only_eligibility"], "BLOCKED")

    def test_provider_and_capture_failures_are_sanitized(self):
        credentials = {
            "TRADIER_SANDBOX_TOKEN": None,
            "ALPACA_PAPER_KEY": "private-key",
            "ALPACA_PAPER_SECRET": "private-secret",
        }

        def denied(request):
            raise HTTPError(
                request.full_url, 401, "private provider message", {},
                io.BytesIO(b"private response body"),
            )

        def malformed(request):
            if request.full_url.endswith("/v2/positions"):
                return {"not": "a list"}
            if "/v2/orders?" in request.full_url:
                return []
            return self.account()

        with mock.patch(
                "alpaca_inventory_probe.load_credentials",
                return_value=credentials):
            auth = check_alpaca_inventory(
                network=True, transport=denied, clock=self.clock())
            bad = check_alpaca_inventory(
                network=True, transport=malformed, clock=self.clock())
        self.assertEqual(auth["inventory_status"], "AUTH_FAILED")
        self.assertEqual(bad["inventory_status"], "HALT_INVENTORY_UNVERIFIED")
        printed = json.dumps({"auth": auth, "bad": bad})
        self.assertNotIn("private provider message", printed)
        self.assertNotIn("private response body", printed)
        self.assertNotIn("private-key", printed)


if __name__ == "__main__":
    unittest.main()
