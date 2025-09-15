from typing import Dict
from .models import Agent

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        if agent.id in self.agents:
            raise ValueError(f"Agente com id {agent.id} já registrado.")
        self.agents[agent.id] = agent

    def unregister_agent(self, agent_id: str):
        if agent_id not in self.agents:
            raise ValueError(f"Agente com id {agent_id} não encontrado.")
        del self.agents[agent_id]

    def get_agent(self, agent_id: str) -> Agent:
        if agent_id not in self.agents:
            raise ValueError(f"Agente com id {agent_id} não encontrado.")
        return self.agents[agent_id]

    def list_agents(self):
        return list(self.agents.values())

agent_registry = AgentRegistry()
