from rag.index_service import index_repository
from .celery_app import celery_app

@celery_app.task
def sync_repository(owner : str, repo : str):
    print(f"Starting backgroung sync: {owner}/{repo}")

    result = index_repository(owner, repo)

    print(f"Background sync completed: {result}")

    return result