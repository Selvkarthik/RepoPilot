from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from tools.github_tools import get_repository_info
from langchain_core.messages import ToolMessage, HumanMessage
import os

load_dotenv()

llm = ChatOpenRouter(
    model='inclusionai/ling-3.0-flash-fin:free',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

llm_with_tools = llm.bind_tools([get_repository_info])

question = 'Tell me about the respository selvkarthik/DocQuery'

response = llm_with_tools.invoke(question)

for tool_call in response.tool_calls:
    if tool_call['name'] == get_repository_info.name:
        result = get_repository_info.invoke(tool_call['args'])

        tool_message = ToolMessage(
            content=result,
            tool_call_id = tool_call['id']
        )

        final_response = llm_with_tools.invoke([
            HumanMessage(content=question),
            response,
            tool_message
        ])

        print("Final answer:", final_response.content)