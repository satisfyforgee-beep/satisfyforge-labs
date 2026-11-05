import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from zerocost_bot.engine import Bar, Settings
from zerocost_bot.evaluation import (
    evaluate_holdout, replay_corporate_actions_as_of,
)


BASE = datetime(2026, 10, 19, 13, 30, tzinfo=timezone.utc)


def sample(n=100):
    return [Bar("DEMO", BASE + timedelta(minutes=i), 10 + i / 100,
                10.01 + i / 100, 9.99 + i / 100, 10 + i / 100, 5000)
            for i in range(n)]


class HistoricalHoldoutTests(unittest.TestCase):
    def test_deterministic_untuned_split_and_metrics(self):
        a = evaluate_holdout(sample())
        b = evaluate_holdout(sample())
        self.assertEqual(a, b)
        self.assertEqual(a["mode"], "OFFLINE_HISTORICAL_HOLDOUT")
        self.assertEqual(a["train"]["bars"], 70)
        self.assertEqual(a["holdout"]["bars"], 30)
        self.assertEqual(a["holdout"]["strategy"]["start_cash"], 1000)
        self.assertIn("max_mark_to_market_drawdown_pct", a["holdout"])
        self.assertTrue(a["paper_only"])

    def test_bad_and_insufficient_data_fails_closed(self):
        with self.assertRaises(ValueError):
            evaluate_holdout(sample(20))
        with self.assertRaises(ValueError):
            evaluate_holdout(sample(), train_fraction=.91)
        rows = sample()
        rows[-1] = replace(rows[-1], time=rows[-2].time)
        with self.assertRaisesRegex(ValueError, "nonduplicated"):
            evaluate_holdout(rows)
        rows = sample()
        rows[5] = replace(rows[5], symbol="OTHER")
        with self.assertRaisesRegex(ValueError, "single instrument"):
            evaluate_holdout(rows)
        rows = sample()
        rows[5] = replace(rows[5], close=float("nan"))
        with self.assertRaises(ValueError):
            evaluate_holdout(rows)

    def test_fixed_settings_are_not_modified(self):
        settings = Settings(start_cash=500, fee_per_order=1.25)
        original = settings.__dict__.copy()
        evaluate_holdout(sample(), settings)
        self.assertEqual(settings.__dict__, original)


def action(action_id="split-1", *, revision=1, quality="complete"):
    return {
        "id": action_id,
        "type": "forward_split",
        "symbol": "DEMO",
        "process_date": "2026-10-18",
        "record_quality": quality,
        "revision": revision,
    }


def page(snapshot_id, observed_at, *, token=None, next_token=None,
         actions=None, data_quality="all"):
    return {
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "page_token": token,
        "next_page_token": next_token,
        "data_quality": data_quality,
        "actions": list(actions or []),
    }


class CorporateActionReplayTests(unittest.TestCase):
    def test_exhausts_exact_page_chain_without_duplicate_events(self):
        observed = "2026-10-19T13:00:00+00:00"
        pages = [
            page("snapshot-a", observed, next_token="page-2",
                 actions=[action("split-1")]),
            page("snapshot-a", observed, token="page-2",
                 actions=[action("dividend-1")]),
        ]
        result = replay_corporate_actions_as_of(
            pages, as_of=datetime(2026, 10, 19, 13, 5, tzinfo=timezone.utc))
        self.assertEqual(result["pages_exhausted"], 2)
        self.assertEqual([x["id"] for x in result["actions"]],
                         ["dividend-1", "split-1"])
        self.assertTrue(all(x["known_at_utc"] == observed
                            for x in result["actions"]))

    def test_truncated_cycle_or_duplicate_event_fails_closed(self):
        observed = "2026-10-19T13:00:00+00:00"
        bad_sets = [
            [page("s", observed, next_token="missing")],
            [page("s", observed, next_token="p2"),
             page("s", observed, token="p2", next_token="p2")],
            [page("s", observed, actions=[action("same"), action("same")])],
        ]
        for pages in bad_sets:
            with self.subTest(pages=pages):
                with self.assertRaises(ValueError):
                    replay_corporate_actions_as_of(
                        pages,
                        as_of=datetime(2026, 10, 19, 13, 5,
                                       tzinfo=timezone.utc))

    def test_incomplete_records_are_explicitly_excluded(self):
        result = replay_corporate_actions_as_of([
            page("snapshot-all", "2026-10-19T13:00:00+00:00",
                 actions=[action("complete"),
                          action("early", quality="incomplete")]),
        ], as_of=datetime(2026, 10, 19, 13, 1, tzinfo=timezone.utc))
        self.assertEqual([x["id"] for x in result["actions"]], ["complete"])
        self.assertEqual(result["excluded_incomplete_ids"], ["early"])
        with self.assertRaisesRegex(ValueError, "Complete snapshot"):
            replay_corporate_actions_as_of([
                page("snapshot-complete", "2026-10-19T13:00:00+00:00",
                     data_quality="complete",
                     actions=[action("early", quality="incomplete")]),
            ], as_of=datetime(2026, 10, 19, 13, 1, tzinfo=timezone.utc))

    def test_later_availability_and_revision_do_not_leak_backward(self):
        pages = [
            page("early", "2026-10-19T12:00:00+00:00",
                 actions=[action(revision=1)]),
            page("late", "2026-10-20T12:00:00+00:00",
                 actions=[action(revision=2)]),
        ]
        early = replay_corporate_actions_as_of(
            pages, as_of=datetime(2026, 10, 19, 12, 1, tzinfo=timezone.utc))
        late = replay_corporate_actions_as_of(
            pages, as_of=datetime(2026, 10, 20, 12, 1, tzinfo=timezone.utc))
        self.assertEqual(early["actions"][0]["revision"], 1)
        self.assertEqual(late["actions"][0]["revision"], 2)
        self.assertEqual(early["snapshot_id"], "early")

    def test_missing_availability_or_future_only_capture_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "observed_at"):
            replay_corporate_actions_as_of([
                page("s", None, actions=[action()]),
            ], as_of=datetime(2026, 10, 19, 13, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, "existed by cutoff"):
            replay_corporate_actions_as_of([
                page("future", "2026-10-20T13:00:00+00:00",
                     actions=[action()]),
            ], as_of=datetime(2026, 10, 19, 13, tzinfo=timezone.utc))

    def test_holdout_freezes_audit_at_or_before_evaluation_start(self):
        pages = [page("before", "2026-10-19T13:00:00+00:00",
                      actions=[action()])]
        report = evaluate_holdout(
            sample(), corporate_action_pages=pages,
            corporate_action_as_of=datetime(2026, 10, 19, 13, 0,
                                             tzinfo=timezone.utc))
        self.assertEqual(report["corporate_action_audit"]["snapshot_id"],
                         "before")
        with self.assertRaisesRegex(ValueError, "evaluation start"):
            evaluate_holdout(
                sample(), corporate_action_pages=pages,
                corporate_action_as_of=BASE + timedelta(seconds=1))


if __name__ == "__main__":
    unittest.main()
