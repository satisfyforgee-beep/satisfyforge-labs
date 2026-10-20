"""Tradier SANDBOX-only paper OTOCO order preview and strongly gated execution.

No production URL, no option/short trades, no public web server, no trade AI.
One whole-share paper OTOCO (limit entry, linked profit and stop exits) per
account/day maximum. An HTTP 200 is NOT a confirmed fill. Sandbox quotes are
delayed 15 minutes: never promote this data to live-execution signals.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_UP, InvalidOperation
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import re

from .journal import OrderJournal

SANDBOX_HOST = "https://sandbox.tradier.com/v1"
SANDBOX_ENV = "TRADIER_SANDBOX_TOKEN"
SUBMIT_GATE = "SF_TRADIER_PAPER_ENABLE"
SUBMIT_VALUE = "SANDBOX_ONLY_APPROVED"
_ACCOUNT = re.compile(r"VA[A-Z0-9]{5,18}$")
_SYMBOL = re.compile(r"[A-Z]{1,5}$")
_ID = re.compile(r"[0-9]{1,18}$")
_STATES = {
    "pending", "open", "partially_filled", "filled", "rejected",
    "expired", "canceled", "pending_cancel", "error",
}
_ET = ZoneInfo("America/New_York")


class PaperBlocked(RuntimeError):
    """A requested simulated trade is denied; no submission has happened."""


class BrokerUncertain(RuntimeError):
    """Broker state cannot be reliably established. Do not retry automatically."""


def _money(value):
    try:
        v = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise PaperBlocked("invalid paper price") from None
    if not v.is_finite() or v <= 0:
        raise PaperBlocked("invalid paper price")
    return v.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def _account_id(value):
    if not isinstance(value, str) or not _ACCOUNT.fullmatch(value):
        raise PaperBlocked("unrecognized sandbox account identifier")
    return value


def _items(data, group, singular):
    if not isinstance(data, dict) or group not in data:
        raise BrokerUncertain("broker response has no " + group + " field")
    section = data[group]
    if section is None:
        return []
    if not isinstance(section, dict) or singular not in section:
        raise BrokerUncertain("invalid broker " + group + " data")
    rows = section[singular]
    if rows is None:
        return []
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or any(not isinstance(x, dict) for x in rows):
        raise BrokerUncertain("malformed broker " + group + " records")
    return rows


def _choose_account(data, expected=None):
    if not isinstance(data, dict) or not isinstance(data.get("profile"), dict):
        raise BrokerUncertain("sandbox user profile missing")
    p = data["profile"]
    raw = p.get("account")
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise BrokerUncertain("sandbox account list absent")
    accounts = []
    for item in raw:
        if not isinstance(item, dict):
            raise BrokerUncertain("malformed sandbox account entry")
        ident = item.get("account_number") or item.get("number")
        accounts.append(_account_id(ident))
    if expected:
        requested = _account_id(expected)
        if requested not in accounts:
            raise PaperBlocked("selected sandbox account is not in profile")
        return requested
    if len(accounts) != 1:
        raise PaperBlocked("select exactly one sandbox account via local configuration")
    return accounts[0]


def build_paper_otoco(symbol, entry_limit, *, quantity=1, tag=None):
    """Single atomic paper bracket: 1-share buy, linked limit/stop sell exits."""
    if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol):
        raise PaperBlocked("only simple US equity symbols supported")
    if type(quantity) is not int or quantity != 1:
        raise PaperBlocked("paper trial restricted to exactly one whole share")
    entry = _money(entry_limit)
    if not Decimal("1") <= entry <= Decimal("20"):
        raise PaperBlocked("paper notional exceeds $20 or entry is too low")
    stop = (entry * Decimal("0.98")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    target = (entry * Decimal("1.035")).quantize(Decimal("0.01"), rounding=ROUND_UP)
    if not Decimal("0") < stop < entry < target:
        raise PaperBlocked("invalid paper protective exit geometry")
    if tag is None or not re.fullmatch(r"sfpaper[0-9a-f]{16}", tag):
        raise PaperBlocked("missing deterministic paper-only order tag")
    return {
        "class": "otoco", "duration": "day", "tag": tag,
        "symbol[0]": symbol, "side[0]": "buy", "quantity[0]": "1",
        "type[0]": "limit", "price[0]": str(entry),
        "symbol[1]": symbol, "side[1]": "sell", "quantity[1]": "1",
        "type[1]": "limit", "price[1]": str(target),
        "symbol[2]": symbol, "side[2]": "sell", "quantity[2]": "1",
        "type[2]": "stop", "stop[2]": str(stop),
    }


def _tag(account_id, today, symbol):
    raw = "satisfyforge-sandbox|" + account_id + "|" + today.isoformat() + "|" + symbol
    return "sfpaper" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_preview(response):
    if not isinstance(response, dict) or not isinstance(response.get("order"), dict):
        raise PaperBlocked("sandbox preview did not return an order")
    order = response["order"]
    if order.get("result") is not True or order.get("status") != "ok":
        raise PaperBlocked("sandbox preview declined the request")
    if order.get("warnings") or order.get("errors") or order.get("error"):
        raise PaperBlocked("sandbox preview requires further review")
    for field in ("commission", "fees", "cost"):
        if field in order:
            value = Decimal(str(order[field]))
            if not value.is_finite():
                raise PaperBlocked("sandbox preview cost data invalid")
    return {
        "status": "PREVIEW_OK", "simulated_only": True,
        "commission_reported": str(order.get("commission", "unavailable")),
        "fees_reported": str(order.get("fees", "unavailable")),
        "warning": "Preview checked parameters but created NO broker order.",
    }


class TradierSandbox:
    """Narrow HTTP transport. Its ONLY host is Tradier's PAPER endpoint."""

    def __init__(self, token=None, transport=None):
        self._token = token if token is not None else os.environ.get(SANDBOX_ENV)
        if not self._token or not isinstance(self._token, str):
            raise PaperBlocked("sandbox token missing from local/Actions secret")
        self.transport = transport or self._http

    def _http(self, method, path, query=None, form=None):
        if not path.startswith("/") or "//" in path or "://" in path:
            raise PaperBlocked("invalid sandbox API path")
        url = SANDBOX_HOST + path
        if query:
            url += "?" + urlencode(query)
        data = urlencode(form).encode("utf-8") if form is not None else None
        headers = {
            "Accept": "application/json", "Authorization": "Bearer " + self._token,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SatisfyForge-sandbox-paper/0.5",
        }
        req = Request(url, data=data, headers=headers, method=method)
        with urlopen(req, timeout=9) as res:
            result = json.load(res)
        if not isinstance(result, dict):
            raise BrokerUncertain("unexpected sandbox response")
        return result

    def _request(self, method, path, query=None, form=None, paper_armed=False):
        readonly = path == "/user/profile" or path == "/markets/quotes"
        readonly = readonly or bool(re.fullmatch(
            r"/accounts/VA[A-Z0-9]{5,18}/(?:balances|positions|orders(?:/[0-9]{1,18})?)", path
        ))
        order_path = bool(re.fullmatch(r"/accounts/VA[A-Z0-9]{5,18}/orders", path))
        if method == "GET":
            if not readonly or form is not None:
                raise PaperBlocked("not a sanctioned sandbox GET endpoint")
        elif method == "POST":
            if not order_path or not isinstance(form, dict):
                raise PaperBlocked("only the sandbox order endpoint supports POST")
            # Revalidate complete form locally: no shorting, options, arbitrary
            # quantities, new symbols or independent exit legs.
            try:
                qty = int(form.get("quantity[0]", 0))
            except (ValueError, TypeError):
                raise PaperBlocked("invalid sandbox order quantity") from None
            check = build_paper_otoco(
                form.get("symbol[0]"), form.get("price[0]"),
                quantity=qty,
                tag=form.get("tag"),
            )
            for field in ("preview",):
                form = dict(form)
                form.pop(field, None)
            if form != check:
                raise PaperBlocked("paper order payload differs from vetted OTOCO")
            if not paper_armed:
                form["preview"] = "true"
            elif os.environ.get(SUBMIT_GATE) != SUBMIT_VALUE:
                raise PaperBlocked("sandbox paper submission remains DISABLED")
        else:
            raise PaperBlocked("unsupported HTTP method")
        try:
            return self.transport(method, path, query, form)
        except HTTPError as err:
            # Do not print response bodies or request URLs: may reveal secrets.
            raise BrokerUncertain("sandbox HTTP " + str(err.code)) from None
        except (URLError, TimeoutError, OSError):
            raise BrokerUncertain("sandbox network outcome uncertain") from None

    def state(self, account_selector=None):
        account = _choose_account(
            self._request("GET", "/user/profile"), expected=account_selector)
        base = "/accounts/" + account
        balance_res = self._request("GET", base + "/balances")
        balances = balance_res.get("balances")
        if not isinstance(balances, dict):
            # Tradier's documented examples occasionally use nested balance.
            balances = (balance_res.get("balance") or {}).get("balances")
        if not isinstance(balances, dict):
            raise BrokerUncertain("broker balance response missing")
        if balances.get("account_number") not in (account, None):
            raise BrokerUncertain("sandbox account balance mismatch")
        raw_cash = balances.get("total_cash")
        try:
            cash = Decimal(str(raw_cash))
        except (InvalidOperation, ValueError, TypeError):
            raise BrokerUncertain("sandbox balance missing or invalid") from None
        if not cash.is_finite() or cash < 0:
            raise BrokerUncertain("sandbox cash negative or non-finite")
        positions = _items(self._request("GET", base + "/positions"),
                           "positions", "position")
        orders = _items(self._request(
            "GET", base + "/orders", query={"limit": 1000}), "orders", "order")
        if len(orders) >= 1000:
            raise BrokerUncertain("too many sandbox orders to confirm uniqueness")
        pending = balances.get("pending_orders_count")
        if pending is None:
            raise BrokerUncertain("sandbox pending order count unavailable")
        try:
            pending = int(pending)
        except (ValueError, TypeError):
            raise BrokerUncertain("bad pending order count") from None
        if pending < 0:
            raise BrokerUncertain("bad pending order count")
        return {
            "account": account, "cash": cash,
            "positions": positions, "orders": orders, "pending": pending,
        }

    @staticmethod
    def _flat(snap, price, symbol):
        if snap["positions"] or snap["orders"] or snap["pending"]:
            raise PaperBlocked("existing sandbox order/position: reconcile first")
        if snap["cash"] < price:
            raise PaperBlocked("sandbox account lacks unleveraged cash")
        if symbol not in ("SOFI", "AAL", "F", "CLF"):
            raise PaperBlocked("paper smoke-trial symbol not on allowlist")

    def preview(self, symbol, price, *, account_selector=None, now=None):
        """POST preview=true only. This NEVER creates an order."""
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise PaperBlocked("timezone required")
        snap = self.state(account_selector)
        entry = _money(price)
        self._flat(snap, entry, symbol)
        tag = _tag(snap["account"], now.astimezone(_ET).date(), symbol)
        form = build_paper_otoco(symbol, entry, tag=tag)
        result = self._request("POST", "/accounts/" + snap["account"] + "/orders",
                               form=form, paper_armed=False)
        return dict(_normalize_preview(result), symbol=symbol,
                    entry_limit=str(entry), max_notional="20.00",
                    otoco_exits=True, source="TRADIER_SANDBOX_15_MIN_DELAYED")

    def submit_paper(self, symbol, price, journal: OrderJournal, *,
                     explicitly_armed=False, account_selector=None, now=None):
        """At most one attempted PAPER order per account/symbol/session.

        Requires explicit runtime argument AND exact env gate; submission
        intentionally requires re-reading broker state and previewing again.
        On unknown remote outcome, journal UNKNOWN and never auto retry.
        """
        if not explicitly_armed or os.environ.get(SUBMIT_GATE) != SUBMIT_VALUE:
            raise PaperBlocked("sandbox paper submission gate is OFF")
        if not isinstance(journal, OrderJournal):
            raise PaperBlocked("durable local journal required")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise PaperBlocked("timezone required")
        et = now.astimezone(_ET)
        if et.weekday() >= 5 or not (9 * 60 + 35 <= et.hour * 60 + et.minute < 14 * 60 + 45):
            raise PaperBlocked("outside approved regular-market paper entry window")
        snap = self.state(account_selector)
        entry = _money(price)
        self._flat(snap, entry, symbol)
        tag = _tag(snap["account"], et.date(), symbol)
        form = build_paper_otoco(symbol, entry, tag=tag)
        preview = self._request("POST", "/accounts/" + snap["account"] + "/orders",
                                form=form, paper_armed=False)
        _normalize_preview(preview)
        # Fresh broker readback after preview (no stale preflight).
        next_state = self.state(snap["account"])
        self._flat(next_state, entry, symbol)
        if next_state["cash"] < entry:
            raise PaperBlocked("paper cash changed after preview")
        midnight = et.replace(hour=0, minute=0, second=0, microsecond=0)
        # ONE order per SANDBOX ACCOUNT per session, even across symbols.
        # The account is hashed before use in the journal's strategy name.
        account_hash = hashlib.sha256(snap["account"].encode()).hexdigest()[:12]
        new, key = journal.reserve("tradier-sandbox-otoco-" + account_hash,
                                   "DAILY", midnight)
        if not new:
            raise PaperBlocked("duplicate paper order intent blocked by journal")
        try:
            result = self._request(
                "POST", "/accounts/" + snap["account"] + "/orders",
                form=form, paper_armed=True)
        except Exception as exc:
            journal.transition(key, "unknown")
            raise BrokerUncertain(
                "sandbox submit result uncertain; manually reconcile broker"
            ) from None
        raw = result.get("order") if isinstance(result, dict) else None
        if (not isinstance(raw, dict) or raw.get("status") != "ok"
                or type(raw.get("id")) is not int or raw["id"] < 1):
            journal.transition(key, "unknown")
            raise BrokerUncertain(
                "sandbox response not a confirmed broker order; reconcile first")
        journal.transition(key, "submitted", broker_order_id=str(raw["id"]))
        return {
            "status": "SUBMITTED_TO_SANDBOX_NOT_A_FILL",
            "paper_only": True, "symbol": symbol,
            "limit_price": str(entry), "protective_exits_requested": True,
            "warning": "Broker must confirm the fill and OTOCO child legs.",
            "journal_key": key,
        }

    def order_readback(self, order_id, *, account_selector=None):
        """Read-only order reconciliation; status is never assumed filled."""
        if isinstance(order_id, bool) or not _ID.fullmatch(str(order_id)):
            raise PaperBlocked("invalid paper order identifier")
        snap = self.state(account_selector)
        response = self._request(
            "GET", "/accounts/" + snap["account"] + "/orders/" + str(order_id),
        )
        order = response.get("order")
        if not isinstance(order, dict) or str(order.get("id")) != str(order_id):
            raise BrokerUncertain("broker could not confirm specific sandbox order")
        status = order.get("status")
        if status not in _STATES:
            raise BrokerUncertain("unknown sandbox order status")
        filled = order.get("exec_quantity")
        qty = order.get("quantity")
        try:
            filled, qty = Decimal(str(filled)), Decimal(str(qty))
        except (InvalidOperation, TypeError, ValueError):
            raise BrokerUncertain("missing fill quantity") from None
        if not (filled.is_finite() and qty.is_finite()
                and Decimal(0) <= filled <= qty and qty > 0):
            raise BrokerUncertain("invalid sandbox fill quantities")
        return {
            "status": status, "filled_qty": str(filled),
            "requested_qty": str(qty), "paper_only": True,
            "is_fill_confirmed": status == "filled" and filled == qty,
            "needs_reconciliation": status in (
                "partially_filled", "error", "pending_cancel"
            ),
            "warning": "Child-exit status must be independently verified.",
        }
