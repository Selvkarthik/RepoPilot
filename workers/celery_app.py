from celery import Celery
from core.config import settings

if not settings.REDIS_BROKER_URL or not settings.REDIS_RESULT_BACKEND:
    raise RuntimeError("Redis configuration is missing.")

celery_app = Celery(
    "repopilot",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_RESULT_BACKEND,
)

celery_app.conf.imports = (
    "workers.repository_worker",
)