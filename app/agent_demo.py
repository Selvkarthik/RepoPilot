from agents.agent import agent
from langchain_core.messages import HumanMessage

response = agent.invoke({
    'messages' : [
        HumanMessage(
            content="How does the database connection work in selvkarthik/DocQuery?"
        )
    ]
})

for message in response['messages']:
    print("\n---")
    print(type(message).__name__)
    print(message)

print(response['messages'][-1].content)