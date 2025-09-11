import os
import argparse

def create_agent(name: str, description: str):
    name_lower = name.lower()
    # name_capitalized is removed, we will use 'name' directly for the class name

    # Create directory
    agent_dir = os.path.join("src", "agents", name_lower)
    os.makedirs(agent_dir, exist_ok=True)

    # Create __init__.py
    init_path = os.path.join(agent_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            pass

    # Create agent class file
    agent_class_content = f"""import time
from src.core.agent import BaseAgent, Message

class {name}Agent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="{name_lower}",
            name="{name}",
            description="{description}",
            orchestrator_url=orchestrator_url
        )

    async def handle_message(self, message: Message):
        print(f"{name} received a message from {{message.sender_id}}: {{message.content}}")
        # Add agent-specific logic here
        return {{"status": "message processed by {name_lower}"}}
"""
    # Special handling for Kamila's file (which is now slightly different)
    if name_lower == 'kamila':
        agent_class_content = """import time
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
        self.logger.info(f"Received a message from {message.sender_id}: {message.content}")
        content = message.content
        if content.get("command") == "generate_report":
            self.send_daily_report()
            return {"status": "Report generation initiated."}
        return {"status": f"Command '{content.get('command')}' not recognized."}
"""

    with open(os.path.join(agent_dir, f"{name_lower}.py"), "w") as f:
        f.write(agent_class_content)

    # Create main.py
    main_py_content = f"""import os
from src.agents.{name_lower}.{name_lower} import {name}Agent

if __name__ == "__main__":
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
    agent_port = int(os.getenv("AGENT_PORT", "8000"))
    agent = {name}Agent(orchestrator_url=orchestrator_url)
    agent.start_server(port=agent_port)
"""
    with open(os.path.join(agent_dir, "main.py"), "w") as f:
        f.write(main_py_content)

    print(f"Agent {name} created/updated successfully in {agent_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or update a S.A.K.A. agent.")
    parser.add_argument("name", type=str, help="The name of the agent (e.g., Athena). Should be capitalized.")
    parser.add_argument("description", type=str, help="A short description of the agent.")
    args = parser.parse_args()
    create_agent(args.name, args.description)
