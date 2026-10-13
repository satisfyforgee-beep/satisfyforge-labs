import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_commerce_safety import scan_operational_surfaces


class CommerceSafetyTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "commerce").mkdir()
        (root / "satisfyforge-site").mkdir()
        (root / "publisher").mkdir()
        (root / "sales").mkdir()
        registry = {
            "checkouts": [
                {"product_id": "blocked123", "status": "quarantined"},
                {"product_id": "safe456", "status": "verified"},
            ]
        }
        (root / "commerce" / "checkout_registry.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        return temp, root

    def test_blocks_quarantined_checkout(self):
        temp, root = self.make_repo()
        try:
            (root / "satisfyforge-site" / "index.html").write_text(
                "https://payhip.com/b/blocked123", encoding="utf-8"
            )
            violations = scan_operational_surfaces(root)
            self.assertEqual(len(violations), 1)
            self.assertIn("blocked123", violations[0])
        finally:
            temp.cleanup()

    def test_allows_verified_checkout_and_request_form(self):
        temp, root = self.make_repo()
        try:
            (root / "satisfyforge-site" / "index.html").write_text(
                "https://payhip.com/b/safe456 https://example.wixforms.com/request",
                encoding="utf-8",
            )
            self.assertEqual(scan_operational_surfaces(root), [])
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
