import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import n8n_client


class LeadWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.db_path = Path(self.temp_dir.name) / "leads_test.db"
        self.original_db_path = database.DATABASE_PATH
        database.DATABASE_PATH = self.db_path
        self.addCleanup(setattr, database, "DATABASE_PATH", self.original_db_path)

    def test_save_lead_persists_company_size_and_requirement(self) -> None:
        lead_data = {
            "name": "Jane Doe",
            "company": "Acme",
            "industry": "Technology",
            "company_size": "51-200",
            "budget": "100000",
            "timeline": "ASAP",
            "requirement": "We need an AI chatbot",
            "score": 85,
            "category": "Hot",
            "reason": "Strong fit",
            "next_action": "Follow up",
            "risks": "None",
        }

        database.save_lead(lead_data)

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT company_size, requirement FROM leads WHERE name = ?",
                ("Jane Doe",),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "51-200")
        self.assertEqual(row[1], "We need an AI chatbot")

    def test_send_lead_to_n8n_includes_company_size_and_requirement(self) -> None:
        lead_data = {
            "name": "Jane Doe",
            "company": "Acme",
            "industry": "Technology",
            "company_size": "201-500",
            "budget": "100000",
            "timeline": "ASAP",
            "requirement": "We need automation",
            "score": 85,
            "category": "Hot",
            "reason": "Strong fit",
            "next_action": "Follow up",
            "risks": "None",
        }

        with patch("n8n_client.requests.post") as mock_post:
            mock_post.return_value.raise_for_status.return_value = None
            result = n8n_client.send_lead_to_n8n(lead_data)

        self.assertTrue(result)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["company_size"], "201-500")
        self.assertEqual(payload["requirement"], "We need automation")


if __name__ == "__main__":
    unittest.main()
