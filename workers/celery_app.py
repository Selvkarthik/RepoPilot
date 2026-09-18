from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

broker_url = os.getenv("REDIS_BROKER_URL")
result_backend = os.getenv("REDIS_RESULT_BACKEND")

if not broker_url or not result_backend:
    raise RuntimeError("Redis configuration is missing.")

celery_app = Celery(
    "repopilot",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.imports = (
    "workers.repository_worker"
)