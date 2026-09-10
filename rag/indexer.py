from pathlib import Path
from dotenv import load_dotenv
from tools.github_client import github
import os

load_dotenv()

supported_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", '.go', ".rs", ".php", ".cs"}
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".cs": "csharp"
}

def _get_files(repository, path=""):
    files = []

    contents = repository.get_contents(path)

    for item in contents:
        if item.type == "file":
            extension = Path(item.path).suffix
            if extension in supported_extensions:
                files.append(item)
        elif item.type == "dir":
            files.extend(_get_files(repository, item.path))

    return files

def get_repository_files(owner:str, repo:str):
    repository = github.get_repo(f"{owner}/{repo}")

    files = _get_files(repository)

    return [
        {
            "path" : file.path,
            "content" : file.decoded_content.decode('utf-8'),
            "language" : LANGUAGE_MAP.get(Path(file.path).suffix.lower())
        }
        for file in files
    ]