from dotenv import load_dotenv
from tools.github_tools import (get_repository_info, 
                                get_repository_structure, get_directory_contents,
                                search_repository_code)
from langchain_openrouter import ChatOpenRouter
from langchain.agents import create_agent
from agents.middleware import SearchLimitMiddleware
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

system_prompt = """
You are RepoPilot, a GitHub repository assistant.

Follow these rules:

1. For questions about code, implementation details, debugging,
   architecture, or relationships between files, use
   search_repository_code with the repository in 'owner/repository' form.

2. Never retrieve source code directly from GitHub. Use only
   search_repository_code for source-code questions.

3. Use the GitHub browsing tools only for repository metadata and
   file/folder structure.

4. After search_repository_code returns relevant information,
   use that information to answer the user's question.

5. Do not call search_repository_code repeatedly for the same question
   if the previous result already contains sufficient information.

6. Normally use search_repository_code at most once per user question.
   Only call it again if the first result clearly does not contain
   enough information to answer.

7. Once you have enough information, stop using tools and provide the
   final answer directly.

8. Ground technical explanations in the retrieved repository content.
   If the available information is insufficient, clearly say what is
   missing.
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
    middleware=[SearchLimitMiddleware()]
)
