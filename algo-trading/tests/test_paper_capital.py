"""Pure OFFLINE paper-capital tests. Never opens a brokerage connection."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from zerocost_bot.paper_capital import PaperCapital, CapitalBlocked


T = datetime(2026, 10, 26, 13, 0, tzinfo=timezone.utc)


class PaperCapitalTests(unittest.TestCase):
    @staticmethod
    def proof(sale_execution_id, trade_date="2026-10-26",
              settlement_date="2026-10-27",
              retrieved_at="2026-10-26T20:30:00Z", **changes):
        proof = {
            "provider": "ALPACA_PAPER",
            "date_type": "SETTLEMENT",
            "calendar_id": "alpaca-settlement-calendar-fixture",
            "trade_date": trade_date,
            "settlement_date": settlement_date,
            "retrieved_at": retrieved_at,
            "sale_execution_id": sale_execution_id,
        }
        proof.update(changes)
        return proof

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "private" / "capital.sqlite3")
        self.ledger = PaperCapital(self.path)

    def test_profit_compounds_only_after_settlement(self):
        l = self.ledger
        l.reserve_buy("entry1", "stock", "SOFI", 2, "12.00", ".10", when=T)
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "125.90")
        l.buy_fill("fill1", "entry1", "stock", "SOFI", 1, "12.00", ".05", when=T)
        l.buy_fill("fill2", "entry1", "stock", "SOFI", 1, "12.00", ".05", when=T)
        l.release_terminal_reservation("done1", "entry1", when=T)
        self.assertEqual(l.snapshot()["settled_cash"], "125.90")
        l.sell_fill("exit1", "stock", "SOFI", 2, "14.00", 0, when=T)
        mid = l.snapshot()
        self.assertEqual(mid["realized_net_pnl"], "3.90")
        self.assertEqual(mid["settled_cash"], "125.90")
        self.assertEqual(mid["unsettled_sale_proceeds"], "28.00")
        self.assertEqual(mid["available_for_next_paper_trade"], "125.90")
        l.confirm_settlement("settlement1", "exit1", when=T + timedelta(days=1),
                             calendar_proof=self.proof("exit1"))
        self.assertEqual(l.snapshot()["settled_cash"], "153.90")
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "153.90")
        again = PaperCapital(self.path)
        self.assertEqual(again.snapshot(), l.snapshot())
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_only_unsettled_profit_cannot_fund_next_entry(self):
        l = self.ledger
        for i in range(5):
            intent = "i" + str(i)
            l.reserve_buy(intent, "stock", "SOFI", 1, 30, 0, when=T)
            l.buy_fill("buy" + str(i), intent, "stock", "SOFI", 1, 30, 0, when=T)
            l.release_terminal_reservation("closed" + str(i), intent, when=T)
        self.assertEqual(l.snapshot()["settled_cash"], "0.00")
        l.sell_fill("sale", "stock", "SOFI", 5, 32, 0, when=T)
        self.assertEqual(l.snapshot()["realized_net_pnl"], "10.00")
        self.assertEqual(l.snapshot()["unsettled_sale_proceeds"], "160.00")
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "0.00")
        with self.assertRaises(CapitalBlocked):
            l.reserve_buy("next", "stock", "F", 1, 5, 0, when=T)
        l.confirm_settlement("s1", "sale", when=T + timedelta(days=1),
                             calendar_proof=self.proof("sale"))
        l.reserve_buy("next", "stock", "F", 1, 5, 0, when=T + timedelta(days=1))
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "155.00")

    def test_settlement_requires_explicit_complete_calendar_proof(self):
        l = self.ledger
        l.reserve_buy("i", "stock", "F", 1, 10, 0, when=T)
        l.buy_fill("b", "i", "stock", "F", 1, 10, 0, when=T)
        l.release_terminal_reservation("done", "i", when=T)
        l.sell_fill("sale", "stock", "F", 1, 11, 0, when=T)
        for proof in (None, {}, self.proof("wrong"),
                      self.proof("sale", provider="UNVERIFIED"),
                      self.proof("sale", settlement_date="2026-10-26")):
            with self.subTest(proof=proof):
                with self.assertRaises(CapitalBlocked):
                    l.confirm_settlement("settle", "sale", when=T + timedelta(days=1),
                                         calendar_proof=proof)
        self.assertEqual(l.snapshot()["unsettled_sale_proceeds"], "11.00")

    def test_holiday_dates_are_proof_driven_not_weekday_guesses(self):
        trade = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
        l = self.ledger
        l.reserve_buy("h", "stock", "F", 1, 10, 0, when=trade)
        l.buy_fill("hb", "h", "stock", "F", 1, 10, 0, when=trade)
        l.release_terminal_reservation("hd", "h", when=trade)
        l.sell_fill("hs", "stock", "F", 1, 11, 0, when=trade)
        proof = self.proof("hs", trade_date="2026-11-25",
                           settlement_date="2026-11-27",
                           retrieved_at="2026-11-25T20:00:00Z")
        with self.assertRaises(CapitalBlocked):
            l.confirm_settlement("early", "hs",
                                 when=datetime(2026, 11, 26, 18, tzinfo=timezone.utc),
                                 calendar_proof=proof)
        l.confirm_settlement("verified", "hs",
                             when=datetime(2026, 11, 27, 15, tzinfo=timezone.utc),
                             calendar_proof=proof)
        self.assertEqual(l.snapshot()["settled_cash"], "151.00")

    def test_settlement_proof_is_durable_idempotent_and_conflicts_halt(self):
        l = self.ledger
        l.reserve_buy("i", "stock", "F", 1, 10, 0, when=T)
        l.buy_fill("b", "i", "stock", "F", 1, 10, 0, when=T)
        l.release_terminal_reservation("done", "i", when=T)
        l.sell_fill("sale", "stock", "F", 1, 11, 0, when=T)
        proof = self.proof("sale")
        when = T + timedelta(days=1)
        self.assertTrue(l.confirm_settlement("s", "sale", when=when,
                                             calendar_proof=proof))
        self.assertFalse(l.confirm_settlement("s", "sale", when=when,
                                              calendar_proof=proof))
        with self.assertRaises(CapitalBlocked):
            l.confirm_settlement("s", "sale", when=when,
                                 calendar_proof=self.proof(
                                     "sale", calendar_id="different-fixture"))
        with l._db() as db:
            evidence = db.execute(
                "SELECT evidence FROM capital_events WHERE event_id='settle:s'"
            ).fetchone()[0]
        self.assertIn('"calendar_id":"alpaca-settlement-calendar-fixture"', evidence)

    def test_equity_calendar_cannot_settle_options_or_crypto(self):
        l = self.ledger
        opt = "SOFI261030C00015000"
        l.reserve_buy("o", "option", opt, 1, ".20", 0, when=T)
        l.buy_fill("ob", "o", "option", opt, 1, ".20", 0, when=T)
        l.release_terminal_reservation("od", "o", when=T)
        l.sell_fill("os", "option", opt, 1, ".30", 0, when=T)
        with self.assertRaises(CapitalBlocked):
            l.confirm_settlement("ox", "os", when=T + timedelta(days=1),
                                 calendar_proof=self.proof("os"))

    def test_option_multiplier_and_crypto_fractional_loss(self):
        l = self.ledger
        opt = "SOFI261030C00015000"
        l.reserve_buy("opt1", "option", opt, 1, ".20", "1.00", when=T)
        l.buy_fill("buyopt", "opt1", "option", opt, 1, ".20", "1.00", when=T)
        l.release_terminal_reservation("optclose", "opt1", when=T)
        l.sell_fill("sellopt", "option", opt, 1, ".30", "1.00", when=T)
        self.assertEqual(l.snapshot()["realized_net_pnl"], "8.00")
        l.reserve_buy("btc1", "crypto", "BTC/USD", ".001", "20000", 0, when=T)
        l.buy_fill("buybtc", "btc1", "crypto", "BTC/USD", ".001", "20000", 0, when=T)
        l.release_terminal_reservation("btcdone", "btc1", when=T)
        l.sell_fill("sellbtc", "crypto", "BTC/USD", ".001", "19000", 0, when=T)
        snap = l.snapshot()
        self.assertEqual(snap["realized_net_pnl"], "7.00")
        self.assertEqual(snap["unsettled_sale_proceeds"], "48.00")
        self.assertEqual(snap["available_for_next_paper_trade"], "109.00")

    def test_fee_and_partial_sale_fifo_basis(self):
        l = self.ledger
        l.reserve_buy("i", "stock", "F", 2, 10, 2, when=T)
        l.buy_fill("e1", "i", "stock", "F", 2, 10, 2, when=T)
        l.release_terminal_reservation("done", "i", when=T)
        l.sell_fill("s1", "stock", "F", 1, 11, 1, when=T)
        self.assertEqual(l.snapshot()["realized_net_pnl"], "-1.00")
        self.assertEqual(l.snapshot()["positions"][0]["remaining_book_cost"], "11.00")
        l.sell_fill("s2", "stock", "F", 1, 15, 1, when=T)
        self.assertEqual(l.snapshot()["realized_net_pnl"], "2.00")
        self.assertEqual(l.snapshot()["positions"], [])

    def test_duplicate_execution_is_idempotent_and_conflicts_halt(self):
        l = self.ledger
        args = ("i", "stock", "CLF", 1, 10, 0)
        self.assertTrue(l.reserve_buy(*args, when=T))
        self.assertFalse(l.reserve_buy(*args, when=T))
        with self.assertRaises(CapitalBlocked):
            l.reserve_buy("i", "stock", "CLF", 1, 11, 0, when=T)
        self.assertTrue(l.buy_fill("f", "i", "stock", "CLF", 1, 10, 0, when=T))
        self.assertFalse(l.buy_fill("f", "i", "stock", "CLF", 1, 10, 0, when=T))
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("f", "i", "stock", "CLF", 1, 11, 0, when=T)
        self.assertEqual(l.snapshot()["settled_cash"], "140.00")

    def test_fill_must_match_reserved_quantity_limit_and_fee(self):
        l = self.ledger
        l.reserve_buy("r", "stock", "F", 1, 20, 1, when=T)
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("more", "r", "stock", "F", 2, 8, 0, when=T)
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("badprice", "r", "stock", "F", 1, 21, 0, when=T)
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("badfee", "r", "stock", "F", 1, 18, 2, when=T)
        l.buy_fill("good", "r", "stock", "F", 1, 18, 1, when=T)
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("second", "r", "stock", "F", 1, 1, 0, when=T)
        self.assertEqual(l.snapshot()["reserved_cash"], "2.00")
        self.assertEqual(l.snapshot()["settled_cash"], "131.00")

    def test_pending_fills_do_not_overspend_or_release_cash(self):
        l = self.ledger
        for i in range(5):
            l.reserve_buy("r" + str(i), "stock", "SOFI", 1, 30, 0, when=T)
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "0.00")
        with self.assertRaises(CapitalBlocked):
            l.reserve_buy("r5", "stock", "F", 1, 1, 0, when=T)
        l.buy_fill("a", "r0", "stock", "SOFI", 1, 25, 0, when=T)
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "0.00")
        l.release_terminal_reservation("complete0", "r0", when=T)
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "5.00")
        with self.assertRaises(CapitalBlocked):
            l.buy_fill("b", "r0", "stock", "SOFI", 1, 1, 0, when=T)

    def test_five_open_positions_limit_new_paper_buys(self):
        l = self.ledger
        for i, sym in enumerate(("F", "SOFI", "AAL", "CLF", "BAC")):
            intent = "intent" + str(i)
            l.reserve_buy(intent, "stock", sym, 1, 5, 0, when=T)
            l.buy_fill("fill" + str(i), intent, "stock", sym, 1, 5, 0, when=T)
            l.release_terminal_reservation("done" + str(i), intent, when=T)
        self.assertEqual(l.snapshot()["available_for_next_paper_trade"], "125.00")
        with self.assertRaises(CapitalBlocked):
            l.reserve_buy("sixth", "stock", "AAPL", 1, 5, 0, when=T)
        l.sell_fill("exit1", "stock", "BAC", 1, 6, 0, when=T)
        l.reserve_buy("sixth", "stock", "AAPL", 1, 5, 0, when=T)
        self.assertEqual(l.snapshot()["reserved_cash"], "5.00")
        self.assertEqual(l.snapshot()["unsettled_sale_proceeds"], "6.00")

    def test_denies_fake_profit_and_unverified_settlement(self):
        l = self.ledger
        with self.assertRaises(CapitalBlocked):
            l.sell_fill("s", "stock", "AAPL", 1, 20, 0, when=T)
        with self.assertRaises(CapitalBlocked):
            l.confirm_settlement("fake", "missing", when=T,
                                 calendar_proof=self.proof("missing"))
        with self.assertRaises(CapitalBlocked):
            l.release_terminal_reservation("fake", "missing", when=T)
        self.assertEqual(l.snapshot()["realized_net_pnl"], "0.00")

    def test_invalid_instruments_and_rejected_exposure(self):
        l = self.ledger
        for asset, sym, q in [
            ("stock", "SOFI", ".5"), ("option", "SOFI261030C00015000", ".1"),
            ("crypto", "BTC/USD", ".000000001"), ("option", "SOFI", 1),
            ("short", "SOFI", 1),
        ]:
            with self.subTest(asset=asset, symbol=sym):
                with self.assertRaises(CapitalBlocked):
                    l.reserve_buy("bad", asset, sym, q, 1, 0, when=T)
        for limit in ["Infinity", "NaN", "-1", 0, 31]:
            with self.subTest(limit=limit):
                with self.assertRaises(CapitalBlocked):
                    l.reserve_buy("bad", "stock", "F", 1, limit, 0, when=T)
        with self.assertRaises(CapitalBlocked):
            l.reserve_buy("bad", "stock", "F", 1, 1, 0, when=datetime(2026,10,26))

    def test_policy_cannot_be_silently_reset(self):
        with self.assertRaises(CapitalBlocked):
            PaperCapital(self.path, opening_cash="1000")
        with self.assertRaises(CapitalBlocked):
            PaperCapital(self.path, maximum_order_debit="40")

    def test_sqlite_storage_refuses_symlink(self):
        target = Path(self.tmp.name) / "not-ledger"
        target.write_text("safe")
        link = Path(self.tmp.name) / "symlink-ledger"
        link.symlink_to(target)
        with self.assertRaises(CapitalBlocked):
            PaperCapital(str(link))


if __name__ == "__main__":
    unittest.main()
