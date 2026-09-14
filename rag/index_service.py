from rag.indexer import get_repository_files, get_repository_state
from rag.documents import create_documents
from rag.splitter import split_documents
from rag.vector_store import store_chunks
from rag.database import get_connection

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

def index_repository(owner : str, repo : str):
    repository = f"{owner}/{repo}"

    github_state = get_repository_state(owner, repo)
    stored_state = get_stored_repository_state(owner, repo)

    if (stored_state
        and stored_state[0] == github_state['branch']
        and stored_state[1] == github_state['commit_sha']):
        return {
            "repository" : repository,
            "files" : 0,
            "chunks" : 0,
            "status" : "up_to_date"
        }

    files = get_repository_files(owner, repo)

    documents = create_documents(files, repository)

    chunks = split_documents(documents)

    store_chunks(chunks)

    save_repository_state(github_state)

    return {
        "repository" : repository,
        "files" : len(files),
        "chunks" : len(chunks),
        "status" : "indexed"
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