import ast
import json
from pathlib import Path
import tempfile
import unittest

from zerocost_bot.alpaca_trade_updates import (
    TradeUpdateError,
    TradeUpdateJournal,
    parse_binary_frame,
)


def frame(event="fill", status="filled", filled_qty="2", timestamp="2026-11-03T14:31:05Z"):
    return json.dumps({
        "stream": "trade_updates",
        "data": {
            "event": event,
            "timestamp": timestamp,
            "order": {
                "id": "fixture-order-1",
                "client_order_id": "sf-paper-fixture-1",
                "status": status,
                "filled_qty": filled_qty,
                "updated_at": timestamp,
            },
        },
    }, separators=(",", ":")).encode()


class AlpacaTradeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tempdir.name) / "updates.sqlite3")
        self.journal = TradeUpdateJournal(self.path)

    def tearDown(self):
        self.journal.close()
        self.tempdir.cleanup()

    def test_binary_fill_is_observed_but_never_broker_confirmed(self):
        parsed = parse_binary_frame(frame())
        self.assertEqual(parsed["event"], "fill")
        result = self.journal.ingest_frame(frame())
        state = self.journal.order_state("fixture-order-1")
        self.assertEqual(result["result"], "OBSERVED_PENDING_GET")
        self.assertFalse(result["broker_confirmed"])
        self.assertEqual(state["observed_state"], "OBSERVED_FILL_PENDING_GET")
        self.assertEqual(state["reconciliation_state"], "GET_REQUIRED")
        self.assertFalse(state["broker_confirmed"])

    def test_rejects_text_malformed_and_wrong_stream_frames(self):
        for bad in (
            frame().decode(), b"\xff", b"{}",
            json.dumps({"stream": "authorization", "data": {}}).encode(),
        ):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(TradeUpdateError):
                    parse_binary_frame(bad)

    def test_reconnect_replay_is_durable_and_idempotent(self):
        first = self.journal.ingest_frame(frame())
        duplicate = self.journal.ingest_frame(frame())
        self.assertEqual(first["result"], "OBSERVED_PENDING_GET")
        self.assertEqual(duplicate["result"], "DUPLICATE_IGNORED")
        self.assertEqual(self.journal.event_count(), 1)
        self.journal.close()
        self.journal = TradeUpdateJournal(self.path)
        self.assertEqual(
            self.journal.ingest_frame(frame())["result"], "DUPLICATE_IGNORED"
        )
        self.assertEqual(self.journal.event_count(), 1)

    def test_conflicting_same_event_identity_halts_to_unknown(self):
        self.journal.ingest_frame(frame(filled_qty="1"))
        result = self.journal.ingest_frame(frame(filled_qty="2"))
        state = self.journal.order_state("fixture-order-1")
        self.assertEqual(result["result"], "CONFLICT_UNKNOWN")
        self.assertEqual(state["observed_state"], "UNKNOWN_REQUIRES_GET")

    def test_out_of_order_event_never_regresses_latest_observation(self):
        self.journal.ingest_frame(frame(timestamp="2026-11-03T14:32:00Z"))
        result = self.journal.ingest_frame(
            frame(event="partial_fill", status="partially_filled", filled_qty="1",
                  timestamp="2026-11-03T14:31:00Z")
        )
        state = self.journal.order_state("fixture-order-1")
        self.assertEqual(result["result"], "OUT_OF_ORDER_IGNORED")
        self.assertEqual(state["observed_state"], "OBSERVED_FILL_PENDING_GET")
        self.assertEqual(self.journal.event_count(), 2)

    def test_missing_stream_marks_unknown_and_duplicate_replay_cannot_clear_it(self):
        self.journal.ingest_frame(frame())
        gap = self.journal.mark_stream_gap(
            "reconnect without complete replay", "2026-11-03T14:32:00Z"
        )
        self.assertEqual(gap["result"], "STREAM_GAP_UNKNOWN")
        self.assertEqual(
            self.journal.order_state("fixture-order-1")["observed_state"],
            "UNKNOWN_REQUIRES_GET",
        )
        self.assertEqual(
            self.journal.ingest_frame(frame())["result"], "DUPLICATE_IGNORED"
        )
        self.assertEqual(
            self.journal.order_state("fixture-order-1")["observed_state"],
            "UNKNOWN_REQUIRES_GET",
        )

    def test_module_has_no_network_or_order_submission_path(self):
        source_path = Path(__file__).parents[1] / "zerocost_bot" / "alpaca_trade_updates.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (node.names if isinstance(node, ast.Import) else
                          [ast.alias(name=node.module or "")])
        }
        self.assertTrue({"socket", "urllib", "requests", "websockets"}.isdisjoint(imports))
        self.assertNotIn("paper-api.alpaca.markets", source)
        self.assertNotIn('"POST"', source)


if __name__ == "__main__":
    unittest.main()
