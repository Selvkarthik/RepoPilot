from celery.exceptions import MaxRetriesExceededError

from .celery_app import celery_app
from rag.index_service import index_repository


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def sync_repository(self, owner: str, repo: str):
    print(f"Starting background sync: {owner}/{repo}")

    try:

        result = index_repository(owner, repo)

        print(f"Background sync completed: {result}")

        return result

    except Exception as exc:
        print(
            f"Background sync failed for "
            f"{owner}/{repo}: {exc}"
        )

        try:
            raise self.retry(
                exc=exc,
                countdown=10 * (2 ** self.request.retries),
            )

        except MaxRetriesExceededError:
            print(
                f"Background sync permanently failed for "
                f"{owner}/{repo}"
            )
            raise