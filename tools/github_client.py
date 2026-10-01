from github import Github, Auth
from core.config import settings

github = Github(
    auth=Auth.Token(settings.GITHUB_TOKEN)
)