import os
from src.agents.hermes.hermes import HermesAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = HermesAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
