from celery.exceptions import MaxRetriesExceededError

from .celery_app import celery_app
from rag.index_service import index_repository

import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def sync_repository(self, owner: str, repo: str):
    logger.info(
        "Starting background sync: %s/%s",
        owner,
        repo,
    )

    try:

        result = index_repository(owner, repo)

        logger.info(
            "Background sync completed: %s/%s result=%s",
            owner,
            repo,
            result,
        )

        return result

    except Exception as exc:
        logger.exception(
            "Background sync failed: %s/%s",
            owner,
            repo,
        )

        try:
            raise self.retry(
                exc=exc,
                countdown=10 * (2 ** self.request.retries),
            )

        except MaxRetriesExceededError:
            logger.error(
                "Background repository sync failed permanently: repository=%s",
                owner, repo,
                exc_info=True,
            )