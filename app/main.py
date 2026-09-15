from fastapi import FastAPI, HTTPException
from agents.agent import agent
from langchain_core.messages import HumanMessage
from .models import AskResponse, AskRequest

app = FastAPI(
    title='RepoPilot',
    description='AI engineering assistant for GitHub repositories',
    version='0.1.0'
)

@app.get('/')
def root():
    return {'msg' : 'RepoPilot is running'}

@app.post('/ask', response_model=AskResponse)
def ask_question(request : AskRequest):
    try:
        message = HumanMessage(
            content=(
                f'Repository: {request.repository}\n'
                f'Question: {request.question}'
            )
        )
        response = agent.invoke({'messages': [message]})
        return AskResponse(
            repository=request.repository,
            answer=response['messages'][-1].content
        )

    except Exception as err:
        raise HTTPException(
            status_code=502,
            detail=f'Unable to answer repository question: {err}',
        ) from err
