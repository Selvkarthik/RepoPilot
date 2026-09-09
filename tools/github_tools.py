from dotenv import load_dotenv
from langchain_core.tools import tool
from github import Github
import os

load_dotenv()

@tool
def get_repository_info(owner:str, repo:str) -> str:
    """Get basic information about a GitHub repository."""

    github = Github(os.getenv("GITHUB_TOKEN"))

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

    github = Github(os.getenv("GITHUB_TOKEN"))

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
        github = Github(os.getenv("GITHUB_TOKEN"))
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
        github = Github(os.getenv("GITHUB_TOKEN"))
        respository = github.get_repo(f"{owner}/{repo}")
        contents = respository.get_contents(path)
        result = []

        for item in contents:
            result.append(f"{item.type} : {item.path}")

        return "\n".join(result)
    except Exception as err:
        return f"Unable to retrieve directory: {err}"