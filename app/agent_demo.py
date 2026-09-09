from agents.agent import agent
from langchain_core.messages import HumanMessage

response = agent.invoke({
    'messages' : [
        HumanMessage(
            content="Explore the rag directory of selvkarthik/DocQuery and explain what each file appears to be responsible for."
        )
    ]
})

for message in response['messages']:
    print("\n---")
    print(type(message).__name__)
    print(message)