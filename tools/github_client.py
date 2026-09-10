from github import Github, Auth
from dotenv import load_dotenv
import os

load_dotenv()

github = Github(
    auth=Auth.Token(os.getenv("GITHUB_TOKEN"))
)