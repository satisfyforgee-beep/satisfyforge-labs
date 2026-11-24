"""Offline research controls. No broker calls, orders, or scheduler.

Use the existing paper engine as the sole fill writer. These functions return
research evidence only; never interpret a suggested size as authorization.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR
from datetime import datetime, timezone
from math import isfinite, sqrt
from statistics import stdev


def dec(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a number")
    d = Decimal(str(value))
    if not d.is_finite():
        raise ValueError("Nonfinite number")
    return d


def utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timezone required")
    return value.astimezone(timezone.utc)


def size_long(*, equity, cash, exposure, symbol_exposure, reserved_cash,
              price, stop_distance, quantity_step, fee_bps=10, slip_bps=5,
              daily_loss=0, weekly_loss=0, drawdown=0, inventory_verified=False):
    """Advisory cap in units; existing order engine must independently recheck.
    Exposure includes pending buys; reserved_cash is unavailable for new orders.
    stop_distance is a modeled price distance, not a guaranteed loss.
    """
    result = {"quantity": "0", "broker_submit_allowed": False, "paper_only": True}
    if inventory_verified is not True:
        return dict(result, reason="UNVERIFIED_INVENTORY")
    try:
        e,c,x,s,r,p,d,q,f,b,dl,wl,dd = map(dec,(equity,cash,exposure,symbol_exposure,
            reserved_cash,price,stop_distance,quantity_step,fee_bps,slip_bps,
            daily_loss,weekly_loss,drawdown))
        if min(e,p,d,q)<=0 or min(c,x,s,r,f,b,dl,wl,dd)<0 or s>x or r>c or c>e or c-r+x>e or d>=p or max(f,b)>1000:
            raise ValueError("Invalid cash-only inventory")
        if dl>=e*Decimal(".01") or wl>=e*Decimal(".03") or dd>=Decimal(".05"):
            return dict(result, reason="LOSS_REVIEW")
        # Budget entry costs and adverse exit costs; gap losses can exceed it.
        buy=p*(1+b/10000)*(1+f/10000)
        sell=(p-d)*(1-b/10000)*(1-f/10000)
        unit_risk=buy-sell
        budget=min(c-r, e*Decimal(".50")-s, e*Decimal(".80")-x)
        qty=min(budget/buy,e*Decimal(".005")/unit_risk)
        qty=max(Decimal(0),(qty/q).to_integral_value(rounding=ROUND_FLOOR)*q)
        return dict(result,quantity=str(qty),reason="RESEARCH_SIZE" if qty else "INSUFFICIENT_BUDGET",
                    modeled_risk=str(qty*unit_risk),modeled_debit=str(qty*buy))
    except (ValueError,ArithmeticError,TypeError):
        return dict(result,reason="INVALID_INPUT")


def rank_markets(captures, *, cutoff, max_age_seconds=172800):
    """Rank completed, caller-verified daily bars by volatility-scaled momentum.
    Not a return forecast. No cross-market cash allocation or order submission.
    Each capture includes source, verified=True, and chronological bars with
    close_at, available_at, open/high/low/close; no silent forward fill.
    """
    now=utc(cutoff)
    if not isfinite(max_age_seconds) or max_age_seconds<=0:
        raise ValueError("Invalid freshness limit")
    accepted=[]; rejected=[]; seen=set()
    for item in captures:
        symbol=item.get("symbol")
        if not isinstance(symbol,str) or not symbol or symbol in seen:
            raise ValueError("Missing or duplicate market")
        seen.add(symbol)
        try:
            if item.get("verified") is not True or not item.get("source"):
                raise ValueError("UNVERIFIED_SOURCE")
            bars=item["bars"]
            if len(bars)<101:
                raise ValueError("INSUFFICIENT_HISTORY")
            times=[]; prices=[]; prev_available=None
            for bar in bars:
                t=utc(bar["close_at"]); a=utc(bar["available_at"])
                o,h,l,c=map(float,(bar["open"],bar["high"],bar["low"],bar["close"]))
                if not all(isfinite(v) and v>0 for v in (o,h,l,c)) or l>min(o,c) or h<max(o,c) or h<l:
                    raise ValueError("BAD_OHLC")
                if t>a or a>now or (times and t<=times[-1]) or (prev_available and a<prev_available):
                    raise ValueError("FUTURE_OR_UNORDERED_DATA")
                times.append(t); prices.append(c); prev_available=a
            if (now-times[-1]).total_seconds()>max_age_seconds:
                raise ValueError("STALE_DATA")
            recent=prices[-21:]
            returns=[b/a-1 for a,b in zip(recent,recent[1:])]
            vol=stdev(returns)
            mom=prices[-1]/prices[-21]-1
            trend=prices[-1]>sum(prices[-100:])/100
            if vol<=0 or mom<=0 or not trend:
                raise ValueError("NO_QUALIFIED_TREND")
            accepted.append({"symbol":symbol,"score":mom/(vol*sqrt(20)),
                             "momentum_20":mom,"daily_volatility":vol,
                             "source":item["source"],"asof":times[-1].isoformat()})
        except (ValueError,ArithmeticError,TypeError,KeyError,OverflowError) as exc:
            rejected.append({"symbol":symbol,"reason":str(exc)})
    accepted.sort(key=lambda row:(-row["score"],row["symbol"]))
    return {"ranked":accepted,"rejected":rejected,"broker_submit_allowed":False,
            "paper_only":True}


def compare_equity(observations, *, allocation="0.5", annual_cash_rate="0"):
    """Independent valuation report on aligned, chronological observations.
    Each row has time, equity, hold_equity. Cash and a fixed ex-ante allocated
    hold benchmark start at the same capital. Allocation matching is NOT
    realized volatility matching. Hold series must already include its costs.
    """
    w=dec(allocation); rate=dec(annual_cash_rate)
    if not 0<=w<=1 or rate!=0:
        raise ValueError("Allocation must be 0..1; cash benchmark is zero interest")
    if len(observations)<2:
        raise ValueError("Need at least two aligned valuations")
    e=[]; h=[]; times=[]
    for row in observations:
        t=utc(row["time"]); v=dec(row["equity"]); b=dec(row["hold_equity"])
        if min(v,b)<=0 or (times and t<=times[-1]):
            raise ValueError("Invalid or duplicate valuation")
        times.append(t); e.append(v); h.append(b)
    if e[0]!=h[0]:
        raise ValueError("Benchmark starting equity mismatch")
    base=e[0]
    def stats(values):
        peak=values[0]; dd=Decimal(0)
        for v in values:
            peak=max(peak,v); dd=max(dd,1-v/peak)
        return {"final":str(values[-1]),"return":str(values[-1]/base-1),"drawdown":str(dd)}
    fixed=[base*(1-w)+w*v for v in h]
    return {"strategy":stats(e),"cash":stats([base]*len(e)),
            "buy_hold":stats(h),"allocation_matched_hold":stats(fixed),
            "allocation":str(w),"start":times[0].isoformat(),"end":times[-1].isoformat(),
            "paper_only":True,"benchmark_note":"Ex-ante allocation match, not volatility matched"}


def journal_report(engine, observations):
    """Read existing SQLite paper journal; no separate fill ledger.
    Valuations must be independently supplied; never invent marks or drawdown.
    """
    orders=engine.orders()
    ids=set(); fees=Decimal(0); pnl=Decimal(0); rejects=[]; fills=0
    for row in orders:
        key=row["client_id"]
        if key in ids:
            raise ValueError("Duplicate journal order")
        ids.add(key)
        if row["status"]=="FILLED":
            fees+=dec(row["fee"]); pnl+=dec(row["realized_pnl"]); fills+=1
        elif row["status"] in ("REJECTED","NOT_FILLED"):
            rejects.append({"client_id":key,"reason":row["reason"],"status":row["status"]})
    return {"paper_only":True,"fills":fills,"fees":str(fees),"realized_pnl":str(pnl),
            "rejected_orders":rejects,"valuation_report":compare_equity(observations) if observations else None,
            "warning":"Separate reads; use quiescent journal, not atomic live snapshot"}


def risk_matched_hold(observations, calibration_count):
    """Choose a frozen volatility-matched hold weight using calibration only.
    Evaluate untouched later rows rebased to the same capital. No leverage.
    Requires regularly spaced aligned observations and no tuning on holdout.
    """
    compare_equity(observations)
    if type(calibration_count) is not int or not 3<=calibration_count<=len(observations)-2:
        raise ValueError("Insufficient calibration or holdout")
    dates=[utc(r["time"]) for r in observations]
    gaps=[(b-a).total_seconds() for a,b in zip(dates,dates[1:])]
    if len(set(gaps))!=1:
        raise ValueError("Volatility match requires regular observation spacing")
    e=[dec(r["equity"]) for r in observations]; h=[dec(r["hold_equity"]) for r in observations]
    def vol(xs):
        return stdev([float(b/a-1) for a,b in zip(xs,xs[1:])])
    hv=vol(h[:calibration_count])
    if hv<=0:
        raise ValueError("Zero benchmark calibration volatility")
    w=min(1.0,vol(e[:calibration_count])/hv)
    start=calibration_count
    base=e[start]
    rows=[{"time":r["time"],"equity":str(e[i]),"hold_equity":str(base*h[i]/h[start])}
          for i,r in enumerate(observations) if i>=start]
    out=compare_equity(rows,allocation=str(w))
    out["benchmark_note"]="Weight frozen from prior calibration return volatility; approximate, no daily rebalancing; holdout volatility may differ."
    out["calibration_end"]=dates[start-1].isoformat()
    return out
