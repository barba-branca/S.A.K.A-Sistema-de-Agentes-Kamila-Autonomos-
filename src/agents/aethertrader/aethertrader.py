import time
from src.core.agent import BaseAgent, Message

class AethertraderAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="aethertrader",
            name="Aethertrader",
            description="Executes trades approved by Kamila.",
            orchestrator_url=orchestrator_url
        )

    async def handle_message(self, message: Message):
        print(f"Aethertrader received a message from {message.sender_id}: {message.content}")
        # Example of sending a reply
        # self.send_message(message.sender_id, {"response": "got your message!"})
        return {"status": "message processed by aethertrader"}
