"""Offline regression tests for real-bar crypto historical virtual executions."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
import unittest

from zerocost_bot.crypto_replay import Candle, fetch_kraken_ohlc, aligned, simulate, _signal


def fake_candle(i, *, op="100", hi="100.4", lo="99.6", cl="100", volume="15"):
    return Candle(1700000100 // 900 * 900 + i * 900,
                  Decimal(op), Decimal(hi), Decimal(lo),
                  Decimal(cl), Decimal(volume))


def sample(count=160):
    return {s: [fake_candle(i) for i in range(count)]
            for s in ("BTC/USD", "ETH/USD", "SOL/USD")}


class ReplayTests(unittest.TestCase):
    def test_control_trades_multiple_assets_and_accounts_for_costs(self):
        t, bars = aligned(sample())
        result = simulate(bars, strategy="control", start=18, end=150)
        self.assertGreaterEqual(result["virtual_closes"], 8)
        self.assertEqual(result["virtual_buys"], result["virtual_closes"])
        self.assertEqual(result["wins"], 0)
        self.assertLess(Decimal(result["net_pnl_after_estimated_costs"]), 0)
        self.assertGreater(Decimal(result["estimated_fees"]), 0)
        self.assertEqual({e["symbol"] for e in result["events"]},
                         {"BTC/USD", "ETH/USD", "SOL/USD"})
        self.assertTrue(all(e["simulation_not_broker_fill"]
                            for e in result["events"]))

    def test_no_future_lookahead_in_entry_signal(self):
        seq = sample()["BTC/USD"]
        k = 50
        before = _signal("breakout", seq, k, 0)
        changed = list(seq)
        changed[k] = fake_candle(k, op="100", hi="900", lo="1", cl="100")
        self.assertEqual(_signal("breakout", changed, k, 0), before)

    def test_exit_stop_first_if_both_touched(self):
        bars = sample()
        # BTC control entry i=24; same bar risk should be checked.
        for s in bars:
            bars[s][24] = fake_candle(24, op="100", hi="105", lo="97", cl="100")
        _, matrix = aligned(bars)
        result = simulate(matrix, strategy="control", start=18, end=45)
        btc = [e for e in result["events"] if e["symbol"] == "BTC/USD"]
        self.assertTrue(btc)
        self.assertEqual(btc[0]["side"], "buy")
        self.assertEqual(btc[1]["side"], "sell")
        self.assertEqual(btc[1]["reason"], "stop")
        self.assertLess(Decimal(btc[1]["pnl"]), 0)

    def test_foreign_candle_and_missing_crossmarket_gap_block(self):
        dataset = sample()
        dataset["ETH/USD"].pop(50)
        with self.assertRaisesRegex(ValueError, "missing aligned"):
            aligned(dataset)

    def test_reversal_and_breakout_are_deterministic_and_bounded(self):
        _, bars = aligned(sample())
        for name in ("breakout", "reversal"):
            report = simulate(bars, strategy=name, start=35, end=140)
            self.assertEqual(report["virtual_buys"], report["virtual_closes"])
            self.assertGreaterEqual(Decimal(report["ending_virtual_cash"]), 0)
            self.assertLessEqual(report["max_drawdown_pct"] and
                                 Decimal(report["max_drawdown_pct"]), 100)

    def test_fresh_fake_last_candle_is_discarded(self):
        start = 1700000100 // 900 * 900
        rows = []
        for i in range(32):
            rows.append([start+i*900, "100", "101", "99", "100",
                         "100", "10", 10])
        payload = {"error": [], "result": {"XXBTZUSD": rows, "last": 0}}
        def fake_open(_request, timeout):
            return io.BytesIO(json.dumps(payload).encode())
        now = datetime.fromtimestamp(start + 33*900, timezone.utc)
        complete = fetch_kraken_ohlc("BTC/USD", opener=fake_open, now=now)
        self.assertEqual(len(complete), 31)
        self.assertEqual(complete[-1].at, start + 30*900)
        self.assertNotIn(rows[-1][0], {x.at for x in complete})

    def test_untrusted_pair_and_bad_prices_fail(self):
        with self.assertRaises(ValueError):
            fetch_kraken_ohlc("DOGE/EUR")
        with self.assertRaises(ValueError):
            fake_candle(1, op="100", lo="105").validate()
        with self.assertRaises(ValueError):
            simulate(sample(), strategy="unbounded", start=18, end=50)


if __name__ == "__main__":
    unittest.main()
