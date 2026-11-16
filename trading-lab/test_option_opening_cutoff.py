import unittest
from datetime import date, datetime, timezone

from option_opening_cutoff import (
    ExpirationOpeningPolicy,
    classify_expiration_day_opening,
)


SESSION = date(2026, 11, 16)
POLICY = ExpirationOpeningPolicy(checked_on=SESSION)


def review(at, **updates):
    values = {
        "intent": "open",
        "instrument_class": "equity_option",
        "expiration": SESSION,
        "observed_at": at,
        "session_date": SESSION,
        "regular_session_open": True,
        "policy": POLICY,
        "classification_verified": True,
        "standard_multiplier_verified": True,
        "exercise_funding_verified": True,
    }
    values.update(updates)
    return classify_expiration_day_opening(**values)


class ExpirationDayOpeningCutoffTests(unittest.TestCase):
    def test_equity_open_is_allowed_before_but_not_at_cutoff(self):
        before = review(datetime(2026, 11, 16, 20, 14, 59,
                                 tzinfo=timezone.utc))
        at = review(datetime(2026, 11, 16, 20, 15,
                             tzinfo=timezone.utc))
        self.assertEqual(before["state"], "OPENING_CUTOFF_REVIEW_PASSED")
        self.assertTrue(before["opening_review_allowed"])
        self.assertEqual(at["state"], "HALT_EXPIRATION_DAY_OPENING_CUTOFF")
        self.assertFalse(at["opening_review_allowed"])
        self.assertFalse(at["broker_submission_enabled"])

    def test_broad_etf_uses_later_boundary(self):
        before = review(
            datetime(2026, 11, 16, 20, 29, 59, tzinfo=timezone.utc),
            instrument_class="broad_based_etf_option")
        at = review(
            datetime(2026, 11, 16, 20, 30, tzinfo=timezone.utc),
            instrument_class="broad_based_etf_option")
        self.assertEqual(before["state"], "OPENING_CUTOFF_REVIEW_PASSED")
        self.assertEqual(at["state"], "HALT_EXPIRATION_DAY_OPENING_CUTOFF")

    def test_dst_conversion_uses_new_york_wall_time(self):
        summer = date(2026, 7, 17)
        policy = ExpirationOpeningPolicy(checked_on=summer)
        before = review(
            datetime(2026, 7, 17, 19, 14, 59, tzinfo=timezone.utc),
            expiration=summer, session_date=summer, policy=policy)
        at = review(
            datetime(2026, 7, 17, 19, 15, tzinfo=timezone.utc),
            expiration=summer, session_date=summer, policy=policy)
        self.assertEqual(before["state"], "OPENING_CUTOFF_REVIEW_PASSED")
        self.assertEqual(at["state"], "HALT_EXPIRATION_DAY_OPENING_CUTOFF")

    def test_close_is_distinguished_but_never_submitted(self):
        result = review(datetime(2026, 11, 16, 20, 45,
                                 tzinfo=timezone.utc), intent="close")
        self.assertEqual(
            result["state"],
            "CLOSE_REVIEW_NOT_BLOCKED_BY_OPENING_CUTOFF")
        self.assertTrue(result["close_review_allowed"])
        self.assertFalse(result["broker_submission_enabled"])
        self.assertIn("no order", result["warning"].lower())

    def test_unknown_class_or_contract_terms_fail_closed(self):
        now = datetime(2026, 11, 16, 19, tzinfo=timezone.utc)
        cases = [
            ({"instrument_class": "index_option"},
             "HALT_INSTRUMENT_CLASS_UNVERIFIED"),
            ({"classification_verified": False},
             "HALT_INSTRUMENT_CLASS_UNVERIFIED"),
            ({"standard_multiplier_verified": False},
             "HALT_CONTRACT_TERMS_UNVERIFIED"),
            ({"exercise_funding_verified": False},
             "HALT_EXERCISE_CAPACITY_UNVERIFIED"),
        ]
        for updates, state in cases:
            with self.subTest(state=state):
                self.assertEqual(review(now, **updates)["state"], state)

    def test_closed_or_mismatched_session_fails_closed(self):
        now = datetime(2026, 11, 16, 19, tzinfo=timezone.utc)
        self.assertEqual(
            review(now, regular_session_open=False)["state"],
            "HALT_REGULAR_SESSION_CLOSED")
        self.assertEqual(
            review(now, session_date=date(2026, 11, 13))["state"],
            "HALT_MARKET_CALENDAR_MISMATCH")

    def test_stale_future_or_unzoned_policy_evidence_fails_closed(self):
        now = datetime(2026, 11, 16, 19, tzinfo=timezone.utc)
        stale = ExpirationOpeningPolicy(checked_on=date(2026, 11, 8))
        future = ExpirationOpeningPolicy(checked_on=date(2026, 11, 17))
        self.assertEqual(review(now, policy=stale)["state"],
                         "HALT_PROVIDER_POLICY_STALE")
        self.assertEqual(review(now, policy=future)["state"],
                         "HALT_PROVIDER_POLICY_STALE")
        self.assertEqual(
            review(datetime(2026, 11, 16, 14, 0))["state"],
            "HALT_TIMESTAMP_UNVERIFIED")

    def test_non_expiration_day_does_not_authorize_an_order(self):
        result = review(
            datetime(2026, 11, 16, 19, tzinfo=timezone.utc),
            expiration=date(2026, 11, 20))
        self.assertEqual(result["state"], "OUTSIDE_EXPIRATION_DAY_SCOPE")
        self.assertFalse(result["opening_review_allowed"])
        self.assertFalse(result["broker_submission_enabled"])


if __name__ == "__main__":
    unittest.main()
