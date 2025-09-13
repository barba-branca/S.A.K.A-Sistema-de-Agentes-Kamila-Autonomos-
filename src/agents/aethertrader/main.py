import os
from src.agents.aethertrader.aethertrader import AethertraderAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = AethertraderAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
