import os
from src.agents.orion.orion import OrionAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = OrionAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
