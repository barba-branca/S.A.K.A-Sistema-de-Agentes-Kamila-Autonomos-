import os
from src.agents.sentinel.sentinel import SentinelAgent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent = SentinelAgent(orchestrator_url=orchestrator_url)
    agent.start_server()
