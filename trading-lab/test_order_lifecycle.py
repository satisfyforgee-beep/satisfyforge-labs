import unittest

from order_lifecycle import OrderLifecycleReconciler


def update(event, filled="0", execution_id=None, status=None):
    payload = {
        "event": event,
        "order": {
            "id": "order-1",
            "qty": "10",
            "filled_qty": filled,
            "status": status or event,
        },
    }
    if execution_id is not None:
        payload["execution_id"] = execution_id
    return payload


class OrderLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.reconciler = OrderLifecycleReconciler()

    def acknowledge(self):
        result = self.reconciler.acknowledge_streams(["trade_updates"])
        self.assertTrue(result["state_authoritative"])
        self.assertFalse(result["broker_submission_enabled"])

    def test_acknowledgement_is_required(self):
        halted = self.reconciler.apply_trade_update(update("new"), "new-1")
        self.assertEqual(halted["result"], "HALT_SUBSCRIPTION_UNVERIFIED")
        self.assertEqual(self.reconciler.orders, {})
        missing = self.reconciler.acknowledge_streams(["account_updates"])
        self.assertFalse(missing["state_authoritative"])

    def test_partial_fills_use_monotonic_cumulative_quantity_and_dedupe(self):
        self.acknowledge()
        first = self.reconciler.apply_trade_update(
            update("partial_fill", "3", "exec-1"))
        duplicate = self.reconciler.apply_trade_update(
            update("partial_fill", "3", "exec-1"))
        second = self.reconciler.apply_trade_update(
            update("partial_fill", "7", "exec-2"))
        filled = self.reconciler.apply_trade_update(
            update("fill", "10", "exec-3"))
        self.assertEqual(first["order"]["filled_quantity"], "3")
        self.assertEqual(duplicate["result"], "DUPLICATE_IGNORED")
        self.assertEqual(second["order"]["filled_quantity"], "7")
        self.assertTrue(filled["order"]["terminal"])

    def test_conflicting_execution_id_fails_closed(self):
        self.acknowledge()
        self.reconciler.apply_trade_update(update("partial_fill", "3", "same"))
        conflict = self.reconciler.apply_trade_update(update("partial_fill", "4", "same"))
        self.assertEqual(conflict["result"], "HALT_OBSERVATION_ID_CONFLICT")
        self.assertTrue(conflict["rest_readback_required"])
        self.assertEqual(conflict["order"]["filled_quantity"], "3")

    def test_out_of_order_fill_regression_requires_readback(self):
        self.acknowledge()
        self.reconciler.apply_trade_update(update("partial_fill", "6", "exec-1"))
        stale = self.reconciler.apply_trade_update(update("partial_fill", "2", "exec-2"))
        self.assertEqual(stale["result"], "HALT_CUMULATIVE_FILL_REGRESSION")
        self.assertFalse(stale["state_authoritative"])

    def test_pending_and_operation_rejection_are_not_terminal(self):
        self.acknowledge()
        pending = self.reconciler.apply_trade_update(update("pending_cancel"), "pending-1")
        self.assertFalse(pending["order"]["terminal"])
        rejected = self.reconciler.apply_trade_update(
            update("order_cancel_rejected"), "reject-1")
        self.assertEqual(rejected["result"], "HALT_OPERATION_REJECTED_READBACK_REQUIRED")
        self.assertFalse(rejected["order"]["terminal"])
        self.assertEqual(rejected["order"]["status"], "pending_cancel")

    def test_disconnect_blocks_events_until_independent_rest_readback(self):
        self.acknowledge()
        self.reconciler.apply_trade_update(update("accepted"), "accepted-1")
        self.reconciler.disconnect()
        self.reconciler.acknowledge_streams(["trade_updates"])
        blocked = self.reconciler.apply_trade_update(update("canceled"), "canceled-1")
        self.assertEqual(blocked["result"], "HALT_RECONNECT_READBACK_REQUIRED")
        restored = self.reconciler.apply_rest_snapshot([
            {"id": "order-1", "qty": "10", "filled_qty": "2", "status": "canceled"}
        ])
        self.assertEqual(restored["result"], "REST_READBACK_APPLIED")
        self.assertTrue(restored["state_authoritative"])
        self.assertTrue(restored["orders"][0]["terminal"])

    def test_readback_cannot_silently_drop_a_tracked_order(self):
        self.acknowledge()
        self.reconciler.apply_trade_update(update("accepted"), "accepted-1")
        self.reconciler.disconnect()
        self.reconciler.acknowledge_streams(["trade_updates"])
        incomplete = self.reconciler.apply_rest_snapshot([])
        self.assertEqual(incomplete["result"], "HALT_REST_READBACK_INCOMPLETE")
        self.assertTrue(incomplete["rest_readback_required"])
        self.assertIn("order-1", self.reconciler.orders)

    def test_terminal_state_cannot_be_regressed_by_late_event(self):
        self.acknowledge()
        self.reconciler.apply_trade_update(update("canceled"), "cancel-1")
        late = self.reconciler.apply_trade_update(update("accepted"), "late-1")
        self.assertEqual(late["result"], "HALT_EVENT_AFTER_TERMINAL")
        self.assertEqual(late["order"]["status"], "canceled")


if __name__ == "__main__":
    unittest.main()
