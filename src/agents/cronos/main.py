import os
from src.agents.cronos.cronos import CronosAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = CronosAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
