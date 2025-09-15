from fastapi import FastAPI, HTTPException
from typing import List
import requests

from src.orchestrator.agent_registry import agent_registry
from src.orchestrator.models import Agent
from src.core.agent import Message # Importando do core

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "S.A.K.A. Orchestrator está em execução."}

# Endpoints de gerenciamento de agentes
@app.post("/agents/register", status_code=201)
def register_agent(agent: Agent):
    try:
        agent_registry.register_agent(agent)
        return {"message": f"Agente {agent.name} registrado com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/unregister/{agent_id}")
def unregister_agent(agent_id: str):
    try:
        agent_registry.unregister_agent(agent_id)
        return {"message": f"Agente {agent_id} desregistrado com sucesso."}
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

# Endpoint de comunicação entre agentes
@app.post("/agents/{target_agent_id}/message")
def send_agent_message(target_agent_id: str, message: Message):
    try:
        target_agent = agent_registry.get_agent(target_agent_id)

        # Encaminha a mensagem para o agente de destino
        try:
            response = requests.post(f"{target_agent.endpoint}/message", json=message.dict())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Erro ao encaminhar mensagem para o agente {target_agent_id}: {e}")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
