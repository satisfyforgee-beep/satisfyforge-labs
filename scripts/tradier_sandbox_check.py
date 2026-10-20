#!/usr/bin/env python3
"""Read-only Tradier sandbox check. Intentionally cannot submit trades."""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://sandbox.tradier.com/v1"

def fetch_json(path, token, params=None, opener=urlopen):
    """Only two paper-only GET routes are allowed."""
    if path not in ("/user/profile", "/markets/quotes"):
        raise ValueError("Route is not on the read-only allowlist")
    query = ("?" + urlencode(params)) if params else ""
    request = Request(BASE_URL + path + query, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
    }, method="GET")
    with opener(request, timeout=12) as response:
        return json.load(response)

def check(token, symbol=None, opener=urlopen):
    profile = fetch_json("/user/profile", token, opener=opener).get("profile") or {}
    accounts = profile.get("account") or []
    if isinstance(accounts, dict):
        accounts = [accounts]
    print("Tradier SANDBOX authentication: OK")
    print(f"Paper accounts visible: {len(accounts)}")
    print("No orders submitted; no live API called.")
    if symbol:
        data = fetch_json("/markets/quotes", token,
                          params={"symbols": symbol, "greeks": "false"}, opener=opener)
        quote = (data.get("quotes") or {}).get("quote")
        if isinstance(quote, list):
            quote = quote[0] if quote else None
        if quote:
            print(f"{symbol} sandbox delayed quote: {quote.get('last', 'unavailable')}")
        else:
            print(f"{symbol} sandbox quote unavailable")
        print("Note: sandbox market data is delayed about 15 minutes and unsuitable for live orders.")

def main():
    parser = argparse.ArgumentParser(description="Tradier read-only sandbox smoke test")
    parser.add_argument("--symbol", help="Optional quote symbol (letters, 1-6 chars)")
    args = parser.parse_args()
    token = os.environ.get("TRADIER_SANDBOX_TOKEN", "").strip()
    if not token:
        print("Missing TRADIER_SANDBOX_TOKEN environment variable (do not paste key into code).", file=sys.stderr)
        return 2
    symbol = args.symbol.upper() if args.symbol else None
    if symbol and (not symbol.isalpha() or len(symbol) > 6):
        parser.error("--symbol must have 1-6 letters")
    try:
        check(token, symbol)
    except HTTPError as exc:
        # Never print provider response bodies, full URLs, tokens or private account data.
        route = str(getattr(exc, "url", "")).split("?")[0]
        stage = "profile" if route == BASE_URL + "/user/profile" else "quote" if route == BASE_URL + "/markets/quotes" else "request"
        print(f"Tradier sandbox {stage} returned HTTP {exc.code}; no orders submitted.", file=sys.stderr)
        return 1
    except (URLError, ValueError, TimeoutError, json.JSONDecodeError):
        print("Sandbox check failed (network or response format); no orders submitted.", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
