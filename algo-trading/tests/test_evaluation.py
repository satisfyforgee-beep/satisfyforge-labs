import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from zerocost_bot.engine import Bar, Settings
from zerocost_bot.evaluation import (
    evaluate_holdout, replay_corporate_actions_as_of,
    replay_stock_trades_as_of, validate_historical_option_provenance,
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


def stock_event(event_id, sequence, arrived_at, event_type="trade", **updates):
    values = {
        "event_id": event_id,
        "event_type": event_type,
        "capture_sequence": sequence,
        "arrived_at": arrived_at,
        "symbol": "DEMO",
    }
    if event_type == "trade":
        values.update({
            "trade_id": updates.pop("trade_id", "trade-1"),
            "price": updates.pop("price", "10.00"),
            "size": updates.pop("size", "100"),
            "conditions": updates.pop("conditions", ["@"]),
            "exchange_time": updates.pop("exchange_time",
                                         "2026-10-19T13:30:00Z"),
        })
    values.update(updates)
    return values


class StockTradeCorrectionReplayTests(unittest.TestCase):
    cutoff = datetime(2026, 10, 19, 13, 35, tzinfo=timezone.utc)

    def test_correction_replaces_original_only_after_local_arrival(self):
        events = [
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z"),
            stock_event("capture-2", 2, "2026-10-19T13:34:00Z",
                        "correction", original_id="trade-1",
                        corrected_id="trade-2", corrected_price="9.95",
                        corrected_size="80", corrected_conditions=["C"]),
        ]
        before = replay_stock_trades_as_of(
            events, symbol="DEMO",
            as_of=datetime(2026, 10, 19, 13, 33, tzinfo=timezone.utc))
        after = replay_stock_trades_as_of(events, symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(before["trades"][0]["trade_id"], "trade-1")
        self.assertEqual(before["trades"][0]["price"], "10.00")
        self.assertEqual(after["trades"][0]["trade_id"], "trade-2")
        self.assertEqual(after["trades"][0]["price"], "9.95")
        self.assertEqual(after["superseded_trade_ids"], ["trade-1"])

    def test_cancel_error_removes_trade_only_after_arrival(self):
        events = [
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z"),
            stock_event("capture-2", 2, "2026-10-19T13:34:00Z",
                        "cancel_error", original_id="trade-1"),
        ]
        result = replay_stock_trades_as_of(events, symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(result["trades"], [])
        self.assertEqual(result["cancelled_trade_ids"], ["trade-1"])

    def test_input_order_does_not_override_arrival_sequence(self):
        correction = stock_event(
            "capture-2", 2, "2026-10-19T13:34:00Z", "correction",
            original_id="trade-1", corrected_id="trade-2",
            corrected_price="10.25", corrected_size="100",
            corrected_conditions=["C"])
        original = stock_event("capture-1", 1, "2026-10-19T13:30:01Z")
        result = replay_stock_trades_as_of(
            [correction, original], symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(result["trades"][0]["trade_id"], "trade-2")

    def test_exact_duplicate_capture_is_idempotent(self):
        original = stock_event("capture-1", 1, "2026-10-19T13:30:01Z")
        result = replay_stock_trades_as_of(
            [original, dict(original)], symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(result["events_applied"], 1)
        self.assertEqual(len(result["trades"]), 1)

    def test_conflicting_duplicate_or_duplicate_sequence_fails_closed(self):
        original = stock_event("capture-1", 1, "2026-10-19T13:30:01Z")
        conflict = dict(original, price="11.00")
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            replay_stock_trades_as_of(
                [original, conflict], symbol="DEMO", as_of=self.cutoff)
        with self.assertRaisesRegex(ValueError, "capture sequence"):
            replay_stock_trades_as_of([
                original,
                stock_event("capture-2", 1, "2026-10-19T13:31:01Z",
                            trade_id="trade-2"),
            ], symbol="DEMO", as_of=self.cutoff)

    def test_unknown_or_cross_symbol_reference_fails_closed(self):
        correction = stock_event(
            "capture-2", 2, "2026-10-19T13:34:00Z", "correction",
            original_id="missing", corrected_id="trade-2",
            corrected_price="10.25", corrected_size="100",
            corrected_conditions=["C"])
        with self.assertRaisesRegex(ValueError, "Unknown"):
            replay_stock_trades_as_of([correction], symbol="DEMO", as_of=self.cutoff)
        with self.assertRaisesRegex(ValueError, "Cross-symbol"):
            replay_stock_trades_as_of([
                stock_event("capture-1", 1, "2026-10-19T13:30:01Z",
                            symbol="OTHER"),
            ], symbol="DEMO", as_of=self.cutoff)

    def test_future_event_never_leaks_backward(self):
        events = [
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z"),
            stock_event("capture-2", 2, "2026-10-20T13:30:01Z",
                        "cancel_error", original_id="trade-1"),
        ]
        result = replay_stock_trades_as_of(events, symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(result["events_applied"], 1)
        self.assertEqual(result["trades"][0]["trade_id"], "trade-1")

    def test_unreliable_provenance_and_prices_fail_closed(self):
        invalid = [
            stock_event("capture-1", 1, None),
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z", price=10.0),
            stock_event("capture-1", 1, "2026-10-19T13:29:00Z"),
        ]
        for event in invalid:
            with self.subTest(event=event):
                with self.assertRaises(ValueError):
                    replay_stock_trades_as_of(
                        [event], symbol="DEMO", as_of=self.cutoff)

    def test_result_is_explicitly_not_execution_evidence(self):
        result = replay_stock_trades_as_of([
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z"),
        ], symbol="DEMO", as_of=self.cutoff)
        self.assertIn("not bar, signal, quote, fill, or order", result["warning"])
        self.assertEqual(result["mode"],
                         "OFFLINE_POINT_IN_TIME_STOCK_TRADE_REPLAY")


def option_history_metadata(**updates):
    values = {
        "provider": "alpaca",
        "asset_class": "option",
        "data_type": "quotes",
        "feed": "indicative",
        "source_provenance": "derived_indicative",
        "window_start": "2026-11-10T14:30:00Z",
        "window_end": "2026-11-10T20:00:00Z",
        "captured_at": "2026-11-11T12:00:00Z",
        "delay_minutes": 0,
        "opra_entitlement_verified": False,
        "execution_evidence": False,
    }
    values.update(updates)
    return values


class HistoricalOptionProvenanceTests(unittest.TestCase):
    def test_accepts_explicit_indicative_quote_as_research_only(self):
        result = validate_historical_option_provenance(
            option_history_metadata())
        self.assertEqual(result["feed"], "indicative")
        self.assertTrue(result["research_only"])
        self.assertFalse(result["execution_evidence"])
        self.assertIn("not quote, fill, or order", result["warning"])

    def test_accepts_documented_indicative_trade_delay(self):
        result = validate_historical_option_provenance(
            option_history_metadata(data_type="trades", delay_minutes=15))
        self.assertEqual(result["delay_minutes"], 15)

    def test_rejects_pre_coverage_and_impossible_windows(self):
        invalid = [
            option_history_metadata(window_start="2024-01-31T23:59:59Z"),
            option_history_metadata(window_end="2026-11-10T14:30:00Z"),
            option_history_metadata(captured_at="2026-11-10T19:00:00Z"),
        ]
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    validate_historical_option_provenance(metadata)

    def test_rejects_unknown_or_conflicting_feed_provenance(self):
        invalid = [
            option_history_metadata(feed="unknown"),
            option_history_metadata(source_provenance="opra"),
            option_history_metadata(provider="other"),
        ]
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    validate_historical_option_provenance(metadata)

    def test_rejects_delayed_trade_claimed_as_contemporaneous(self):
        with self.assertRaisesRegex(ValueError, "preserve delay"):
            validate_historical_option_provenance(
                option_history_metadata(data_type="trades", delay_minutes=0))

    def test_requires_verified_entitlement_for_opra(self):
        with self.assertRaisesRegex(ValueError, "entitlement"):
            validate_historical_option_provenance(option_history_metadata(
                feed="opra", source_provenance="opra", delay_minutes=0))
        result = validate_historical_option_provenance(option_history_metadata(
            feed="opra", source_provenance="opra", delay_minutes=0,
            opra_entitlement_verified=True))
        self.assertTrue(result["opra_entitlement_verified"])

    def test_rejects_execution_claim_and_unknown_delay(self):
        invalid = [
            option_history_metadata(execution_evidence=True),
            option_history_metadata(delay_minutes=None),
            option_history_metadata(opra_entitlement_verified=None),
        ]
        for metadata in invalid:
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    validate_historical_option_provenance(metadata)

    def test_requires_timezone_aware_capture_provenance(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            validate_historical_option_provenance(
                option_history_metadata(captured_at="2026-11-11T12:00:00"))


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
