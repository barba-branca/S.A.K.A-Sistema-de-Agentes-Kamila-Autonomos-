import os
from src.agents.kamila.kamila import KamilaAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent_port = int(os.getenv("AGENT_PORT", "8000"))
    agent = KamilaAgent(orchestrator_url=orchestrator_url)
    agent.start_server(port=agent_port)
