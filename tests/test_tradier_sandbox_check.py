"""Offline contract tests. No token or network needed."""
import importlib.util
import io
from pathlib import Path
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

FILE = Path(__file__).resolve().parents[1] / "scripts" / "tradier_sandbox_check.py"
spec = importlib.util.spec_from_file_location("tradier_sandbox_check", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class MockResponse(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

class SandboxCheckTests(unittest.TestCase):
    def test_profile_read_only_and_no_identifier_printed(self):
        seen = []
        def fake(request, timeout):
            seen.append((request.full_url, request.get_method(), request.get_header("Authorization")))
            return MockResponse(b'{"profile":{"account":{"account_number":"PRIVATE","status":"active"}}}')
        out = io.StringIO()
        with redirect_stdout(out):
            mod.check("fake-token", opener=fake)
        self.assertEqual(seen[0][0], "https://sandbox.tradier.com/v1/user/profile")
        self.assertEqual(seen[0][1], "GET")
        self.assertEqual(seen[0][2], "Bearer fake-token")
        self.assertNotIn("fake-token", out.getvalue())
        self.assertNotIn("PRIVATE", out.getvalue())

    def test_delayed_quote_path(self):
        paths = []
        def fake(request, timeout):
            paths.append(request.full_url)
            if "/user/profile" in request.full_url:
                return MockResponse(b'{"profile":{"account":[]}}')
            return MockResponse(b'{"quotes":{"quote":{"symbol":"SPY","last":500}}}')
        out = io.StringIO()
        with redirect_stdout(out):
            mod.check("fake", "SPY", opener=fake)
        self.assertTrue(paths[1].startswith("https://sandbox.tradier.com/v1/markets/quotes?"))
        self.assertIn("delayed", out.getvalue().lower())

    def test_orders_not_allowed(self):
        with self.assertRaises(ValueError):
            mod.fetch_json("/accounts/123/orders", "secret")

    def test_http_auth_failure_is_sanitized(self):
        err = HTTPError("https://sandbox.tradier.com/v1/user/profile", 401,
                        "private-token-should-not-appear", {}, None)
        output = io.StringIO()
        with patch.dict(mod.os.environ, {"TRADIER_SANDBOX_TOKEN": "private-token-should-not-appear"}):
            with patch.object(mod, "check", side_effect=err):
                with redirect_stderr(output):
                    result = mod.main()
        self.assertEqual(result, 1)
        self.assertIn("profile returned HTTP 401", output.getvalue())
        self.assertNotIn("private-token-should-not-appear", output.getvalue())

if __name__ == "__main__":
    unittest.main()
