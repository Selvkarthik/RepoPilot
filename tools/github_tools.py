from langchain_core.tools import tool

from tools.github_client import github
from rag.retriever import CodeRetriever

from rag.index_service import index_repository as run_index


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
def get_file_content(owner:str, repo:str, path:str) -> str:
    """Get the content of a specific file from a GitHub repository"""
    try:
        repository = github.get_repo(f"{owner}/{repo}")
        file = repository.get_contents(path)
        content = file.decoded_content.decode('utf_8')
        return content
    except Exception as err:
        return f"Unable to retrieve file: {err}"

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
    Search the indexed source of a GitHub repository.
    Use this tool when you need to understand the implementation
    or contents of source files.
    """

    retriever = CodeRetriever(
        repository=repository,
        k=3
    )

    documents = retriever.invoke(query)

    if not documents:
        return "No relevant code was found."

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

    return "\n---\n".join(results)

@tool
def index_github_repository(owner: str, repo: str) -> str:
    """Index a GitHub repository so its source code can be searched using RAG."""

    try:
        result = run_index(owner, repo)

        return (
            f"Successfully indexed {result['repository']}."
            f"Processed {result['files']} files and"
            f"generated {result['chunks']} chunks."
        )
    except Exception as err:
        return f"Unable to index repository: {err}"