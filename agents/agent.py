from dotenv import load_dotenv
from tools.github_tools import (get_repository_info, 
                                get_repository_structure, get_file_content, get_directory_contents)
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
    get_file_content,
    get_directory_contents
    ]

agent = create_agent(
    model=llm,
    tools=tools
)