import os
from src.agents.athena.athena import AthenaAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = AthenaAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
