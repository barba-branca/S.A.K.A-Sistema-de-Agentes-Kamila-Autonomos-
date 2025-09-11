import time
from src.core.agent import BaseAgent, Message

class OrionAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="orion",
            name="Orion",
            description="Analyzes macroeconomic trends and financial reports.",
            orchestrator_url=orchestrator_url
        )

    async def handle_message(self, message: Message):
        print(f"Orion received a message from {message.sender_id}: {message.content}")
        # Example of sending a reply
        # self.send_message(message.sender_id, {"response": "got your message!"})
        return {"status": "message processed by orion"}
