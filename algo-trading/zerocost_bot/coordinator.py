"""Paper-only coordinator: consensus -> broker readback -> risk veto -> journal -> PAPER order.

No live brokerage host, no background runner, no automatic arming. This is
intentionally NOT called by the read-only streaming market research program.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import os
from .agents import Decision
from .risk_gate import RiskGate, BrokerState, Quote, Preflight
from .journal import OrderJournal, order_key
from .paper_broker import PaperBroker, make_bracket, ORDER_PREFIX


@dataclass(frozen=True)
class PreparedPaper:
    decision: Decision
    quote: Quote
    bar_time: datetime
    risk: Preflight
    payload: dict
    reservation_id: str


class PaperCoordinator:
    def __init__(self, broker: PaperBroker, journal: OrderJournal, gate=None):
        if not isinstance(broker, PaperBroker):
            raise TypeError("paper broker adapter required; live adapter rejected")
        self.broker = broker
        self.journal = journal
        self.gate = gate or RiskGate()

    @staticmethod
    def broker_state(snapshot):
        acct = snapshot["account"]
        clock = snapshot["clock"]
        # Snapshot must originate from the authorized paper broker. Fail closed
        # if the broker did not supply enough equity or order information.
        for key in ("equity","cash","buying_power","last_equity","status"):
            if key not in acct:
                raise ValueError("missing broker account field: "+key)
        for key in ("positions", "open_orders", "today_orders"):
            if key not in snapshot or not isinstance(snapshot[key],list):
                raise ValueError("missing broker account inventory")
        if "is_open" not in clock:
            raise ValueError("missing broker market clock")
        count=sum(str(o.get("client_order_id","")).startswith(ORDER_PREFIX)
                  for o in snapshot["today_orders"])
        return BrokerState(
            cash=Decimal(str(acct["cash"])),
            equity=Decimal(str(acct["equity"])),
            day_start_equity=Decimal(str(acct["last_equity"])),
            buying_power=Decimal(str(acct["buying_power"])),
            positions=len(snapshot["positions"]),
            pending_orders=len(snapshot["open_orders"]),
            entries_today=count,
            market_open=bool(clock["is_open"]),
            trading_blocked=(acct["status"] != "ACTIVE" or
               bool(acct.get("trading_blocked")) or
               bool(acct.get("account_blocked")) or
               bool(acct.get("trade_suspended_by_user")))
        )

    def prepare(self, decision: Decision, quote: Quote, bar_time: datetime,
                now: datetime):
        """Read-only request: broker readback and deterministic order proposal."""
        if bar_time.tzinfo is None:
            raise ValueError("bar timezone required")
        snapshot = self.broker.snapshot()
        state = self.broker_state(snapshot)
        risk = self.gate.check(decision, state, quote, now)
        if not risk.approved:
            return {"status": "skip", "reason": risk.reason}
        # Independent original paper-broker checks remain in place.
        broker_qty = self.broker.validate(
            snapshot, decision.symbol, bar_time,
            float(quote.ask),
            max_fraction=float(self.gate.p.maximum_equity_fraction),
            max_daily_orders=self.gate.p.max_entries_per_day
        )
        if broker_qty < risk.qty:
            return {"status": "skip", "reason": "paper broker limit below risk proposal"}
        reservation = order_key("v02", decision.symbol, bar_time)
        paper_client_id = ORDER_PREFIX + reservation.rsplit("-",1)[-1]
        payload = make_bracket(
            decision.symbol,risk.qty,Decimal(risk.entry_limit),
            stop_fraction=self.gate.p.stop_fraction,
            target_fraction=self.gate.p.take_profit_fraction,
            client_id=paper_client_id
        )
        return PreparedPaper(decision,quote,bar_time,risk,payload,reservation)

    def submit(self, prepared: PreparedPaper, explicitly_armed=False, now=None):
        """Submit PAPER order only when owner manually double-arms paper tests.

        An uncertain broker outcome is permanently BLOCKED in the journal until
        a human or a future read-only broker reconciliation confirms state.
        """
        if not isinstance(prepared,PreparedPaper):
            raise ValueError("not a reviewed paper proposal")
        if (not explicitly_armed or
                os.environ.get("SF_PAPER_ORDER_ENABLE")!="PAPER_ONLY_APPROVED"):
            raise RuntimeError("paper submission disabled")
        now = now or datetime.now(timezone.utc)
        snapshot = self.broker.snapshot()
        risk = self.gate.check(prepared.decision,self.broker_state(snapshot),
                               prepared.quote,now)
        if not risk.approved or risk.qty != prepared.risk.qty:
            return {"status":"skip","reason":"broker state or price changed; re-review"}
        # Run broker's own independent pretrade validations AGAIN before reserving.
        try:
            max_qty=self.broker.validate(
                snapshot,prepared.decision.symbol,prepared.bar_time,
                float(prepared.quote.ask),
                max_fraction=float(self.gate.p.maximum_equity_fraction),
                max_daily_orders=self.gate.p.max_entries_per_day)
        except (ValueError,RuntimeError) as ex:
            return {"status":"skip","reason":"broker preflight rejected: "+str(ex)}
        if max_qty < prepared.risk.qty:
            return {"status":"skip","reason":"broker share cap changed"}
        first,key=self.journal.reserve("v02",prepared.decision.symbol,
                                       prepared.bar_time)
        if key != prepared.reservation_id or not first:
            return {"status":"duplicate_blocked","reason":"proposal already reserved; reconcile broker"}
        try:
            outcome=self.broker.paper_submit(prepared.payload,explicitly_armed=True)
            if outcome.get("status")=="submitted_to_paper_broker":
                self.journal.transition(key,"submitted")
            elif outcome.get("status")=="already_exists":
                self.journal.transition(key,"unknown")
            else:
                self.journal.transition(key,"unknown")
            return {"status":outcome.get("status","unknown"),
                    "paper_only":True,
                    "client_order_id":prepared.payload["client_order_id"],
                    "broker_order_id":outcome.get("order",{}).get("id")}
        except Exception:
            self.journal.transition(key,"unknown")
            return {"status":"unknown_needs_reconciliation",
                    "reason":"paper broker result uncertain; do not retry",
                    "paper_only":True}
