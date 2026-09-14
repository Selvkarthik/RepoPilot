from pathlib import Path
from tools.github_client import github
import hashlib

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

    result = []

    for file in files:
        content = file.decode_content.decode('utf-8')
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        result.append({
            "path" : file.path,
            "content" : content,
            "language" : LANGUAGE_MAP.get(Path(file.path).suffix.lower()),
            "content_hash" : content_hash
        })

    return result

def get_repository_state(owner:str, repo:str):
    repository = github.get_repo(f"{owner}/{repo}")
    branch = repository.default_branch
    branch_info = repository.get_branch(branch)

    return {
        "owner" : owner,
        "repo" : repo,
        "branch" : branch,
        "commit_sha" : branch_info.commit.sha
    }