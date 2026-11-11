"""Regression tests for quarantined checkout links in customer-facing surfaces."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_commerce_safety import load_blocked_product_ids, scan_operational_surfaces


class CommerceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "commerce").mkdir()
        (self.root / "commerce" / "checkout_registry.json").write_text(
            json.dumps({"checkouts": [
                {"product_id": "BLOCKED", "status": "quarantined"},
                {"product_id": "PENDING", "status": "unverified"},
                {"product_id": "SAFE", "status": "verified"}
            ]}), encoding="utf-8"
        )

    def test_blocked_statuses(self):
        self.assertEqual(load_blocked_product_ids(self.root / "commerce" / "checkout_registry.json"), {"BLOCKED", "PENDING"})

    def test_blocks_customer_facing_links(self):
        page = self.root / "sales" / "offer.md"
        page.parent.mkdir()
        page.write_text("https://payhip.com/b/BLOCKED", encoding="utf-8")
        violations = scan_operational_surfaces(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("BLOCKED", violations[0])

    def test_unverified_checkout_is_blocked(self):
        page = self.root / "publisher" / "post.txt"
        page.parent.mkdir()
        page.write_text("https://payhip.com/b/PENDING", encoding="utf-8")
        self.assertEqual(len(scan_operational_surfaces(self.root)), 1)

    def test_verified_checkout_is_allowed(self):
        page = self.root / "satisfyforge-site" / "index.html"
        page.parent.mkdir()
        page.write_text("https://payhip.com/b/SAFE", encoding="utf-8")
        self.assertEqual(scan_operational_surfaces(self.root), [])

    def test_nonoperational_docs_not_flagged(self):
        page = self.root / "docs" / "historical.md"
        page.parent.mkdir()
        page.write_text("https://payhip.com/b/BLOCKED", encoding="utf-8")
        self.assertEqual(scan_operational_surfaces(self.root), [])


if __name__ == "__main__":
    unittest.main()
