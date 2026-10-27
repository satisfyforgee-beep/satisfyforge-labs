#!/usr/bin/env python3
"""SatisfyForge read-only Tradier sandbox / Alpaca paper connectivity check.

No brokerage order API, POST request, polling loop, persistent process, or
live-account base URL is used. No credentials, account identifiers, balances,
HTTP response bodies, or exception URLs are included in output.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from zerocost_bot.alpaca import latest_equity_quotes


TRADIER_SANDBOX_PROFILE = "https://sandbox.tradier.com/v1/user/profile"
ALPACA_PAPER_ACCOUNT = "https://paper-api.alpaca.markets/v2/account"
KEYCHAIN_ITEMS = {
    "TRADIER_SANDBOX_TOKEN": "com.satisfyforge.tradier.sandbox",
    "ALPACA_PAPER_KEY": "com.satisfyforge.alpaca.paper.key",
    "ALPACA_PAPER_SECRET": "com.satisfyforge.alpaca.paper.secret",
}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Authenticated requests must never be forwarded to another host.
        return None


_SAFE_HTTP = build_opener(_NoRedirect)


def _keychain_secret(service: str) -> str | None:
    """Read only an exact named Keychain entry into memory; never print it."""
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-a", "satisfyforge", "-s", service, "-w"],
            capture_output=True, check=False, timeout=5, text=True,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def load_credentials(*, allow_keychain: bool = False) -> dict[str, str | None]:
    """Prefer already configured environment; Keychain is explicit opt-in."""
    out: dict[str, str | None] = {}
    for variable, service in KEYCHAIN_ITEMS.items():
        out[variable] = os.getenv(variable) or (_keychain_secret(service) if allow_keychain else None)
    return out


def _get_json(request: Request, transport=None) -> dict:
    if request.get_method() != "GET":
        raise ValueError("Only read-only GET is permitted")
    if request.full_url not in {TRADIER_SANDBOX_PROFILE, ALPACA_PAPER_ACCOUNT}:
        raise ValueError("Endpoint is not on the read-only allowlist")
    if transport is not None:
        return transport(request)
    with _SAFE_HTTP.open(request, timeout=8) as response:
        return json.load(response)


def _quote_json(request: Request, transport=None) -> dict:
    parsed = urlsplit(request.full_url)
    if (request.get_method() != "GET" or parsed.scheme != "https"
            or parsed.netloc != "data.alpaca.markets"
            or parsed.path != "/v2/stocks/quotes/latest"
            or parse_qs(parsed.query) != {"symbols": ["SOFI"], "feed": ["iex"]}):
        raise ValueError("Quote request is outside the IEX read-only allowlist")
    if transport is not None:
        return transport(request)
    with _SAFE_HTTP.open(request, timeout=8) as response:
        return json.load(response)


def _safe_check(request: Request, transport=None) -> str:
    """Sanitized status only; untrusted API errors never reach stdout."""
    try:
        body = _get_json(request, transport)
        if not isinstance(body, dict):
            return "INVALID_RESPONSE"
        if request.full_url == TRADIER_SANDBOX_PROFILE:
            return "CONNECTED" if isinstance(body.get("profile"), dict) else "INVALID_RESPONSE"
        return "CONNECTED" if "status" in body and "id" in body else "INVALID_RESPONSE"
    except HTTPError as exc:
        return "AUTH_FAILED" if exc.code in {401, 403} else "HTTP_ERROR"
    except (URLError, TimeoutError, OSError):
        return "NETWORK_ERROR"
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return "INVALID_RESPONSE"


def check_connections(*, network: bool = False, allow_keychain: bool = False,
                      transport=None) -> dict:
    credentials = load_credentials(allow_keychain=allow_keychain)
    tradier = credentials["TRADIER_SANDBOX_TOKEN"]
    alpaca_key = credentials["ALPACA_PAPER_KEY"]
    alpaca_secret = credentials["ALPACA_PAPER_SECRET"]
    states = {
        "tradier_sandbox": "READY" if tradier else "MISSING_CREDENTIAL",
        "alpaca_paper": "READY" if alpaca_key and alpaca_secret else
                        ("INCOMPLETE_CREDENTIAL_PAIR" if alpaca_key or alpaca_secret else "MISSING_CREDENTIAL"),
        "alpaca_iex_quotes": "NOT_CHECKED",
    }
    if network:
        if tradier:
            request = Request(TRADIER_SANDBOX_PROFILE, headers={
                "Authorization": f"Bearer {tradier}", "Accept": "application/json"}, method="GET")
            states["tradier_sandbox"] = _safe_check(request, transport)
        if alpaca_key and alpaca_secret:
            headers = {"APCA-API-KEY-ID": alpaca_key, "APCA-API-SECRET-KEY": alpaca_secret,
                       "Accept": "application/json"}
            request = Request(ALPACA_PAPER_ACCOUNT, headers=headers, method="GET")
            states["alpaca_paper"] = _safe_check(request, transport)
            if states["alpaca_paper"] == "CONNECTED":
                # This helper has one hardcoded read-only IEX quote GET. The
                # response is never returned, printed, or used to make an order.
                try:
                    quotes = latest_equity_quotes(
                        ["SOFI"], alpaca_key, alpaca_secret,
                        lambda request: _quote_json(request, transport))
                    states["alpaca_iex_quotes"] = "CONNECTED" if quotes else "NO_QUOTE_RETURNED"
                except HTTPError as exc:
                    states["alpaca_iex_quotes"] = "AUTH_FAILED" if exc.code in {401, 403} else "HTTP_ERROR"
                except (URLError, TimeoutError, OSError):
                    states["alpaca_iex_quotes"] = "NETWORK_ERROR"
                except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                    states["alpaca_iex_quotes"] = "INVALID_RESPONSE"

    return {
        "mode": "READ_ONLY_PAPER_DATA_PREFLIGHT",
        "network_attempted": bool(network),
        "keychain_opted_in": bool(allow_keychain),
        "broker_order_submission_enabled": False,
        "live_money_enabled": False,
        "always_on_monitoring_enabled": False,
        "tradier_prices_delayed_minutes": 15,
        "alpaca_equity_feed": "IEX_ONLY_NOT_CONSOLIDATED",
        "connections": states,
        "secrets_and_account_numbers_displayed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check sandbox/paper data readiness without trading")
    parser.add_argument("--network", action="store_true", help="Opt in to fixed read-only HTTPS GET checks")
    parser.add_argument("--keychain", action="store_true", help="Opt in to three exact named macOS Keychain entries")
    args = parser.parse_args()
    print(json.dumps(check_connections(network=args.network, allow_keychain=args.keychain), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
