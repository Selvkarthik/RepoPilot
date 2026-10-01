from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "RepoPilot is running"})

    @patch("app.main.agent")
    def test_valid_ask_request(self, mock_agent):
        mock_agent.invoke.return_value = {
            "messages": [SimpleNamespace(content="Authentication uses JWT tokens.")]
        }

        response = self.client.post(
            "/ask",
            json={
                "repository": "selvkarthik/DocQuery",
                "question": "How does authentication work?",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["repository"], "selvkarthik/DocQuery")
        self.assertEqual(data["answer"], "Authentication uses JWT tokens.")

    def test_invalid_repository_format(self):
        # Missing owner/ separator
        response = self.client.post(
            "/ask",
            json={
                "repository": "InvalidRepoNoSlash",
                "question": "How does it work?",
            },
        )
        self.assertEqual(response.status_code, 422)

        # Extra slashes
        response2 = self.client.post(
            "/ask",
            json={
                "repository": "owner/repo/sub",
                "question": "How does it work?",
            },
        )
        self.assertEqual(response2.status_code, 422)

    def test_empty_question_rejected(self):
        # Completely empty string
        response = self.client.post(
            "/ask",
            json={
                "repository": "owner/repo",
                "question": "",
            },
        )
        self.assertEqual(response.status_code, 422)

        # Whitespace-only string
        response_whitespace = self.client.post(
            "/ask",
            json={
                "repository": "owner/repo",
                "question": "   ",
            },
        )
        self.assertEqual(response_whitespace.status_code, 422)

    def test_oversized_question_rejected(self):
        # Maximum allowed question length is 2000 chars in AskRequest
        oversized = "x" * 2001
        response = self.client.post(
            "/ask",
            json={
                "repository": "owner/repo",
                "question": oversized,
            },
        )
        self.assertEqual(response.status_code, 422)

    @patch("app.main.agent")
    def test_expected_error_response_when_agent_fails(self, mock_agent):
        mock_agent.invoke.side_effect = RuntimeError("OpenRouter service unavailable")

        response = self.client.post(
            "/ask",
            json={
                "repository": "owner/repo",
                "question": "How does this code work?",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("Unable to answer repository question", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
