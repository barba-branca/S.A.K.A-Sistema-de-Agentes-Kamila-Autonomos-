import os
from src.agents.gaia.gaia import GaiaAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = GaiaAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
