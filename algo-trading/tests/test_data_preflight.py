import io
import json
import os
import unittest
from urllib.error import HTTPError
from urllib.request import Request
from unittest import mock

from data_preflight import (_get_json, _quote_json, _keychain_secret,
                            check_connections, load_credentials)


class PreflightTests(unittest.TestCase):
    def test_missing_credentials_make_no_network_calls(self):
        with mock.patch.dict(os.environ, {
            "TRADIER_SANDBOX_TOKEN": "", "ALPACA_PAPER_KEY": "", "ALPACA_PAPER_SECRET": ""}):
            result = check_connections(network=True, transport=lambda request: self.fail("unexpected GET"))
        self.assertEqual(result["connections"]["tradier_sandbox"], "MISSING_CREDENTIAL")
        self.assertEqual(result["connections"]["alpaca_paper"], "MISSING_CREDENTIAL")
        self.assertFalse(result["broker_order_submission_enabled"])
        self.assertFalse(result["live_money_enabled"])

    def test_env_is_preferred_without_keychain(self):
        with mock.patch.dict(os.environ, {"TRADIER_SANDBOX_TOKEN": "sandbox-only",
                                       "ALPACA_PAPER_KEY": "paper-key", "ALPACA_PAPER_SECRET": "paper-secret"}), \
             mock.patch("data_preflight._keychain_secret") as keychain:
            dry = check_connections()
        keychain.assert_not_called()
        self.assertEqual(dry["connections"]["alpaca_paper"], "READY")
        self.assertEqual(dry["connections"]["tradier_sandbox"], "READY")
        self.assertFalse(dry["network_attempted"])
        self.assertNotIn("paper-secret", json.dumps(dry))

    def test_read_only_paper_hosts_sanitized_response(self):
        requests = []

        def fake(request):
            requests.append(request)
            if "sandbox.tradier.com" in request.full_url:
                return {"profile": {"id": "private-user", "account": [{"account_number": "hidden"}]}}
            if "paper-api.alpaca.markets" in request.full_url:
                return {"id": "private-account", "status": "ACTIVE", "cash": "9999"}
            return {"quotes": {"SOFI": {"bp": 12.01, "ap": 12.02, "t": "2026-10-27T14:15:00Z"}}}

        with mock.patch.dict(os.environ, {"TRADIER_SANDBOX_TOKEN": "private-token",
                                       "ALPACA_PAPER_KEY": "paper-key", "ALPACA_PAPER_SECRET": "paper-secret"}):
            result = check_connections(network=True, transport=fake)
        self.assertEqual(result["connections"], {"tradier_sandbox": "CONNECTED",
                                                 "alpaca_paper": "CONNECTED",
                                                 "alpaca_iex_quotes": "CONNECTED"})
        self.assertEqual(len(requests), 3)
        self.assertTrue(all(req.get_method() == "GET" for req in requests))
        self.assertTrue(all("api.alpaca.markets/v2/orders" not in req.full_url for req in requests))
        self.assertIn("feed=iex", requests[-1].full_url)
        printed = json.dumps(result)
        for secret in ("private-token", "paper-key", "paper-secret", "private-user", "private-account", "9999"):
            self.assertNotIn(secret, printed)

    def test_auth_failure_is_redacted(self):
        def denied(request):
            raise HTTPError(request.full_url, 401, "token leaked here", {}, io.BytesIO(b"secret"))

        with mock.patch.dict(os.environ, {"TRADIER_SANDBOX_TOKEN": "private-token",
                                       "ALPACA_PAPER_KEY": "", "ALPACA_PAPER_SECRET": ""}):
            result = check_connections(network=True, transport=denied)
        self.assertEqual(result["connections"]["tradier_sandbox"], "AUTH_FAILED")
        self.assertNotIn("leaked", json.dumps(result))
        self.assertNotIn("private-token", json.dumps(result))

    def test_partial_paper_pair_is_not_used(self):
        with mock.patch.dict(os.environ, {"TRADIER_SANDBOX_TOKEN": "", "ALPACA_PAPER_KEY": "key",
                                       "ALPACA_PAPER_SECRET": ""}):
            result = check_connections(network=True, transport=lambda request: self.fail("not ready"))
        self.assertEqual(result["connections"]["alpaca_paper"], "INCOMPLETE_CREDENTIAL_PAIR")

    def test_fixed_endpoint_allowlist_blocks_live_host_and_posts(self):
        for url in ("https://api.tradier.com/v1/user/profile",
                    "https://api.alpaca.markets/v2/account",
                    "https://paper-api.alpaca.markets/v2/orders"):
            with self.assertRaises(ValueError):
                _get_json(Request(url, method="GET"), transport=lambda request: {})
        with self.assertRaises(ValueError):
            _get_json(Request("https://sandbox.tradier.com/v1/user/profile", method="POST"),
                      transport=lambda request: {})
        with self.assertRaises(ValueError):
            _quote_json(Request("https://data.alpaca.markets/v2/stocks/quotes/latest?feed=sip&symbols=SOFI"),
                        transport=lambda request: {})

    def test_keychain_lookup_is_opt_in_and_exact(self):
        with mock.patch.dict(os.environ, {"TRADIER_SANDBOX_TOKEN": "", "ALPACA_PAPER_KEY": "", "ALPACA_PAPER_SECRET": ""}), \
             mock.patch("data_preflight.platform.system", return_value="Darwin"), \
             mock.patch("data_preflight.subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="secret-value\n")
            self.assertEqual(load_credentials(allow_keychain=False)["TRADIER_SANDBOX_TOKEN"], None)
            run.assert_not_called()
            found = load_credentials(allow_keychain=True)
            self.assertEqual(found["TRADIER_SANDBOX_TOKEN"], "secret-value")
            self.assertEqual(run.call_count, 3)
            self.assertTrue(all("find-generic-password" in call.args[0] for call in run.call_args_list))
        with mock.patch("data_preflight.platform.system", return_value="Linux"):
            self.assertIsNone(_keychain_secret("com.satisfyforge.tradier.sandbox"))


if __name__ == "__main__":
    unittest.main()
