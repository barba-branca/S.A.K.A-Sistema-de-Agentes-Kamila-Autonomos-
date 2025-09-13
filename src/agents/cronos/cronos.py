import time
from src.core.agent import BaseAgent, Message

class CronosAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="cronos",
            name="Cronos",
            description="Analyzes temporal cycles to avoid unfavorable trading periods.",
            orchestrator_url=orchestrator_url
        )

    async def handle_message(self, message: Message):
        print(f"Cronos received a message from {message.sender_id}: {message.content}")
        # Example of sending a reply
        # self.send_message(message.sender_id, {"response": "got your message!"})
        return {"status": "message processed by cronos"}
