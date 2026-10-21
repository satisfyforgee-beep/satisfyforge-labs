"""Tradier paper-only, trigger-driven options entry with broker-managed OTOCO exits.

Security boundaries: hard-coded sandbox host; no external URL or real-account routing;
no order POST unless three independent arming gates all pass. No POST retries.
Stdlib only so the prototype can be tested without extra subscriptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo
import json
import os
import re
import sqlite3
import time

SANDBOX_HOST = "https://sandbox.tradier.com/v1"
ARM_TOKEN = "SANDBOX_OPTIONS_ONLY_I_APPROVE"
NY = ZoneInfo("America/New_York")
OPTION_RE = re.compile(r"^([A-Z]{1,6})(\d{6})([CP])(\d{8})$")
SYMBOL_RE = re.compile(r"^[A-Z]{1,6}$")
MAX_TOTAL_PREMIUM = Decimal("60.00")
MAX_DAILY_LOSS = Decimal("10.00")
LIVE_QUOTES_AVAILABLE = False  # sandbox snapshots are delayed ~15 minutes


class Halt(Exception):
    """Fail-closed refusal; no new orders."""


def dec(value, name="number") -> Decimal:
    try:
        x = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise Halt(f"invalid {name}") from exc
    if not x.is_finite():
        raise Halt(f"non-finite {name}")
    return x


def one_or_many(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


@dataclass(frozen=True)
class Plan:
    underlying: str
    option_symbol: str
    direction: str  # down = long put; up = long call
    underlying_trigger: Decimal
    quantity: int
    entry_limit: Decimal
    profit_limit: Decimal
    stop_trigger: Decimal
    max_spread: Decimal = Decimal("0.03")
    max_cost: Decimal = MAX_TOTAL_PREMIUM
    min_underlying_volume: int = 100000
    enabled: bool = False

    @classmethod
    def from_dict(cls, data):
        required = ["underlying", "option_symbol", "direction", "underlying_trigger",
                    "quantity", "entry_limit", "profit_limit", "stop_trigger"]
        if not isinstance(data, dict) or any(k not in data for k in required):
            raise Halt("incomplete strategy configuration")
        try:
            plan = cls(
                underlying=str(data["underlying"]).upper(),
                option_symbol=str(data["option_symbol"]).upper(),
                direction=str(data["direction"]),
                underlying_trigger=dec(data["underlying_trigger"], "trigger"),
                quantity=int(data["quantity"]),
                entry_limit=dec(data["entry_limit"], "entry limit"),
                profit_limit=dec(data["profit_limit"], "profit limit"),
                stop_trigger=dec(data["stop_trigger"], "stop trigger"),
                max_spread=dec(data.get("max_spread", "0.03"), "spread"),
                max_cost=dec(data.get("max_cost", "60"), "budget"),
                min_underlying_volume=int(data.get("min_underlying_volume", 100000)),
                enabled=data.get("enabled", False),
            )
        except (ValueError, TypeError) as exc:
            raise Halt("bad strategy field") from exc
        plan.validate()
        return plan

    def validate(self):
        if not SYMBOL_RE.fullmatch(self.underlying):
            raise Halt("invalid underlying")
        m = OPTION_RE.fullmatch(self.option_symbol)
        if not m or m.group(1) != self.underlying:
            raise Halt("option OCC symbol must match underlying")
        if self.direction not in {"up", "down"} or (self.direction == "up") != (m.group(3) == "C"):
            raise Halt("direction and option type mismatch")
        try:
            expiry = datetime.strptime(m.group(2), "%y%m%d").date()
        except ValueError as exc:
            raise Halt("invalid OCC expiration") from exc
        if expiry < datetime.now(NY).date():
            raise Halt("expired option")
        if self.enabled is not True and self.enabled is not False:
            raise Halt("enabled must be boolean")
        if self.quantity < 1 or self.quantity > 10 or self.min_underlying_volume < 0:
            raise Halt("invalid quantity or minimum volume")
        if not 0 < self.max_cost <= MAX_TOTAL_PREMIUM:
            raise Halt("budget exceeds hard $60 ceiling")
        if not (Decimal("0.01") <= self.entry_limit < self.profit_limit <= Decimal("20.00")):
            raise Halt("take-profit must exceed entry limit")
        if not (Decimal("0.01") <= self.stop_trigger < self.entry_limit):
            raise Halt("stop trigger must be below entry limit")
        if not (Decimal("0.00") < self.max_spread <= Decimal("0.05")):
            raise Halt("option spread over allowed maximum")
        if self.underlying_trigger <= 0 or self.entry_limit * 100 * self.quantity > self.max_cost:
            raise Halt("estimated premium exceeds plan budget")
        # Refuse nonsense prices if input was silently rounded.
        for x in (self.entry_limit, self.profit_limit, self.stop_trigger):
            if x != x.quantize(Decimal("0.01")):
                raise Halt("option prices must be in whole cents")

    def key(self, session_date):
        attrs = (self.option_symbol, self.direction, str(self.underlying_trigger),
                 self.quantity, str(self.entry_limit), str(self.profit_limit), str(self.stop_trigger))
        digest = sha256(repr(attrs).encode()).hexdigest()[:12]
        return f"SFPA-{session_date:%Y%m%d}-{digest}"

    def order(self, tag):
        # Tradier OTOCO entry + OCO exits; NOT a single naked options entry.
        # Children are conditional on the entry filling, per Tradier API docs.
        qty = str(self.quantity)
        common = {"class": "otoco", "duration": "day", "tag": tag}
        for idx, side, type_ in ((0, "buy_to_open", "limit"),
                                  (1, "sell_to_close", "limit"),
                                  (2, "sell_to_close", "stop")):
            common[f"symbol[{idx}]"] = self.underlying
            common[f"option_symbol[{idx}]"] = self.option_symbol
            common[f"quantity[{idx}]"] = qty
            common[f"side[{idx}]"] = side
            common[f"type[{idx}]"] = type_
        common["price[0]"] = str(self.entry_limit)
        common["price[1]"] = str(self.profit_limit)
        common["stop[2]"] = str(self.stop_trigger)
        return common


class TradierSandbox:
    """Network adapter always pinned to official sandbox host; never production."""
    def __init__(self, token=None, account=None, transport=None):
        self.token = token if token is not None else os.environ.get("TRADIER_SANDBOX_TOKEN", "")
        self.account = account if account is not None else os.environ.get("TRADIER_SANDBOX_ACCOUNT", "")
        if not self.token or not self.account or not re.fullmatch(r"[A-Za-z0-9_-]{3,40}", self.account):
            raise Halt("sandbox token and account ID must be configured locally")
        self._transport = transport or self._http

    def _http(self, method, path, params):
        if method not in {"GET", "POST"} or not re.fullmatch(r"/(?:markets/quotes|user/profile|accounts/[A-Za-z0-9_-]+/(?:balances|positions|orders(?:/[0-9]+)?))", path):
            raise Halt("unsupported sandbox API endpoint")
        if method == "POST" and path != f"/accounts/{self.account}/orders":
            raise Halt("only sandbox order preview/placement can POST")
        if "/accounts/" in path and f"/accounts/{self.account}/" not in path:
            raise Halt("cross-account request refused")
        uri = SANDBOX_HOST + path
        headers = {"Authorization": "Bearer " + self.token, "Accept": "application/json"}
        payload = None
        if method == "GET":
            if params:
                uri += "?" + urlencode(params)
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            payload = urlencode(params).encode("utf-8")
        request = Request(uri, data=payload, headers=headers, method=method)
        try:
            with urlopen(request, timeout=8) as response:
                result = json.load(response)
        except (URLError, HTTPError, TimeoutError, ValueError) as exc:
            # No token/account IDs or response bodies are copied into logs.
            raise Halt("sandbox request failed; order state may be uncertain") from exc
        if not isinstance(result, dict):
            raise Halt("unexpected sandbox response")
        if result.get("errors") or result.get("error"):
            raise Halt("Tradier sandbox reported an API error")
        return result

    def call(self, method, path, params=None):
        return self._transport(method, path, params or {})

    def snapshot(self, symbols):
        acc = self.account
        raw = {
            "profile": self.call("GET", "/user/profile"),
            "balances": self.call("GET", f"/accounts/{acc}/balances"),
            "positions": self.call("GET", f"/accounts/{acc}/positions"),
            "orders": self.call("GET", f"/accounts/{acc}/orders", {"includeTags": "true", "limit": "1000"}),
            "quotes": self.call("GET", "/markets/quotes", {"symbols": ",".join(symbols)}),
        }
        if any(not isinstance(v, dict) for v in raw.values()):
            raise Halt("malformed sandbox account snapshot")
        return raw

    def preview(self, form):
        return self.call("POST", f"/accounts/{self.account}/orders", {**form, "preview": "true"})

    def place_paper(self, form, explicitly_armed=False):
        # Defense-in-depth: two independent gates required at adapter boundary.
        if not explicitly_armed or os.environ.get("SF_TRADIER_PAPER_ORDER_ENABLE") != ARM_TOKEN:
            raise Halt("sandbox order POST disarmed")
        if form.get("class") != "otoco" or not str(form.get("tag","")).startswith("SFPA-"):
            raise Halt("only tagged protective OTOCO paper orders are permitted")
        return self.call("POST", f"/accounts/{self.account}/orders", {**form, "preview": "false"})


class Journal:
    """SQLite makes simultaneous attempts to use the same strategy tag mutually exclusive."""
    def __init__(self, path):
        db = Path(path)
        db.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db), timeout=4, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS attempts
            (tag TEXT PRIMARY KEY, stage TEXT NOT NULL, order_id TEXT,
             created_at TEXT NOT NULL, last_error TEXT NOT NULL DEFAULT '')""")

    def read(self, tag):
        row = self.db.execute("SELECT stage,order_id FROM attempts WHERE tag=?", (tag,)).fetchone()
        return row

    def reserve(self, tag, now):
        cur = self.db.execute("INSERT OR IGNORE INTO attempts(tag,stage,created_at) VALUES(?,?,?)",
                              (tag, "intent", now.isoformat()))
        return cur.rowcount == 1

    def status(self, tag, stage, order_id=None, message=""):
        self.db.execute("UPDATE attempts SET stage=?,order_id=?,last_error=? WHERE tag=?",
                        (stage, order_id, message[:200], tag))

    def session_count(self, date_str):
        return self.db.execute("SELECT count(*) FROM attempts WHERE created_at LIKE ?",
                               (date_str + "%",)).fetchone()[0]


class Runner:
    def __init__(self, api, journal, plan, paper_submit=False, clock=None):
        self.api, self.journal, self.plan = api, journal, plan
        self.paper_submit = paper_submit
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def gate(self):
        # Separate CLI, environment, and config gates are intentionally mandatory.
        return (self.paper_submit and os.environ.get("SF_TRADIER_PAPER_ORDER_ENABLE") == ARM_TOKEN
                and self.plan.enabled is True)

    def run_once(self):
        now = self.clock()
        if now.tzinfo is None:
            raise Halt("clock lacks timezone")
        local = now.astimezone(NY)
        day = local.date()
        tag = self.plan.key(day)
        past = self.journal.read(tag)
        if past:
            return self.reconcile(tag, past)
        if local.weekday() >= 5 or not ((local.hour,local.minute) >= (9,35) and (local.hour,local.minute) < (15,0)):
            return {"action": "blocked", "reason": "outside approved entry session", "sandbox": True}

        raw = self.api.snapshot([self.plan.underlying, self.plan.option_symbol])
        self.check_account(raw, tag, local)
        u, o = self.quotes(raw, now)
        last = dec(u.get("last"), "underlying last")
        triggered = last >= self.plan.underlying_trigger if self.plan.direction == "up" else last <= self.plan.underlying_trigger
        if not triggered:
            return {"action":"watch", "reason":"price trigger not met", "underlying_price":str(last), "sandbox_delayed":True}
        bid = dec(o.get("bid"), "option bid")
        ask = dec(o.get("ask"), "option ask")
        if ask > self.plan.entry_limit:
            return {"action":"watch", "reason":"option ask above limit", "option_ask":str(ask), "sandbox_delayed":True}
        if bid <= 0 or ask < bid or ask - bid > self.plan.max_spread:
            return {"action":"blocked", "reason":"option spread too wide or invalid", "sandbox_delayed":True}
        form = self.plan.order(tag)
        if not self.gate():
            return {"action":"paper_proposal_only", "underlying_price":str(last),
                    "option_bid":str(bid), "option_ask":str(ask),
                    "estimated_premium":str(self.plan.entry_limit * self.plan.quantity * 100),
                    "entry_limit":str(self.plan.entry_limit), "profit_limit":str(self.plan.profit_limit),
                    "stop_trigger":str(self.plan.stop_trigger), "sandbox_delayed":True,
                    "note":"No broker order or preview POST was sent"}
        preview = self.api.preview(form)
        p = preview.get("order")
        if not isinstance(p, dict) or p.get("result") is not True or p.get("status") != "ok":
            raise Halt("broker preview rejected OTOCO; no unprotected fallback")
        fees = dec(p.get("fees", 0), "preview fees") + dec(p.get("commission", 0), "preview commission")
        # Broker preview cost is often positive for debit; explicitly fail if inflated/unknown.
        predicted = self.plan.entry_limit * self.plan.quantity * 100 + fees
        broker_cost = dec(p.get("cost"), "preview cost")
        if predicted > self.plan.max_cost or abs(broker_cost) > self.plan.max_cost:
            raise Halt("preview cost incl. fees exceeds max budget")
        if not self.journal.reserve(tag, now):
            return {"action":"blocked", "reason":"duplicate strategy intent", "sandbox":True}
        try:
            response = self.api.place_paper(form, explicitly_armed=True)
            order = response.get("order")
            if not isinstance(order, dict) or not order.get("id") or str(order.get("status","")).lower() not in {"ok","open","pending","filled"}:
                raise Halt("ambiguous sandbox order acknowledgement")
            self.journal.status(tag,"submitted",str(order["id"]))
            return {"action":"submitted_to_sandbox", "order_id":str(order["id"]),
                    "broker_acknowledgement":order.get("status"), "filled":False,
                    "estimated_total_cost":str(predicted),"sandbox_delayed":True}
        except Exception:
            self.journal.status(tag, "uncertain", message="Check Tradier paper orders by tag; never retry POST")
            raise Halt("paper order acknowledgement uncertain; do not resubmit, inspect broker tag") from None

    def reconcile(self, tag, past):
        """Read-only post-submit recovery; never attempt a second POST."""
        stage, saved_id = past
        orders = self.api.call("GET", f"/accounts/{self.api.account}/orders",
                               {"includeTags":"true", "limit":"1000"})
        if not isinstance(orders, dict):
            raise Halt("order reconciliation response malformed")
        order_container=orders.get("orders") or {}
        if not isinstance(order_container,dict):
            raise Halt("order reconciliation payload malformed")
        listed = one_or_many(order_container.get("order"))
        matches = [o for o in listed if isinstance(o,dict) and
                   (o.get("tag") == tag or (saved_id and str(o.get("id")) == saved_id))]
        if saved_id:
            try:
                detail=self.api.call("GET",f"/accounts/{self.api.account}/orders/{saved_id}")
                single=detail.get("order")
                if isinstance(single,dict) and not any(str(o.get("id"))==saved_id for o in matches):
                    matches.insert(0,single)
            except Exception:
                # Keep existing state. A failed read is not permission to resubmit.
                pass
        if not matches:
            return {"action":"needs_manual_reconciliation", "stage":stage,
                    "reason":"broker tag not found; no automatic resubmission", "sandbox":True}
        statuses=sorted({str(o.get("status","unknown")) for o in matches})
        new_id=next((str(o["id"]) for o in matches if o.get("id")), saved_id)
        self.journal.status(tag,"reconciled",new_id)
        return {"action":"broker_order_status", "statuses":statuses,
                "order_id":new_id,"sandbox":True,
                "note":"An order acknowledgement is not a fill; broker status may change"}

    def check_account(self, raw, tag, now):
        accounts = one_or_many(raw["profile"].get("profile", {}).get("account"))
        mine = [x for x in accounts if str(x.get("account_number")) == self.api.account]
        if len(mine) != 1 or str(mine[0].get("status","active")).lower() != "active" or int(mine[0].get("option_level") or 0) < 2:
            raise Halt("sandbox option account missing or not approved")
        balances = raw["balances"].get("balances",raw["balances"].get("balance"))
        if not isinstance(balances,dict):
            raise Halt("missing broker balances")
        cash = dec(balances.get("total_cash"),"cash")
        option_bp = dec(balances.get("option_buying_power"),"option buying power")
        close_pl = dec(balances.get("close_pl"),"realized daily PL")
        # Entire order debit incl. fees checked again after preview. This is a coarse preflight.
        if min(cash, option_bp) < self.plan.entry_limit*self.plan.quantity*100 or close_pl <= -MAX_DAILY_LOSS:
            raise Halt("insufficient unleveraged cash/options BP or daily loss cap")
        if balances.get("pending_orders_count", 0) not in (0,"0",None):
            raise Halt("pending account orders")
        positions_response = raw["positions"].get("positions") or {}
        orders_response = raw["orders"].get("orders") or {}
        if not isinstance(positions_response,dict) or not isinstance(orders_response,dict):
            raise Halt("unrecognized positions/orders response")
        positions = one_or_many(positions_response.get("position"))
        orders = one_or_many(orders_response.get("order"))
        # Fail closed if any position / active order in paper account, even unrelated.
        if positions:
            raise Halt("existing paper positions: no new entry")
        open_states = {"pending", "open", "partially_filled", "pending_cancel", "accepted", "held"}
        if any(str(x.get("status","")).lower() in open_states for x in orders):
            raise Halt("existing open paper order: no new entry")
        if any(x.get("tag") == tag for x in orders):
            raise Halt("broker already has strategy tag; prevent duplicate")
        if self.journal.session_count(now.date().isoformat()) >= 2:
            raise Halt("max two local order attempts per day")

    def quotes(self, raw, now):
        quotes = one_or_many(raw["quotes"].get("quotes",{}).get("quote"))
        by_symbol = {q.get("symbol"):q for q in quotes if isinstance(q,dict)}
        if self.plan.underlying not in by_symbol or self.plan.option_symbol not in by_symbol:
            raise Halt("missing underlying/option quote")
        u,o=by_symbol[self.plan.underlying],by_symbol[self.plan.option_symbol]
        # Tradier sandbox timestamps are 15 minutes behind. Allow a 20-minute
        # *sandbox-only* quote window; this is NOT a real-time momentum signal.
        for q in (u,o):
            timestamps=[q.get("bid_date"),q.get("ask_date")]
            if any(v is None for v in timestamps):
                raise Halt("quote timestamp missing")
            for ts in timestamps:
                diff=now.timestamp()-float(ts)/1000
                if diff < -30 or diff > 20*60:
                    raise Halt("sandbox quote too old or in future")
        if dec(u.get("volume"),"underlying volume") < self.plan.min_underlying_volume:
            raise Halt("underlying volume below minimum")
        qtype=o.get("type")
        if qtype and qtype != "option":
            raise Halt("option symbol is not an option")
        return u,o
