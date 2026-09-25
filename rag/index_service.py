from rag.indexer import get_repository_files, get_repository_state
from rag.documents import create_documents
from rag.splitter import split_documents
from rag.database import get_connection
from rag.repository import CodeRepository
import logging

logger = logging.getLogger(__name__)


def store_chunks(chunks):
    """Load the embedding-backed storage only when a file needs indexing."""
    from rag.vector_store import store_chunks as persist_chunks

    persist_chunks(chunks)

def get_stored_repository_state(owner : str, repo : str):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT branch, commit_sha
                FROM repositories
                WHERE owner = %s
                AND repo = %s
                """,
                (owner, repo)
            )
            return cursor.fetchone()

def index_repository(owner: str, repo: str):

    repository = f"{owner}/{repo}"

    github_state = get_repository_state(owner, repo)
    stored_state = get_stored_repository_state(owner, repo)

    if (
        stored_state
        and stored_state[0] == github_state["branch"]
        and stored_state[1] == github_state["commit_sha"]
    ):
        return build_index_result(repository, "up_to_date")

    # Get the current files from GitHub
    files = get_repository_files(owner, repo)

    # Get file hashes currently stored in DB
    db = CodeRepository()
    stored_files = db.get_file_hashes(repository)

    current_paths = {
        file["path"]
        for file in files
    }

    # Files that disappeared from GitHub
    deleted_files = set(stored_files.keys()) - current_paths

    deleted_chunks = 0

    for file_path in deleted_files:
        deleted_chunks += db.delete_file(repository, file_path)

    # Only new or changed files need to be re-indexed
    files_to_index = []
    files_added = 0
    files_updated = 0

    for file in files:

        old_hash = stored_files.get(file["path"])

        if old_hash != file["content_hash"]:
            files_to_index.append(file)
            if old_hash is None:
                files_added += 1
            else:
                files_updated += 1

    logger.info("Stored files: %d", len(stored_files))
    logger.info("GitHub files: %d", len(files))
    logger.info(
    "Files to index: count=%d",
    len(files_to_index),
)
    logger.info(
            "Index changes: added=%d updated=%d deleted=%d",
            files_added,
            files_updated,
            len(deleted_files)
        )

    # Process changed/new files
    total_chunks = 0

    for file in files_to_index:

        # Remove old chunks if this is an updated file
        if file["path"] in stored_files:
            deleted_chunks += db.delete_file(
                repository,
                file["path"]
            )

        documents = create_documents(
            [file],
            repository
        )

        chunks = split_documents(documents)

        store_chunks(chunks)

        db.save_file(
            repository=repository,
            file_path=file["path"],
            language=file["language"],
            content_hash=file["content_hash"]
        )

        total_chunks += len(chunks)

    save_repository_state(github_state)

    return build_index_result(
        repository,
        "updated",
        files_added=files_added,
        files_updated=files_updated,
        files_deleted=len(deleted_files),
        chunks_created=total_chunks,
        chunks_deleted=deleted_chunks
    )


def build_index_result(
    repository: str,
    status: str,
    *,
    files_added: int = 0,
    files_updated: int = 0,
    files_deleted: int = 0,
    chunks_created: int = 0,
    chunks_deleted: int = 0
):
    """Return a consistent summary of a repository indexing run."""
    return {
        "repository": repository,
        "status": status,
        "files_added": files_added,
        "files_updated": files_updated,
        "files_deleted": files_deleted,
        "chunks_created": chunks_created,
        "chunks_deleted": chunks_deleted,
    }

def save_repository_state(state):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO repositories
                (owner, repo, branch, commit_sha)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (owner, repo)
                DO UPDATE SET
                branch = EXCLUDED.branch,
                commit_sha = EXCLUDED.commit_sha,
                last_indexed_at = CURRENT_TIMESTAMP
                """,
                (
                    state['owner'],
                    state['repo'],
                    state['branch'],
                    state['commit_sha']
                )
            )
        connection.commit()
