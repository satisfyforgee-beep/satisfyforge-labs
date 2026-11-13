import tempfile
import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal as D
from pathlib import Path

from option_expiration import (
    ExpiryObservation, OptionExpiryJournal, OptionExpiryTerms,
    reconcile_expiration,
)


EXPIRY = date(2026, 11, 13)
NEXT_DAY = datetime(2026, 11, 14, 14, tzinfo=timezone.utc)
CALL = OptionExpiryTerms("ADJ261113C00014500", "ADJ", "call", EXPIRY,
                         D("1"), D("50"), D("-725"))
PUT = OptionExpiryTerms("ADJ261113P00014500", "ADJ", "put", EXPIRY,
                        D("1"), D("-50"), D("725"))


def activity(kind="exercise", symbol=CALL.symbol, activity_id="nta-1",
             observed_at=NEXT_DAY):
    return {
        "activity_id": activity_id,
        "kind": kind,
        "symbol": symbol,
        "quantity": "1",
        "effective_at": "2026-11-13T21:00:00+00:00",
        "observed_at": observed_at,
    }


def observation(**updates):
    values = {
        "observation_id": "obs-1",
        "as_of": NEXT_DAY,
        "account_checked_at": NEXT_DAY,
        "positions_checked_at": NEXT_DAY,
        "activity_checked_at": NEXT_DAY,
        "option_position_quantity": D("0"),
        "underlying_quantity_delta": D("50"),
        "cash_delta": D("-725"),
        "cash_before_expiry": D("1000"),
        "underlying_before_expiry": D("0"),
        "activities": (activity(),),
    }
    values.update(updates)
    return ExpiryObservation(**values)


class OptionExpirationTests(unittest.TestCase):
    def test_adjusted_call_exercise_requires_independent_matching_deltas(self):
        result = reconcile_expiration(CALL, observation())
        self.assertEqual(result["status"], "CONFIRMED_EXERCISED")
        self.assertTrue(result["final"])
        self.assertIn("no fill, order", result["warning"])

    def test_adjusted_put_requires_underlying_and_matches_credit(self):
        obs = observation(
            underlying_quantity_delta=D("-50"), cash_delta=D("725"),
            cash_before_expiry=D("0"), underlying_before_expiry=D("50"),
            activities=(activity(symbol=PUT.symbol),))
        self.assertEqual(reconcile_expiration(PUT, obs)["status"],
                         "CONFIRMED_EXERCISED")
        insufficient = replace(obs, underlying_before_expiry=D("49"))
        self.assertEqual(reconcile_expiration(PUT, insufficient)["status"],
                         "PENDING_UNDERLYING_INSUFFICIENT")

    def test_next_day_activity_not_websocket_absence_confirms_state(self):
        no_activity = observation(activities=())
        self.assertEqual(reconcile_expiration(CALL, no_activity)["status"],
                         "PENDING_ACTIVITY_READBACK")
        same_day = datetime(2026, 11, 13, 22, tzinfo=timezone.utc)
        early = observation(as_of=same_day, account_checked_at=same_day,
                            positions_checked_at=same_day,
                            activity_checked_at=same_day, activities=())
        self.assertEqual(reconcile_expiration(CALL, early)["status"],
                         "PENDING_NOT_EXPIRED")

    def test_future_activity_never_leaks_backward(self):
        cutoff = datetime(2026, 11, 14, 13, tzinfo=timezone.utc)
        obs = observation(
            as_of=cutoff, account_checked_at=cutoff,
            positions_checked_at=cutoff, activity_checked_at=cutoff,
            activities=(activity(observed_at=NEXT_DAY),))
        self.assertEqual(reconcile_expiration(CALL, obs)["status"],
                         "PENDING_ACTIVITY_READBACK")

    def test_cash_insufficient_or_delta_mismatch_never_finalizes(self):
        self.assertEqual(reconcile_expiration(
            CALL, observation(cash_before_expiry=D("724")))["status"],
            "PENDING_CASH_INSUFFICIENT")
        self.assertEqual(reconcile_expiration(
            CALL, observation(cash_delta=D("-700")))["status"],
            "PENDING_STATE_MISMATCH")

    def test_expiration_requires_zero_independent_deltas(self):
        expired = observation(
            underlying_quantity_delta=D("0"), cash_delta=D("0"),
            activities=(activity(kind="expiration"),))
        self.assertEqual(reconcile_expiration(CALL, expired)["status"],
                         "CONFIRMED_EXPIRED")
        mismatch = replace(expired, cash_delta=D("1"))
        self.assertEqual(reconcile_expiration(CALL, mismatch)["status"],
                         "PENDING_STATE_MISMATCH")

    def test_missing_account_state_remains_pending(self):
        incomplete = observation(account_checked_at=None)
        self.assertEqual(reconcile_expiration(CALL, incomplete)["status"],
                         "PENDING_INCOMPLETE_READBACK")
        unknown = observation(cash_delta=None)
        self.assertEqual(reconcile_expiration(CALL, unknown)["status"],
                         "PENDING_UNKNOWN_ACCOUNT_STATE")

    def test_duplicate_activities_are_idempotent_but_conflicts_fail(self):
        row = activity()
        duplicate = observation(activities=(row, dict(row)))
        self.assertEqual(reconcile_expiration(CALL, duplicate)["status"],
                         "CONFIRMED_EXERCISED")
        conflict = dict(row, kind="expiration")
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            reconcile_expiration(CALL, observation(activities=(row, conflict)))

    def test_journal_is_atomic_and_observation_id_is_durable(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = OptionExpiryJournal(Path(tmp) / "paper.sqlite3")
            first = journal.record(CALL, observation())
            second = journal.record(CALL, observation())
            self.assertEqual(first, second)
            self.assertEqual(len(journal.records()), 1)
            with self.assertRaisesRegex(ValueError, "reused"):
                journal.record(CALL, observation(cash_delta=D("-700")))


if __name__ == "__main__":
    unittest.main()
