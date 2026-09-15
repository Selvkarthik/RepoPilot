from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class AskEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.main.agent")
    def test_returns_agent_answer_for_valid_request(self, agent):
        agent.invoke.return_value = {
            "messages": [SimpleNamespace(content="The connection uses psycopg.")]
        }

        response = self.client.post(
            "/ask",
            json={
                "repository": "selvkarthik/DocQuery",
                "question": "How does the database connection work?",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "repository": "selvkarthik/DocQuery",
                "answer": "The connection uses psycopg.",
            },
        )
        message = agent.invoke.call_args.args[0]["messages"][0]
        self.assertIn("Repository: selvkarthik/DocQuery", message.content)

    def test_rejects_invalid_repository(self):
        response = self.client.post(
            "/ask",
            json={"repository": "DocQuery", "question": "How does it work?"},
        )

        self.assertEqual(response.status_code, 422)

    @patch("app.main.agent")
    def test_returns_bad_gateway_when_agent_fails(self, agent):
        agent.invoke.side_effect = RuntimeError("LLM unavailable")

        response = self.client.post(
            "/ask",
            json={
                "repository": "selvkarthik/DocQuery",
                "question": "How does it work?",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "Unable to answer repository question: LLM unavailable",
        )


if __name__ == "__main__":
    unittest.main()
