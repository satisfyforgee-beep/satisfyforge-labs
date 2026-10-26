"""Durable OFFLINE forward-simulation of three spot crypto virtual positions.

NO simulated exchange API, brokerage orders, production credentials or POST.
Events are based on real public Kraken book snapshots, but fill assumptions
are modeled (never actual exchange fills). Stop/target are software checks
only: missed polls and gaps can exceed stop limits. A hard three-entry
lifetime cap makes repeated invocations safe.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP
from pathlib import Path

from .market_coverage import AssetClass, CoverageGate, MarketQuote
from .paper_capital import PaperCapital, CapitalBlocked

SYMBOLS = ("BTC/USD", "ETH/USD", "SOL/USD")
ALLOCATION = Decimal("15.00")
ENTRY_FEE_RATE = Decimal("0.004")
EXIT_FEE_RATE = Decimal("0.004")
SLIPPAGE = Decimal("0.0005")
STOP = Decimal("0.02")
TARGET = Decimal("0.035")
TWO_PLACES = Decimal("0.01")
EIGHT_PLACES = Decimal("0.00000001")
MAX_HOLD = timedelta(hours=24)
TRIAL_ID = "trial20261026"
_MODE = "OFFLINE_FORWARD_VIRTUAL_CRYPTO_NOT_BROKER_FILLED"


def _fee(value, rate):
    return (value * rate).quantize(TWO_PLACES, rounding=ROUND_UP)


def _quotes(quotes, now):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise CapitalBlocked("timezone-aware check time required")
    if not isinstance(quotes, dict) or set(quotes) != set(SYMBOLS):
        raise CapitalBlocked("complete three-asset quote set required")
    for sym, q in quotes.items():
        if (not isinstance(q, MarketQuote) or q.asset != AssetClass.CRYPTO
                or q.provider != "kraken_public" or q.symbol != sym):
            raise CapitalBlocked("only public Kraken spot data supported")
        gate = CoverageGate(max_age_seconds=10)
        gate.ingest(q)
        verdict = gate.assess(sym, AssetClass.CRYPTO, now)
        if verdict.status != "RESEARCH_ONLY" or verdict.source != "kraken_public":
            raise CapitalBlocked("unverified or outdated spot book")
        spread = (Decimal(str(q.ask)) - Decimal(str(q.bid))) / Decimal(str(q.ask))
        if spread < 0 or spread > Decimal("0.005"):
            raise CapitalBlocked("unacceptable simulated entry/exit spread")


class VirtualCryptoTrial:
    def __init__(self, db_path):
        path = Path(db_path).expanduser().absolute()
        self.ledger = PaperCapital(str(path), opening_cash="150.00",
                                   maximum_order_debit="30.00",
                                   maximum_reservations=5)

    def _history(self):
        with closing(self.ledger._db()) as db:
            return db.execute(
                "SELECT event_id,kind,reference,asset,symbol,quantity,price,fee,amount,observed_at "
                "FROM capital_events ORDER BY sequence"
            ).fetchall()

    def _buy_times(self):
        times = {}
        for row in self._history():
            if row[1] == "buy" and row[3] == "crypto":
                times.setdefault(row[4], datetime.fromisoformat(row[9]))
        return times

    def _trial_intents(self):
        return {
            row[4] for row in self._history()
            if row[1] == "reserve" and row[2].startswith(TRIAL_ID)
        }

    def _preflight_book(self):
        snap = self.ledger.snapshot()
        if snap["active_reservation_count"] != 0:
            raise CapitalBlocked("unfinished reservation; stop and inspect journal")
        if any(pos.get("asset") != "crypto" or pos.get("symbol") not in SYMBOLS
               for pos in snap["positions"]):
            raise CapitalBlocked("unexpected portfolio asset; stop")
        return snap

    def start_three(self, quotes, now):
        _quotes(quotes, now)
        snap = self._preflight_book()
        intent_history = self._trial_intents()
        if snap["positions"] or intent_history:
            return {"mode": _MODE, "state": "ALREADY_STARTED_NO_DUPLICATE",
                    "virtual_buys_this_call": 0, "broker_orders_sent": 0,
                    "account": self.summary(quotes, now)}
        # Fetch and validate all three before starting; avoid partial work
        # caused by missing symbol, spread or invalid quote.
        plans = []
        for symbol in SYMBOLS:
            q = quotes[symbol]
            ask = Decimal(str(q.ask))
            price = (ask * (Decimal(1) + SLIPPAGE)).quantize(
                EIGHT_PLACES, rounding=ROUND_UP)
            budget = min(ALLOCATION, Decimal(snap["available_for_next_paper_trade"]))
            # Reserve a few cents for upward-rounded taker fees and
            # BTC-size granularity, instead of filling above the budget.
            qty = ((budget - Decimal("0.03")) /
                   (price * (Decimal(1) + ENTRY_FEE_RATE))).quantize(
                       EIGHT_PLACES, rounding=ROUND_DOWN)
            cost = qty * price
            fee = _fee(cost, ENTRY_FEE_RATE)
            # Match PaperCapital currency accounting (nearest cent), so
            # the owner-facing debit equals the journaled cash movement.
            debit = (cost + fee).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if qty <= 0 or debit < Decimal("5") or debit > ALLOCATION:
                raise CapitalBlocked("virtual entry can't fit allocated budget")
            plans.append((symbol, qty, price, fee, debit))
        # These are virtual fills assumed at a modeled worse-than-ask price.
        # No request is sent to a broker. Deterministic per-asset trial
        # references and the capital ledger suppress duplicate replays.
        filled = []
        for symbol, qty, price, fee, debit in plans:
            key = TRIAL_ID + ":" + symbol.replace("/", "")
            reserved = self.ledger.reserve_buy(
                key, "crypto", symbol, str(qty), str(price), str(fee), when=now)
            if not reserved:
                raise CapitalBlocked("duplicate trial intent; stop")
            self.ledger.buy_fill(
                key + ":entry", key, "crypto", symbol,
                str(qty), str(price), str(fee), when=now)
            self.ledger.release_terminal_reservation(
                key + ":filled", key, when=now)
            filled.append({
                "asset": "crypto", "symbol": symbol,
                "quantity": str(qty), "virtual_entry_price": str(price),
                "virtual_debit_including_fee": str(debit),
                "entry_fee_estimate": str(fee),
                "model_not_exchange_fill": True,
            })
        return {"mode": _MODE, "state": "THREE_VIRTUAL_ENTRIES_RECORDED",
                "virtual_buys_this_call": len(filled),
                "virtual_buys": filled,
                "broker_orders_sent": 0,
                "account": self.summary(quotes, now)}

    def evaluate_exits(self, quotes, now):
        _quotes(quotes, now)
        self._preflight_book()
        times = self._buy_times()
        exits = []
        for pos in self.ledger.snapshot()["positions"]:
            symbol = pos["symbol"]
            if symbol not in SYMBOLS or symbol not in times:
                raise CapitalBlocked("unrecognized virtual position history")
            qty = Decimal(pos["quantity"])
            cost = Decimal(pos["remaining_book_cost"])
            if qty <= 0 or cost <= 0:
                raise CapitalBlocked("invalid virtual cost basis")
            unit_cost = cost / qty
            bid = Decimal(str(quotes[symbol].bid))
            hold = now.astimezone(timezone.utc) - times[symbol].astimezone(timezone.utc)
            if hold < timedelta(0):
                raise CapitalBlocked("future-dated virtual fill")
            reason = None
            if bid <= unit_cost * (Decimal(1) - STOP):
                reason = "STOP_OBSERVED"
            elif bid >= unit_cost * (Decimal(1) + TARGET):
                reason = "TARGET_OBSERVED"
            elif hold >= MAX_HOLD:
                reason = "MAX_24H_HOLD"
            if reason is None:
                continue
            price = (bid * (Decimal(1) - SLIPPAGE)).quantize(
                EIGHT_PLACES, rounding=ROUND_DOWN)
            gross = qty * price
            fee = _fee(gross, EXIT_FEE_RATE)
            if gross <= fee:
                raise CapitalBlocked("exit costs exceed proceeds")
            event_key = TRIAL_ID + ":" + symbol.replace("/", "") + ":exit"
            self.ledger.sell_fill(
                event_key, "crypto", symbol,
                str(qty), str(price), str(fee), when=now)
            # This is an OFFLINE virtual settlement assumption, not verified
            # transfer/availability in a real cryptocurrency venue.
            self.ledger.confirm_settlement(
                event_key + ":virtualsettle", event_key, when=now)
            realized = (gross - fee).quantize(TWO_PLACES) - cost
            exits.append({
                "symbol": symbol, "reason": reason, "virtual_sale_price": str(price),
                "modeled_exit_fee": str(fee),
                "realized_pnl_after_costs_estimate": str(
                    realized.quantize(TWO_PLACES)),
                "model_not_exchange_fill": True,
            })
        return {"mode": _MODE, "state": "VIRTUAL_EXIT_CHECK_COMPLETE",
                "virtual_exits_this_call": len(exits),
                "exits": exits, "broker_orders_sent": 0,
                "account": self.summary(quotes, now)}

    def summary(self, quotes, now):
        _quotes(quotes, now)
        snap = self._preflight_book()
        marks = []
        estimated_liquidation = Decimal(snap["settled_cash"])
        for pos in snap["positions"]:
            symbol = pos["symbol"]
            q = Decimal(pos["quantity"])
            bid = Decimal(str(quotes[symbol].bid))
            px = bid * (Decimal(1) - SLIPPAGE)
            estimated_value = q * px * (Decimal(1) - EXIT_FEE_RATE)
            estimated_liquidation += estimated_value
            marks.append({
                "asset": "crypto", "symbol": symbol, "quantity": str(q),
                "remaining_book_cost": pos["remaining_book_cost"],
                "reference_bid": str(bid),
                "estimated_net_exit_value": str(
                    estimated_value.quantize(TWO_PLACES)),
                "virtual_protective_stop_reference": str(
                    ((Decimal(pos["remaining_book_cost"]) / q)
                     * (Decimal(1) - STOP)).quantize(TWO_PLACES)),
                "virtual_target_reference": str(
                    ((Decimal(pos["remaining_book_cost"]) / q)
                     * (Decimal(1) + TARGET)).quantize(TWO_PLACES)),
            })
        history = self._history()
        return {
            "mode": _MODE, "at_utc": now.astimezone(timezone.utc).isoformat(),
            "opening_virtual_cash": snap["opening_cash"],
            "settled_virtual_cash": snap["settled_cash"],
            "realized_virtual_pnl": snap["realized_net_pnl"],
            "virtual_entry_event_count": sum(row[1] == "buy" for row in history),
            "virtual_exit_event_count": sum(row[1] == "sell" for row in history),
            "virtual_positions": marks,
            "estimated_total_liquidation_value": str(
                estimated_liquidation.quantize(TWO_PLACES)),
            "broker_orders_sent": 0, "real_money_orders_sent": 0,
            "performance_not_broker_verified": True,
            "warning": ("Single-venue Kraken quote snapshot and modeled "
                        "fees/slippage. Stops are checked ONLY when the script "
                        "runs; gaps and outages can exceed stop references."),
        }
