from dotenv import load_dotenv
from tools.github_tools import (get_repository_info, 
                                get_repository_structure, get_directory_contents,
                                search_repository_code)
from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent
import os

load_dotenv()

llm = ChatOpenRouter(
    model='inclusionai/ling-3.0-flash-fin:free',
    api_key=os.getenv("OPENROUTER_API_KEY")
)

tools = [
    get_repository_info,
    get_repository_structure,
    get_directory_contents,
    search_repository_code
    ]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=(
        "You are RepoPilot, a GitHub repository assistant. For questions about "
        "how code works, implementation details, or relationships between files, "
        "use search_repository_code with the repository in 'owner/repository' form "
        "before answering. That tool synchronizes the repository index, so do not "
        "ask the user to index it manually. Never retrieve source code directly "
        "from GitHub; use only search_repository_code for code, debugging, and "
        "architecture questions. Use the GitHub browsing tools for repository "
        "metadata and structure. Ground "
        "your code explanations in tool results and say when information is missing."
    )
)
