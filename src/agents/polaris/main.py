import os
from src.agents.polaris.polaris import PolarisAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = PolarisAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
