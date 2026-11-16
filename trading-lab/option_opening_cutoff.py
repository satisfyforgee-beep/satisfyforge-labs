"""Offline expiration-day option opening cutoff classifier.

This module is a pure preflight.  It does not connect to a provider, create an
order, or claim that a close, liquidation, exercise, or assignment occurred.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


NEW_YORK = ZoneInfo("America/New_York")
ALPACA_0DTE_FAQ = (
    "https://docs.alpaca.markets/us/docs/options-expiration-0-dte-faq"
)


@dataclass(frozen=True)
class ExpirationOpeningPolicy:
    """Explicit, dated provider policy; refresh rather than silently assuming."""

    checked_on: date
    equity_option_cutoff_et: time = time(15, 15)
    broad_based_etf_option_cutoff_et: time = time(15, 30)
    source_url: str = ALPACA_0DTE_FAQ
    max_age_days: int = 7

    def __post_init__(self) -> None:
        if not isinstance(self.checked_on, date):
            raise ValueError("checked_on must be a provider-policy review date")
        if self.source_url != ALPACA_0DTE_FAQ:
            raise ValueError("Unverified expiration-day cutoff source")
        if type(self.max_age_days) is not int or self.max_age_days < 0:
            raise ValueError("max_age_days must be a nonnegative integer")
        for value in (self.equity_option_cutoff_et,
                      self.broad_based_etf_option_cutoff_et):
            if value.tzinfo is not None:
                raise ValueError("Cutoff times must be naive America/New_York wall times")


def classify_expiration_day_opening(
    *,
    intent: str,
    instrument_class: str,
    expiration: date,
    observed_at: datetime,
    session_date: date,
    regular_session_open: bool,
    policy: ExpirationOpeningPolicy,
    classification_verified: bool,
    standard_multiplier_verified: bool,
    exercise_funding_verified: bool,
) -> dict:
    """Classify one offline review without authorizing broker submission.

    ``opening_review_allowed`` means only that this specific cutoff gate passed.
    Every other account, quote, liquidity, idempotency, and exit gate remains
    independently required before any paper-broker adapter could be armed.
    """
    warning = (
        "Offline cutoff review only; no order, fill, close, liquidation, "
        "exercise, or assignment is inferred."
    )
    base = {
        "mode": "OFFLINE_EXPIRATION_DAY_OPENING_CUTOFF",
        "paper_only": True,
        "broker_submission_enabled": False,
        "opening_review_allowed": False,
        "warning": warning,
        "policy_source": policy.source_url,
        "policy_checked_on": policy.checked_on.isoformat(),
    }

    if (not isinstance(observed_at, datetime) or observed_at.tzinfo is None
            or observed_at.utcoffset() is None):
        return _result(base, "HALT_TIMESTAMP_UNVERIFIED",
                       "Timezone-aware observation required")
    try:
        observed_et = observed_at.astimezone(NEW_YORK)
    except (ValueError, OverflowError):
        return _result(base, "HALT_TIMESTAMP_UNVERIFIED",
                       "Observation cannot be normalized to America/New_York")
    base["observed_at_et"] = observed_et.isoformat()

    if intent not in {"open", "close"}:
        return _result(base, "HALT_INTENT_UNSUPPORTED",
                       "Only explicit open or close intent is supported")
    if instrument_class not in {
        "equity_option", "broad_based_etf_option"
    } or not classification_verified:
        return _result(base, "HALT_INSTRUMENT_CLASS_UNVERIFIED",
                       "Verified equity-option or broad-ETF-option class required")
    if not standard_multiplier_verified:
        return _result(base, "HALT_CONTRACT_TERMS_UNVERIFIED",
                       "Standard contract multiplier must be independently verified")
    if observed_et.date() != session_date:
        return _result(base, "HALT_MARKET_CALENDAR_MISMATCH",
                       "Provider session date and America/New_York date disagree")
    policy_age = (observed_et.date() - policy.checked_on).days
    if policy_age < 0 or policy_age > policy.max_age_days:
        return _result(base, "HALT_PROVIDER_POLICY_STALE",
                       "Expiration-day cutoff policy is future-dated or stale")
    if expiration != session_date:
        return _result(base, "OUTSIDE_EXPIRATION_DAY_SCOPE",
                       "Contract does not expire in the reviewed session")
    if not regular_session_open:
        return _result(base, "HALT_REGULAR_SESSION_CLOSED",
                       "Expiration-day cutoff review requires an open regular session")

    cutoff = (policy.equity_option_cutoff_et
              if instrument_class == "equity_option"
              else policy.broad_based_etf_option_cutoff_et)
    base["opening_cutoff_et"] = cutoff.isoformat(timespec="minutes")

    if intent == "close":
        result = _result(
            base, "CLOSE_REVIEW_NOT_BLOCKED_BY_OPENING_CUTOFF",
            "Provider opening cutoff does not prohibit a verified closing order")
        result["close_review_allowed"] = True
        return result
    if observed_et.time().replace(tzinfo=None) >= cutoff:
        return _result(base, "HALT_EXPIRATION_DAY_OPENING_CUTOFF",
                       "Opening intent is at or after the provider cutoff")
    if not exercise_funding_verified:
        return _result(base, "HALT_EXERCISE_CAPACITY_UNVERIFIED",
                       "Expiration deliverables cannot be supported by verified cash/shares")

    result = _result(base, "OPENING_CUTOFF_REVIEW_PASSED",
                     "Opening intent is before the dated provider cutoff")
    result["opening_review_allowed"] = True
    return result


def _result(base: dict, state: str, reason: str) -> dict:
    return {**base, "state": state, "reason": reason}
