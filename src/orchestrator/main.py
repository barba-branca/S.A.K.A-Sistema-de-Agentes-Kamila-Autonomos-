from fastapi import FastAPI, HTTPException
from typing import List
import requests

from src.orchestrator.agent_registry import agent_registry
from src.orchestrator.models import Agent
from src.core.agent import Message # Importing from core

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "S.A.K.A. Orchestrator is running."}

# Agent management endpoints
@app.post("/agents/register", status_code=201)
def register_agent(agent: Agent):
    try:
        agent_registry.register_agent(agent)
        return {"message": f"Agent {agent.name} registered successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/unregister/{agent_id}")
def unregister_agent(agent_id: str):
    try:
        agent_registry.unregister_agent(agent_id)
        return {"message": f"Agent {agent_id} unregistered successfully."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/agents/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    try:
        return agent_registry.get_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/agents", response_model=List[Agent])
def list_agents():
    return agent_registry.list_agents()

# Inter-agent communication endpoint
@app.post("/agents/{target_agent_id}/message")
def send_agent_message(target_agent_id: str, message: Message):
    try:
        target_agent = agent_registry.get_agent(target_agent_id)

        # Forward the message to the target agent
        try:
            response = requests.post(f"{target_agent.endpoint}/message", json=message.dict())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Error forwarding message to agent {target_agent_id}: {e}")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
