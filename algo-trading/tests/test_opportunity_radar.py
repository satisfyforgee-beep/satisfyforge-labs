"""Paper radar never routes an order, even for favorable quote inputs."""
import unittest
from datetime import datetime, timedelta, timezone

from zerocost_bot.market_coverage import AssetClass, MarketQuote
from zerocost_bot.opportunity_radar import review_paper_idea, PAPER_MODE

NOW = datetime(2026, 10, 26, 21, 29, 30, tzinfo=timezone.utc)


def paper_cash(cash="150.00", active=0, positions=None, pnl="0.00"):
    return {
        "mode": PAPER_MODE, "opening_cash": "150.00",
        "available_for_next_paper_trade": cash,
        "maximum_order_debit": "30.00", "settled_cash": cash,
        "reserved_cash": "0.00", "active_reservation_count": active,
        "positions": [] if positions is None else positions,
        "realized_net_pnl": pnl,
    }


def quote(asset, symbol, bid, ask, provider, age=1):
    t = NOW - timedelta(seconds=age)
    return MarketQuote(provider, asset, symbol, bid, ask, t, t, NOW, True)


class PaperRadarTests(unittest.TestCase):
    def test_crypto_fractional_research_does_not_authorize_orders(self):
        result = review_paper_idea(
            quote(AssetClass.CRYPTO, "BTC/USD", 79927.9, 79928.1,
                  "kraken_public"), paper_cash(), now=NOW)
        self.assertEqual(result.status, "RESEARCH_ONLY")
        self.assertEqual(result.data_source, "kraken_public")
        self.assertEqual(result.hypothetical_max_quantity, "0.00037220")
        self.assertFalse(result.paper_order_authorized)
        self.assertFalse(result.as_report()["live_order_authorized"])
        self.assertIn("NO_VERIFIED_ALPHA", result.reasons[0])

    def test_stock_closed_waits(self):
        result = review_paper_idea(
            quote(AssetClass.STOCK, "SOFI", 14.43, 14.44, "tradier_live"),
            paper_cash(), now=NOW, market_regular_session=False)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("US_REGULAR_SESSION_CLOSED", result.reasons)

    def test_stock_regular_session_can_be_research_only(self):
        result = review_paper_idea(
            quote(AssetClass.STOCK, "SOFI", 14.43, 14.44, "tradier_live"),
            paper_cash(), now=NOW, market_regular_session=True)
        self.assertEqual(result.hypothetical_max_quantity, "2")
        self.assertEqual(result.status, "RESEARCH_ONLY")

    def test_option_multiplier_budget_and_near_expiry(self):
        later = review_paper_idea(
            quote(AssetClass.OPTION, "SOFI261120C00015000",
                  0.219, 0.22, "tradier_live"),
            paper_cash(), now=NOW, market_regular_session=True)
        self.assertEqual(later.status, "RESEARCH_ONLY")
        self.assertEqual(later.hypothetical_max_quantity, "1")
        self.assertEqual(later.hypothetical_max_debit, "22.25")
        near = review_paper_idea(
            quote(AssetClass.OPTION, "SOFI261030C00015000",
                  0.219, 0.22, "tradier_live"),
            paper_cash(), now=NOW, market_regular_session=True)
        self.assertIn("OPTION_EXPIRY_TOO_NEAR", near.reasons)
        expensive = review_paper_idea(
            quote(AssetClass.OPTION, "SOFI261120C00015000",
                  0.519, 0.52, "tradier_live"),
            paper_cash(), now=NOW, market_regular_session=True)
        self.assertEqual(expensive.status, "BLOCKED")
        self.assertIn("ONE_UNIT_OR_CONTRACT_EXCEEDS_30_DOLLAR_CAP", expensive.reasons)

    def test_delayed_and_stale_blocked(self):
        delayed = review_paper_idea(
            quote(AssetClass.STOCK, "SOFI", 14.43, 14.44, "tradier_sandbox"),
            paper_cash(), now=NOW, market_regular_session=True)
        self.assertIn("DELAYED_QUOTES_NOT_ENTRY_DATA", delayed.reasons)
        stale = review_paper_idea(
            quote(AssetClass.CRYPTO, "SOL/USD", 100.41, 100.42,
                  "kraken_public", age=30),
            paper_cash(), now=NOW)
        # Kraken's public REST snapshot freshness is based on response receipt.
        self.assertEqual(stale.status, "RESEARCH_ONLY")

    def test_spread_and_slots_and_loss_cash(self):
        wide = review_paper_idea(
            quote(AssetClass.CRYPTO, "ETH/USD", 2100, 2306.53,
                  "kraken_public"), paper_cash(), now=NOW)
        self.assertIn("WIDE_SPREAD", wide.reasons)
        full = review_paper_idea(
            quote(AssetClass.CRYPTO, "SOL/USD", 100.41, 100.42,
                  "kraken_public"),
            paper_cash("12.00", active=4,
                       positions=[{"asset": "stock", "symbol": "SOFI"}],
                       pnl="-5.00"), now=NOW)
        self.assertIn("MAX_FIVE_PAPER_POSITIONS_OR_RESERVATIONS", full.reasons)

    def test_insufficient_and_wrong_account_type(self):
        blocked = review_paper_idea(
            quote(AssetClass.CRYPTO, "ETH/USD", 2306.52, 2306.53,
                  "kraken_public"), paper_cash("0.20"), now=NOW)
        self.assertEqual(blocked.status, "BLOCKED")
        with self.assertRaises(ValueError):
            review_paper_idea(
                quote(AssetClass.CRYPTO, "ETH/USD", 2306.52, 2306.53,
                      "kraken_public"), {"mode": "LIVE_BROKER_ACCOUNT"},
                now=NOW)

    def test_malformed_unsupported_instrument_denied(self):
        result = review_paper_idea(
            quote(AssetClass.CRYPTO, "BTC/USD", 0, 100,
                  "kraken_public"), paper_cash(), now=NOW)
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.hypothetical_max_debit, "0.00")


if __name__ == "__main__":
    unittest.main()
