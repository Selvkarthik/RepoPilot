from langchain_core.tools import tool

from tools.github_client import github

from rag.repository import CodeRepository
from fastapi import HTTPException

from rag.cache import (
    build_cache_key,
    get_cached_result,
    set_cached_result
)


def get_code_retriever(repository: str, k: int = 3):
    """Create a retriever only when code search is requested."""
    from rag.retriever import CodeRetriever

    return CodeRetriever(repository=repository, k=k)


def split_repository_name(repository: str):
    """Validate and split the owner/repository form used by GitHub."""
    owner, separator, repo = repository.partition("/")

    if not separator or not owner or not repo or "/" in repo:
        raise ValueError("Repository must use the 'owner/repository' format.")

    return owner, repo


@tool
def get_repository_info(owner:str, repo:str) -> str:
    """Get basic information about a GitHub repository."""

    repository = github.get_repo(f"{owner}/{repo}")

    return (
        f"Name: {repository.full_name}\n"
        f"Description: {repository.description}\n"
        f"Language: {repository.language}\n"
        f"Stars: {repository.stargazers_count}\n"
        f"Forks: {repository.forks_count}\n"
        f"Open Issues: {repository.open_issues_count}\n"
        f"Default Branch: {repository.default_branch}"
    )

@tool
def get_repository_structure(owner:str, repo:str) -> str:
    """Get the file and folder structure of a GitHub repository"""

    repository = github.get_repo(f"{owner}/{repo}")

    contents = repository.get_contents("")

    result = []

    for item in contents:
        result.append(f"{item.type} : {item.path}")

    return "\n".join(result)

@tool
def get_directory_contents(owner:str, repo:str, path:str = "") -> str:
    """Get directory contents"""
    try:
        respository = github.get_repo(f"{owner}/{repo}")
        contents = respository.get_contents(path)
        result = []

        for item in contents:
            result.append(f"{item.type} : {item.path}")

        return "\n".join(result)
    except Exception as err:
        return f"Unable to retrieve directory: {err}"

@tool
def search_repository_code(query : str, repository : str) -> str:
    """
    Search the indexed source code of a GitHub repository.

    The repository must use the 'owner/repository' format.
    Repository synchronization is handled separately by the
    background indexing system.
    """

    try:
        db = CodeRepository()

        commit_sha = db.get_repository_commit(repository)

        if not commit_sha:
            return f"Repository {repository} has not been indexed yet."

        cache_key = build_cache_key(
            repository,
            commit_sha,
            query
        )

        cached_result = get_cached_result(cache_key)

        if cached_result is not None:
            print(f"Cache HIT: {repository}")
            return cached_result

        print(f"Cache MISS: {repository}")

        retriever = get_code_retriever(repository, k=3)
        documents = retriever.invoke(query)

    except Exception as err:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail=f"Unable to prepare {repository} for code search: {err}"
        ) from err

    if not documents:
        result = "No relevant code was found in the repository."

        set_cached_result(
            cache_key, result,
        )

        return result

    results = []

    for document in documents:
        results.append(
            f"""
            File: {document.metadata['file_path']}
            Language: {document.metadata['language']}
            Chunk: {document.metadata['chunk_index']}
            {document.page_content}
            """
        )

    result = "\n---\n".join(results)

    set_cached_result(cache_key, result,)

    return result