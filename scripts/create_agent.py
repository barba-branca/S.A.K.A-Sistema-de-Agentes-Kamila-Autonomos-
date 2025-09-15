import os
import argparse

def create_agent(name: str, description: str):
    name_lower = name.lower()

    # Cria o diretório do agente
    agent_dir = os.path.join("src", "agents", name_lower)
    os.makedirs(agent_dir, exist_ok=True)

    # Cria o arquivo __init__.py
    init_path = os.path.join(agent_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            pass

    # Cria o arquivo da classe do agente
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
        self.logger.info(f"Recebeu mensagem de {{message.sender_id}}: {{message.content}}")
        # Adicione a lógica específica do agente aqui
        return {{"status": "mensagem processada por {name_lower}"}}
"""
    # Tratamento especial para o arquivo da Kamila (que é um pouco diferente)
    if name_lower == 'kamila':
        agent_class_content = """import time
from src.core.agent import BaseAgent, Message
from src.core.whatsapp_service import send_whatsapp_message

class KamilaAgent(BaseAgent):
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        super().__init__(
            agent_id="kamila",
            name="Kamila",
            description="A CEO da S.A.K.A. Ela coordena todos os agentes e toma as decisões finais.",
            orchestrator_url=orchestrator_url
        )

    def send_daily_report(self):
        self.logger.info("Gerando o relatório diário...")
        report_body = (
            "📈 *Relatório Diário S.A.K.A.*\\n\\n"
            "Bom dia! Segue o resumo das atividades de hoje:\\n\\n"
            "- *Sentimento de Mercado (Athena)*: Cautelosamente Otimista\\n"
            "- *Cenário Macro (Orion)*: Estável, com potencial de alta nos juros.\\n"
            "- *Trades Executados (Aethertrader)*: 3\\n"
            "- *P&L do Portfólio*: +0.5%\\n"
            "- *Nível de Risco Atual (Sentinel)*: Baixo\\n\\n"
            "Tenha um dia produtivo!"
        )
        send_whatsapp_message(body=report_body)

    async def handle_message(self, message: Message):
        self.logger.info(f"Recebeu uma mensagem de {message.sender_id}: {message.content}")
        content = message.content
        if content.get("command") == "generate_report":
            self.send_daily_report()
            return {"status": "Geração de relatório iniciada."}
        return {"status": f"Comando '{content.get('command')}' não reconhecido."}
"""

    with open(os.path.join(agent_dir, f"{name_lower}.py"), "w") as f:
        f.write(agent_class_content)

    # Cria o arquivo main.py
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

    print(f"Agente {name} criado/atualizado com sucesso em {agent_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cria ou atualiza um agente S.A.K.A.")
    parser.add_argument("name", type=str, help="O nome do agente (ex: Athena). Deve ser capitalizado.")
    parser.add_argument("description", type=str, help="Uma breve descrição do agente.")
    args = parser.parse_args()
    create_agent(args.name, args.description)
