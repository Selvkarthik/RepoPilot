from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
import os

load_dotenv()

llm = ChatOpenRouter(
    model='inclusionai/ling-3.0-flash-fin:free',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

response = llm.invoke("Explain what GitHub is in one sentence.")
print(response.content)