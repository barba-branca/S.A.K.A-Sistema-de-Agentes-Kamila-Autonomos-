import os
import shutil
import subprocess

AGENT_NAME = "AgenteDeTeste"
AGENT_NAME_LOWER = "agentedeteste"
AGENT_DESC = "Um agente temporário para testes."
AGENT_DIR = os.path.join("src", "agents", AGENT_NAME_LOWER)

def run_create_agent_script():
    """Função auxiliar para executar o script."""
    subprocess.run(
        ["python", "scripts/create_agent.py", AGENT_NAME, AGENT_DESC],
        check=True,
        capture_output=True,
        text=True
    )

def cleanup_agent_files():
    """Função auxiliar para limpar os arquivos criados."""
    if os.path.exists(AGENT_DIR):
        shutil.rmtree(AGENT_DIR)

def test_create_agent_script_creates_directory_and_files():
    """Testa se o script cria o diretório e os arquivos corretamente."""
    cleanup_agent_files() # Garante um estado limpo
    try:
        run_create_agent_script()
        assert os.path.isdir(AGENT_DIR)
        assert os.path.isfile(os.path.join(AGENT_DIR, "__init__.py"))
        assert os.path.isfile(os.path.join(AGENT_DIR, f"{AGENT_NAME_LOWER}.py"))
        assert os.path.isfile(os.path.join(AGENT_DIR, "main.py"))
    finally:
        cleanup_agent_files() # Limpa após o teste

def test_create_agent_script_generates_correct_content():
    """Testa se o script gera o conteúdo correto nos arquivos."""
    cleanup_agent_files() # Garante um estado limpo
    try:
        run_create_agent_script()

        # Verifica o conteúdo do main.py
        with open(os.path.join(AGENT_DIR, "main.py"), "r") as f:
            content = f.read()
            assert f"from src.agents.{AGENT_NAME_LOWER}.{AGENT_NAME_LOWER} import {AGENT_NAME}Agent" in content
            assert f"agent = {AGENT_NAME}Agent(orchestrator_url=orchestrator_url)" in content

        # Verifica o conteúdo do arquivo da classe do agente
        with open(os.path.join(AGENT_DIR, f"{AGENT_NAME_LOWER}.py"), "r") as f:
            content = f.read()
            assert f"class {AGENT_NAME}Agent(BaseAgent):" in content
            assert f'agent_id="{AGENT_NAME_LOWER}"' in content
            assert f'name="{AGENT_NAME}"' in content
            assert f'description="{AGENT_DESC}"' in content

    finally:
        cleanup_agent_files()
