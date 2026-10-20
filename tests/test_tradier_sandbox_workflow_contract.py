"""Workflow safety contract: no automatic broker preview on repo pushes."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/tradier-sandbox-readonly.yml"

class WorkflowGuardTests(unittest.TestCase):
    def test_broker_auth_preview_manual_dispatch_only(self):
        source = WORKFLOW.read_text()
        self.assertIn("if: github.event_name == 'workflow_dispatch'",source)
        self.assertIn("needs: offline-validation",source)
        self.assertNotIn("github.event_name == 'workflow_dispatch' || github.event_name == 'push'",source)

    def test_preview_only_and_no_live_account_access(self):
        source = WORKFLOW.read_text()
        self.assertIn("unset SF_TRADIER_PAPER_ENABLE",source)
        self.assertIn("tradier_paper_cli.py --symbol SOFI --preview",source)
        self.assertIn("secrets.TRADIER_SANDBOX_TOKEN",source)
        self.assertNotIn("TRADIER_PRODUCTION_TOKEN",source)
        self.assertNotIn("--paper-submit",source)
        self.assertNotIn("submit_paper(",source)

if __name__ == "__main__":
    unittest.main()
