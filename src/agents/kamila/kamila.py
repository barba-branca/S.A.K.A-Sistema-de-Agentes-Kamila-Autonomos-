import time
from src.core.agent import BaseAgent, Message
from src.core.whatsapp_service import send_whatsapp_message

class KamilaAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="kamila",
            name="Kamila",
            description="The CEO of S.A.K.A. She coordinates all agents and makes final decisions.",
            orchestrator_url=orchestrator_url
        )

    def send_daily_report(self):
        """Generates and sends a daily report via WhatsApp."""
        self.logger.info("Generating the daily report...")
        report_body = (
            "📈 *S.A.K.A. Daily Report*\\n\\n"
            "Good morning! Here is a summary of today's activities:\\n\\n"
            "- *Market Sentiment (Athena)*: Cautiously Optimistic\\n"
            "- *Macro Outlook (Orion)*: Stable, with potential interest rate hikes.\\n"
            "- *Trades Executed (Aethertrader)*: 3\\n"
            "- *Portfolio P&L*: +0.5%\\n"
            "- *Current Risk Level (Sentinel)*: Low\\n\\n"
            "Have a productive day!"
        )
        send_whatsapp_message(body=report_body)


    async def handle_message(self, message: Message):
        """Handles incoming messages for Kamila."""
        self.logger.info(f"Received a message from {message.sender_id}: {message.content}")

        content = message.content
        if content.get("command") == "generate_report":
            self.send_daily_report()
            return {"status": "Report generation initiated."}

        if content.get("command") == "status_check":
            self.send_message("orion", {"query": "What is the current market outlook?"})
            return {"status": "Status check initiated. Asking Orion for outlook."}

        return {"status": f"Command '{content.get('command')}' not recognized."}
