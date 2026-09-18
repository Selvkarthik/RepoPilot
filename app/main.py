from fastapi import FastAPI, HTTPException, Header, Request
from typing import Optional
from dotenv import load_dotenv
import hashlib
import hmac
import os

from agents.agent import agent
from langchain_core.messages import HumanMessage

from .models import AskResponse, AskRequest
from workers.repository_worker import sync_repository

load_dotenv()

app = FastAPI(
    title='RepoPilot',
    description='AI engineering assistant for GitHub repositories',
    version='0.1.0'
)

def verify_signature(
        payload : bytes,
        signature : str | None
) -> bool:
    secret = os.getenv('GITHUB_WEBHOOK_SECRET')

    if not secret or not signature:
        return False

    expected_signature = (
        "sha256="
        +hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
    )

    return hmac.compare_digest(
        expected_signature,
        signature
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

@app.post("/webhooks/github")
async def githbub_webhook(
    request : Request,
    x_github_event : Optional[str] = Header(default=None),
    x_hub_signature_256 : Optional[str] = Header(default=None)
):
    payload = await request.body()

    if not verify_signature(
        payload, x_hub_signature_256
    ):
        raise HTTPException(
            status_code=401,
            detail='Invalid Webhook signature'
        )
    
    if x_github_event != 'push':
        return {
            "status" : 'ignored',
            "reason" : "unsupported_event"
        }

    data = await request.json()

    repository = data.get('repository')

    if not repository:
        raise HTTPException(
            status_code=400,
            detail='Missing repository information.'
        )

    owner = repository.get("owner", {}).get("login")
    repo = repository.get("name")

    if not owner or not repo:
        raise HTTPException(
            status_code=404,
            detail='Invalid repository information.'
        )

    sync_repository.delay(owner, repo)

    return {
        "status" : "accepted",
        "repository" : f"{owner}/{repo}"
    }