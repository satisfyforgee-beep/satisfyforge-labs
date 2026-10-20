"""Strongly restricted Alpaca PAPER broker adapter; never talks to live trading host.

A returned HTTP success from paper mode is a *simulated* broker order only.
No calls to this module are made in demo/replay mode.
"""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
import json
import os
import re

PAPER_HOST = "https://paper-api.alpaca.markets"
ORDER_PREFIX = "sf-paper-v01-"

def money(v):
    return str(Decimal(str(v)).quantize(Decimal(".01"),rounding=ROUND_HALF_UP))

def make_bracket(symbol,qty,entry_limit,stop_fraction=.02,target_fraction=.035,client_id=None):
    if not re.fullmatch(r"[A-Z]{1,6}",symbol):
        raise ValueError("equity symbol only")
    if not isinstance(qty,int) or qty<1 or qty>1000:
        raise ValueError("invalid whole-share quantity")
    price=Decimal(str(entry_limit))
    if price < Decimal(".10"):
        raise ValueError("price too low")
    if not Decimal("0") < Decimal(str(stop_fraction)) < Decimal("0.2"):
        raise ValueError("invalid stop")
    if not Decimal("0") < Decimal(str(target_fraction)) < Decimal("0.5"):
        raise ValueError("invalid target")
    if client_id is None or not re.fullmatch(r"sf-paper-v01-[A-Za-z0-9-]{1,28}",client_id):
        raise ValueError("missing deterministic client order id")
    stop=Decimal(money(price*(1-Decimal(str(stop_fraction)))))
    target=Decimal(money(price*(1+Decimal(str(target_fraction)))))
    if stop>=price or target<=price:
        raise ValueError("stop and take profit must straddle entry")
    return {"symbol":symbol,"qty":str(qty),"side":"buy","type":"limit",
            "time_in_force":"day","limit_price":money(price),
            "order_class":"bracket",
            "take_profit":{"limit_price":money(target)},
            "stop_loss":{"stop_price":money(stop)},
            "client_order_id":client_id}


class PaperBroker:
    def __init__(self,key=None,secret=None,transport=None):
        self.key = key or os.environ.get("ALPACA_PAPER_KEY")
        self.secret = secret or os.environ.get("ALPACA_PAPER_SECRET")
        if not self.key or not self.secret:
            raise RuntimeError("paper account keys required; never put them in repository")
        self.transport=transport or self._http

    def _http(self,method,path,params=None,body=None):
        # Never let a caller override the paper hostname or supply a URL.
        if not path.startswith("/v2/") or "//" in path or "://" in path:
            raise ValueError("only Alpaca paper /v2 endpoints allowed")
        url=PAPER_HOST+path
        if params:
            url += "?"+urlencode(params)
        payload=json.dumps(body).encode() if body is not None else None
        req=Request(url,data=payload,method=method,headers={
            "APCA-API-KEY-ID":self.key, "APCA-API-SECRET-KEY":self.secret,
            "Content-Type":"application/json","Accept":"application/json"})
        with urlopen(req,timeout=8) as response:
            return json.load(response)

    def request(self,method,path,params=None,body=None):
        return self.transport(method,path,params,body)

    def snapshot(self):
        return {
            "account":self.request("GET","/v2/account"),
            "clock":self.request("GET","/v2/clock"),
            "positions":self.request("GET","/v2/positions"),
            "open_orders":self.request("GET","/v2/orders",{"status":"open","nested":"true"}),
            "today_orders":self.request("GET","/v2/orders",{"status":"all","limit":"200","direction":"desc"}),
        }

    def validate(self, snapshot, symbol, latest_time, current_limit, max_fraction=.20,
                 max_daily_orders=3):
        account=snapshot["account"]
        if (account.get("status")!="ACTIVE" or account.get("trading_blocked")
                or account.get("account_blocked") or account.get("trade_suspended_by_user")):
            raise RuntimeError("paper account not active or trading blocked")
        # Reject new entries after a 3% equity decline relative to last close.
        # last_equity is required, so missing broker risk state fails closed.
        prior=Decimal(str(account.get("last_equity") or "0"))
        equity_now=Decimal(str(account.get("equity") or "0"))
        if prior <= 0 or equity_now <= 0 or equity_now <= prior*Decimal("0.97"):
            raise RuntimeError("daily loss limit hit or missing broker equity baseline")
        if not snapshot["clock"].get("is_open"):
            raise RuntimeError("market closed")
        now=datetime.now(timezone.utc)
        if latest_time.tzinfo is None or not 0 <= (now-latest_time).total_seconds() <= 150:
            raise RuntimeError("market minute bar stale, out of order, or in future")
        if snapshot["positions"] or snapshot["open_orders"]:
            raise RuntimeError("existing paper position/open order: no new trade")
        from zoneinfo import ZoneInfo
        local=now.astimezone(ZoneInfo("America/New_York"))
        if local.hour < 9 or (local.hour == 9 and local.minute < 35) or local.hour>=15:
            raise RuntimeError("outside approved paper-entry hours (09:35 to 14:59 ET)")
        if any(x.get("client_order_id","").startswith(ORDER_PREFIX)
               and x.get("created_at","").startswith(now.date().isoformat())
               for x in snapshot["today_orders"]):
            count=sum(x.get("client_order_id","").startswith(ORDER_PREFIX)
                      and x.get("created_at","").startswith(now.date().isoformat())
                      for x in snapshot["today_orders"])
            if count>=max_daily_orders:
                raise RuntimeError("max daily paper orders reached")
        equity=Decimal(str(account["equity"]))
        bp=Decimal(str(account["buying_power"]))
        max_budget=min(bp-Decimal("1"),equity*Decimal(str(max_fraction)))
        limit=Decimal(str(current_limit))
        qty=int(max_budget // limit)
        if qty<1:
            raise RuntimeError("insufficient paper capital under allocation cap")
        if Decimal(qty)*limit>max_budget:
            raise RuntimeError("allocation cap violation")
        return qty

    def paper_submit(self, payload, explicitly_armed=False):
        """This is a real POST, but only to Alpaca's PAPER simulation host.
        Calling requires a per-process explicit flag and env kill switch.
        """
        if not explicitly_armed or os.environ.get("SF_PAPER_ORDER_ENABLE")!="PAPER_ONLY_APPROVED":
            raise RuntimeError("paper-order kill switch is OFF")
        if payload.get("order_class")!="bracket" or payload.get("side")!="buy":
            raise ValueError("only long equity bracket buy paper orders allowed")
        if not str(payload.get("client_order_id","")).startswith(ORDER_PREFIX):
            raise ValueError("missing project paper client order id")
        # Idempotency: check by client ID before POST. On transport timeout,
        # caller must query broker status; never blindly repeat a POST.
        try:
            existing=self.request("GET","/v2/orders:by_client_order_id",
                                  {"client_order_id":payload["client_order_id"]})
            if existing and existing.get("id"):
                return {"status":"already_exists","order":existing}
        except HTTPError as err:
            if err.code!=404:
                raise
        result=self.request("POST","/v2/orders",body=payload)
        return {"status":"submitted_to_paper_broker","order":result}
