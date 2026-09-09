from langchain_core.messages import (SystemMessage, HumanMessage)
from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenRouter(
    model='inclusionai/ling-3.0-flash-fin:free',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

messages = [
    SystemMessage(
        content = 'You are a helpful GitHub assistant.'
    ),
    HumanMessage(
        content='What is a pull request?'
    )
]

response = llm.invoke(messages)

print(response)
print("\nAnswer: ", response.content)