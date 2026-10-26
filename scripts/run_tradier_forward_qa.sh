#!/bin/zsh
# Owner-controlled, read-only Tradier SANDBOX delayed-quote virtual book.
# Never passes a secret as a command-line argument or writes broker orders.
set -eu
umask 077
cd "${0:A:h}/.."
# Skip Keychain and network outside the regular NY market session.
if ! /usr/bin/python3 -c 'from datetime import datetime; from zoneinfo import ZoneInfo; n=datetime.now(ZoneInfo("America/New_York")); m=n.hour*60+n.minute; raise SystemExit(0 if n.weekday()<5 and 9*60+35<=m<16*60 else 1)'; then
  print -r -- '{"state":"OUTSIDE_PAPER_SESSION","broker_orders_sent":0}'
  exit 0
fi
# Secret stays in macOS Keychain; no plaintext token files.
KEY="$(/usr/bin/security find-generic-password -a "$(/usr/bin/id -un)" -s satisfyforge-tradier-sandbox -w 2>/dev/null || true)"
if [[ -z "$KEY" ]]; then
  print -r -- '{"state":"HALT_KEYCHAIN_UNAVAILABLE","broker_orders_sent":0}'
  exit 2
fi
export TRADIER_SANDBOX_TOKEN="$KEY"
unset KEY
exec /usr/bin/python3 scripts/tradier_forward_qa.py
