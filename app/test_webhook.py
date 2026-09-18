import hashlib
import hmac
import os

import requests
from dotenv import load_dotenv


load_dotenv()

secret = os.getenv("GITHUB_WEBHOOK_SECRET")

body = b'{"repository":{"name":"DocQuery","owner":{"login":"selvkarthik"}}}'

signature = (
    "sha256="
    + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
)

response = requests.post(
    "http://127.0.0.1:8000/webhooks/github",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": signature,
    },
)

print(response.status_code)
print(response.json())