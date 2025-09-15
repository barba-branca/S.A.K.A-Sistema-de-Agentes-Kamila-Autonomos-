import requests
import os
import logging
from typing import Optional
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

# Configura o sistema de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Message(BaseModel):
    sender_id: str
    content: dict

class BaseAgent:
    def __init__(self, agent_id: str, name: str, description: Optional[str] = None, orchestrator_url: str = "http://localhost:8000"):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.orchestrator_url = orchestrator_url

        # O endpoint do próprio agente. Configurável para Local vs. Docker.
        agent_port = os.getenv("AGENT_PORT", "8000")
        agent_host = os.getenv("AGENT_HOST", self.agent_id)
        self.endpoint = os.getenv("AGENT_ENDPOINT", f"http://{agent_host}:{agent_port}")

        self.app = FastAPI()
        self.app.add_api_route("/message", self.handle_message, methods=["POST"])
        self.logger = logging.getLogger(self.name)

    async def handle_message(self, message: Message):
        """A ser sobrescrito por subclasses para lidar com mensagens recebidas."""
        self.logger.info(f"Recebeu mensagem de {message.sender_id}: {message.content}")
        return {"status": "mensagem recebida"}

    def register_with_orchestrator(self):
        """Registra o agente com o Orquestrador."""
        agent_data = {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint
        }
        try:
            self.logger.info(f"Registrando com o orquestrador em {self.orchestrator_url}...")
            response = requests.post(f"{self.orchestrator_url}/agents/register", json=agent_data)
            response.raise_for_status()
            self.logger.info("Registrado com sucesso.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao registrar: {e}")

    def send_message(self, target_agent_id: str, content: dict):
        """Envia uma mensagem para outro agente através do orquestrador."""
        message = {
            "sender_id": self.agent_id,
            "content": content
        }
        try:
            response = requests.post(f"{self.orchestrator_url}/agents/{target_agent_id}/message", json=message.dict())
            response.raise_for_status()
            self.logger.info(f"Mensagem enviada para {target_agent_id} com sucesso.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao enviar mensagem para {target_agent_id}: {e}")

    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Inicia o servidor de API do agente."""
        self.register_with_orchestrator()
        self.logger.info(f"Iniciando servidor em {host}:{port}...")
        uvicorn.run(self.app, host=host, port=port)
