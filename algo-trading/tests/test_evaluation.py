import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from zerocost_bot.engine import Bar, Settings
from zerocost_bot.evaluation import (
    classify_stock_trade_bar_updates, evaluate_holdout,
    replay_corporate_actions_as_of,
    replay_crypto_quotes_as_of,
    replay_stock_bars_as_of, replay_stock_trades_as_of,
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


def captured_bar(bar, **changes):
    values = {
        "symbol": bar.symbol,
        "time": bar.time.isoformat(),
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }
    values.update(changes)
    return values


def bar_page(snapshot_id, observed_at, bars, *, token=None, next_token=None,
             adjustment="raw", symbol_asof="2026-10-19"):
    return {
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "source": "ALPACA_STOCK_BARS",
        "feed": "iex",
        "symbol": "DEMO",
        "adjustment": adjustment,
        "symbol_asof": symbol_asof,
        "timeframe": "1Min",
        "page_token": token,
        "next_page_token": next_token,
        "bars": list(bars),
    }


class StockBarPointInTimeTests(unittest.TestCase):
    cutoff = datetime(2026, 10, 19, 15, 25, tzinfo=timezone.utc)

    def test_complete_pagination_and_explicit_query_provenance(self):
        rows = sample(4)
        pages = [
            bar_page("snapshot-a", "2026-10-19T15:20:00Z",
                     [captured_bar(x) for x in rows[:2]], next_token="p2",
                     adjustment="split"),
            bar_page("snapshot-a", "2026-10-19T15:20:00Z",
                     [captured_bar(x) for x in rows[2:]], token="p2",
                     adjustment="split"),
        ]
        result = replay_stock_bars_as_of(
            pages, as_of=self.cutoff, symbol="DEMO", adjustment="split",
            symbol_asof="2026-10-19")
        self.assertEqual(result["pages_exhausted"], 2)
        self.assertEqual(result["bars"], 4)
        self.assertEqual(result["adjustment"], "split")
        self.assertEqual(result["symbol_asof"], "2026-10-19")
        self.assertEqual(len(result["content_sha256"]), 64)

    def test_later_revised_snapshot_never_leaks_backward(self):
        row = sample(1)[0]
        pages = [
            bar_page("early", "2026-10-19T15:20:00Z",
                     [captured_bar(row)]),
            bar_page("late", "2026-10-20T13:20:00Z",
                     [captured_bar(row, close=99)]),
        ]
        result = replay_stock_bars_as_of(
            pages, as_of=self.cutoff, symbol="DEMO", adjustment="raw",
            symbol_asof="2026-10-19")
        self.assertEqual(result["snapshot_id"], "early")

    def test_unknown_adjustment_asof_or_incomplete_pages_fail_closed(self):
        row = captured_bar(sample(1)[0])
        valid = [bar_page("s", "2026-10-19T15:20:00Z", [row])]
        with self.assertRaisesRegex(ValueError, "adjustment"):
            replay_stock_bars_as_of(
                valid, as_of=self.cutoff, symbol="DEMO", adjustment="unknown",
                symbol_asof="2026-10-19")
        with self.assertRaisesRegex(ValueError, "as-of"):
            replay_stock_bars_as_of(
                valid, as_of=self.cutoff, symbol="DEMO", adjustment="raw",
                symbol_asof="current")
        with self.assertRaisesRegex(ValueError, "truncated"):
            replay_stock_bars_as_of(
                [bar_page("s", "2026-10-19T15:20:00Z", [row],
                          next_token="missing")],
                as_of=self.cutoff, symbol="DEMO", adjustment="raw",
                symbol_asof="2026-10-19")

    def test_holdout_requires_exact_audited_bar_content(self):
        rows = sample()
        pages = [bar_page(
            "exact", "2026-10-19T15:20:00Z",
            [captured_bar(row) for row in rows])]
        report = evaluate_holdout(
            rows, stock_bar_pages=pages, stock_bar_as_of=self.cutoff,
            stock_bar_adjustment="raw", stock_bar_symbol_asof="2026-10-19")
        self.assertEqual(report["stock_bar_audit"]["snapshot_id"], "exact")
        changed = list(rows)
        changed[-1] = replace(changed[-1], close=changed[-1].close + 0.01,
                              high=changed[-1].high + 0.01)
        with self.assertRaisesRegex(ValueError, "do not match"):
            evaluate_holdout(
                changed, stock_bar_pages=pages, stock_bar_as_of=self.cutoff,
                stock_bar_adjustment="raw",
                stock_bar_symbol_asof="2026-10-19")

    def test_holdout_rejects_future_or_partial_audit_configuration(self):
        rows = sample()
        pages = [bar_page(
            "exact", "2026-10-19T15:20:00Z",
            [captured_bar(row) for row in rows])]
        with self.assertRaisesRegex(ValueError, "supplied together"):
            evaluate_holdout(rows, stock_bar_pages=pages)
        with self.assertRaisesRegex(ValueError, "evaluation end"):
            evaluate_holdout(
                rows, stock_bar_pages=pages,
                stock_bar_as_of=rows[-1].time - timedelta(seconds=1),
                stock_bar_adjustment="raw",
                stock_bar_symbol_asof="2026-10-19")


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


class StockTradeConditionEligibilityTests(unittest.TestCase):
    cutoff = datetime(2026, 10, 19, 13, 35, tzinfo=timezone.utc)

    def test_regular_nasdaq_sale_updates_all_bar_components(self):
        result = classify_stock_trade_bar_updates(
            tape="C", bar_type="minute", conditions=["@"])
        self.assertEqual(result["open_close_update"], "ALWAYS")
        self.assertEqual(result["high_low_update"], "ALWAYS")
        self.assertEqual(result["volume_update"], "ALWAYS")
        self.assertTrue(result["can_seed_complete_bar"])
        self.assertFalse(result["execution_evidence"])
        self.assertFalse(result["fill_inference_allowed"])

    def test_odd_lot_is_volume_only_not_price_or_fill_evidence(self):
        result = classify_stock_trade_bar_updates(
            tape="C", bar_type="minute", conditions=["I"])
        self.assertTrue(result["volume_only"])
        self.assertEqual(result["open_close_update"], "NEVER")
        self.assertEqual(result["high_low_update"], "NEVER")
        self.assertFalse(result["can_seed_complete_bar"])
        self.assertFalse(result["fill_inference_allowed"])

    def test_prior_reference_differs_between_minute_and_daily_bars(self):
        minute = classify_stock_trade_bar_updates(
            tape="C", bar_type="minute", conditions=["P"])
        daily = classify_stock_trade_bar_updates(
            tape="C", bar_type="daily", conditions=["P"])
        self.assertTrue(minute["volume_only"])
        self.assertEqual(daily["open_close_update"], "FIRST_ONLY")
        self.assertEqual(daily["high_low_update"], "ALWAYS")
        self.assertTrue(daily["can_seed_complete_bar"])

    def test_multiple_conditions_apply_the_strictest_rule(self):
        odd_lot = classify_stock_trade_bar_updates(
            tape="C", bar_type="daily", conditions=["@", "4", "I"])
        derived = classify_stock_trade_bar_updates(
            tape="C", bar_type="daily", conditions=["@", "4"])
        self.assertTrue(odd_lot["volume_only"])
        self.assertEqual(derived["open_close_update"], "FIRST_ONLY")
        self.assertEqual(derived["high_low_update"], "ALWAYS")

    def test_unknown_duplicate_or_tape_conflicting_condition_fails_closed(self):
        cases = [
            {"tape": "C", "bar_type": "minute", "conditions": ["?"]},
            {"tape": "C", "bar_type": "minute", "conditions": ["I", "I"]},
            {"tape": "A", "bar_type": "minute", "conditions": ["@"]},
            {"tape": "O", "bar_type": "daily", "conditions": ["4"]},
        ]
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    classify_stock_trade_bar_updates(**values)

    def test_future_arrival_does_not_change_point_in_time_condition_audit(self):
        events = [
            stock_event("capture-1", 1, "2026-10-19T13:30:01Z"),
            stock_event("capture-2", 2, "2026-10-20T13:30:01Z",
                        trade_id="trade-2", conditions=["I"]),
        ]
        point_in_time = replay_stock_trades_as_of(
            events, symbol="DEMO", as_of=self.cutoff)
        self.assertEqual(len(point_in_time["trades"]), 1)
        result = classify_stock_trade_bar_updates(
            tape="C", bar_type="minute",
            conditions=point_in_time["trades"][0]["conditions"])
        self.assertFalse(result["volume_only"])


def crypto_quote(symbol, time, bid="100", ask="101"):
    return {
        "symbol": symbol,
        "time": time,
        "bid_price": bid,
        "bid_size": "0.5",
        "ask_price": ask,
        "ask_size": "0.6",
    }


def crypto_quote_page(snapshot_id, observed_at, quotes, *, token=None,
                      next_token=None, location="us-1",
                      symbols=("BTC/USD", "ETH/USD"),
                      start="2026-01-01T23:00:00Z",
                      end="2026-01-02T00:00:00Z",
                      entitlement="real_time"):
    return {
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "source": "ALPACA_CRYPTO_QUOTES",
        "location": location,
        "symbols": list(symbols),
        "start": start,
        "end": end,
        "entitlement": entitlement,
        "page_token": token,
        "next_page_token": next_token,
        "quotes": list(quotes),
    }


class CryptoQuotePointInTimeTests(unittest.TestCase):
    cutoff = datetime(2026, 1, 2, 0, 30, tzinfo=timezone.utc)
    start = datetime(2026, 1, 1, 23, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, 0, tzinfo=timezone.utc)

    def replay(self, pages, **changes):
        values = {
            "as_of": self.cutoff,
            "location": "us-1",
            "symbols": ["BTC/USD", "ETH/USD"],
            "start": self.start,
            "end": self.end,
        }
        values.update(changes)
        return replay_crypto_quotes_as_of(pages, **values)

    def test_exhausts_total_limit_pages_and_proves_symbol_coverage(self):
        pages = [
            crypto_quote_page(
                "capture-a", "2026-01-02T00:20:00Z",
                [crypto_quote("BTC/USD", "2026-01-01T23:30:00Z")],
                next_token="p2"),
            crypto_quote_page(
                "capture-a", "2026-01-02T00:20:00Z",
                [crypto_quote("ETH/USD", "2026-01-01T23:31:00Z",
                              bid="200", ask="201")], token="p2"),
        ]
        result = self.replay(pages)
        self.assertEqual(result["pages_exhausted"], 2)
        self.assertEqual(result["quotes_by_symbol"],
                         {"BTC/USD": 1, "ETH/USD": 1})
        self.assertEqual(result["location"], "us-1")
        self.assertEqual(len(result["content_sha256"]), 64)
        self.assertFalse(result["execution_evidence"])
        self.assertFalse(result["fill_inference_allowed"])

    def test_us1_coverage_location_and_symbols_are_explicit(self):
        pages = [crypto_quote_page(
            "capture-a", "2026-01-02T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ])]
        with self.assertRaisesRegex(ValueError, "predates us-1"):
            self.replay(
                pages,
                start=datetime(2025, 10, 13, tzinfo=timezone.utc))
        with self.assertRaisesRegex(ValueError, "provenance mismatch"):
            self.replay(pages, location="eu-1")
        with self.assertRaisesRegex(ValueError, "location"):
            self.replay(pages, location="unknown")
        with self.assertRaisesRegex(ValueError, "unique crypto symbols"):
            self.replay(pages, symbols=["BTC/USD", "BTC/USD"])

    def test_truncated_cycle_or_orphan_pagination_fails_closed(self):
        row = crypto_quote("BTC/USD", "2026-01-01T23:30:00Z")
        cases = [
            [crypto_quote_page("s", "2026-01-02T00:20:00Z", [row],
                               next_token="missing")],
            [crypto_quote_page("s", "2026-01-02T00:20:00Z", [row],
                               next_token="p2"),
             crypto_quote_page("s", "2026-01-02T00:20:00Z", [], token="p2",
                               next_token="p2")],
            [crypto_quote_page("s", "2026-01-02T00:20:00Z", [row]),
             crypto_quote_page("s", "2026-01-02T00:20:00Z", [], token="orphan")],
            [crypto_quote_page("s", "2026-01-02T00:20:00Z", [row],
                               next_token="p2"),
             crypto_quote_page("s", "2026-01-02T00:20:00Z", [], token="p2"),
             crypto_quote_page("s", "2026-01-02T00:20:00Z", [], token="p2")],
        ]
        for pages in cases:
            with self.subTest(pages=pages):
                with self.assertRaisesRegex(ValueError,
                                            "pagination|page token"):
                    self.replay(pages)

    def test_missing_symbol_duplicate_or_crossed_quote_fails_closed(self):
        missing = [crypto_quote_page(
            "s", "2026-01-02T00:20:00Z",
            [crypto_quote("BTC/USD", "2026-01-01T23:30:00Z")])]
        with self.assertRaisesRegex(ValueError, "missing requested symbols"):
            self.replay(missing)
        duplicate = [crypto_quote_page(
            "s", "2026-01-02T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z"),
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ])]
        with self.assertRaisesRegex(ValueError, "Duplicate crypto quote"):
            self.replay(duplicate)
        crossed = [crypto_quote_page(
            "s", "2026-01-02T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z",
                             bid="102", ask="101"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ])]
        with self.assertRaisesRegex(ValueError, "Crossed crypto quote"):
            self.replay(crossed)

    def test_entitlement_delay_and_future_quotes_fail_closed(self):
        delayed = [crypto_quote_page(
            "s", "2026-01-02T00:10:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ], entitlement="delayed_15m")]
        with self.assertRaisesRegex(ValueError, "delayed entitlement"):
            self.replay(delayed)
        unknown_entitlement = [crypto_quote_page(
            "s", "2026-01-02T00:20:00Z", [], entitlement="unknown")]
        with self.assertRaisesRegex(ValueError, "entitlement"):
            self.replay(unknown_entitlement)
        future = [crypto_quote_page(
            "s", "2026-01-02T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-02T00:01:00Z"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ])]
        with self.assertRaisesRegex(ValueError, "outside captured interval"):
            self.replay(future)

    def test_later_snapshot_never_leaks_backward(self):
        pages = [
            crypto_quote_page("early", "2026-01-02T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z"),
            ]),
            crypto_quote_page("late", "2026-01-03T00:20:00Z", [
                crypto_quote("BTC/USD", "2026-01-01T23:30:00Z",
                             bid="999", ask="1000"),
                crypto_quote("ETH/USD", "2026-01-01T23:31:00Z",
                             bid="999", ask="1000"),
            ]),
        ]
        result = self.replay(pages)
        self.assertEqual(result["snapshot_id"], "early")


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
