import hashlib
import hmac
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app, verify_signature


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.secret = "test-secret-key-12345"

    def _sign(self, payload: bytes, secret: str) -> str:
        return "sha256=" + hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

    def test_verify_signature_direct(self):
        payload = b'{"action": "test"}'
        sig = self._sign(payload, self.secret)

        with patch("app.main.settings.GITHUB_WEBHOOK_SECRET", self.secret):
            self.assertTrue(verify_signature(payload, sig))
            self.assertFalse(verify_signature(payload, "sha256=invalidhex"))
            self.assertFalse(verify_signature(payload, None))
            self.assertFalse(verify_signature(payload, ""))

    @patch("app.main.sync_repository")
    def test_webhook_valid_signature_accepted(self, mock_sync):
        payload = b'{"repository": {"name": "RepoPilot", "owner": {"login": "selvkarthik"}}}'
        sig = self._sign(payload, self.secret)

        with patch("app.main.settings.GITHUB_WEBHOOK_SECRET", self.secret):
            response = self.client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": sig,
                },
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["repository"], "selvkarthik/RepoPilot")
        mock_sync.delay.assert_called_once_with("selvkarthik", "RepoPilot")

    def test_webhook_invalid_signature_rejected(self):
        payload = b'{"repository": {"name": "RepoPilot", "owner": {"login": "selvkarthik"}}}'

        with patch("app.main.settings.GITHUB_WEBHOOK_SECRET", self.secret):
            response = self.client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=wrongsignature",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid Webhook signature")

    def test_webhook_missing_signature_rejected(self):
        payload = b'{"repository": {"name": "RepoPilot", "owner": {"login": "selvkarthik"}}}'

        with patch("app.main.settings.GITHUB_WEBHOOK_SECRET", self.secret):
            response = self.client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid Webhook signature")

    def test_webhook_non_push_event_ignored(self):
        payload = b'{"repository": {"name": "RepoPilot", "owner": {"login": "selvkarthik"}}}'
        sig = self._sign(payload, self.secret)

        with patch("app.main.settings.GITHUB_WEBHOOK_SECRET", self.secret):
            response = self.client.post(
                "/webhooks/github",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "ping",
                    "X-Hub-Signature-256": sig,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ignored")


if __name__ == "__main__":
    unittest.main()
