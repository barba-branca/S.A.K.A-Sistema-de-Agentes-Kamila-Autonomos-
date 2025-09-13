# S.A.K.A. - Sistema de Agentes Kamila Autônomos

S.A.K.A. é uma prova de conceito de uma startup de IA autônoma composta por múltiplos agentes especializados. O sistema foi projetado para ser uma plataforma escalável e modular para desenvolver e coordenar agentes de IA em tarefas complexas, como trading automatizado.

Cada agente executa em um contêiner Docker isolado e se comunica através de um Orquestrador central, tornando o sistema robusto e escalável.

## Estrutura do Projeto

O projeto está organizado nos seguintes diretórios principais:

-   `src/`: Contém todo o código-fonte em Python.
    -   `src/orchestrator/`: O serviço do Orquestrador central que gerencia os agentes e roteia a comunicação.
    -   `src/agents/`: Cada subdiretório contém a implementação de um agente específico (ex: `kamila`, `orion`).
    -   `src/core/`: Componentes compartilhados, incluindo a classe `BaseAgent` e outros serviços centrais, como a integração com o WhatsApp.
-   `tests/`: Contém testes unitários para o projeto.
-   `scripts/`: Armazena scripts utilitários, como o `create_agent.py` para gerar o código base de novos agentes.
-   `docs/`: Para documentação detalhada sobre a arquitetura e o design do projeto.
-   `config/`: Destinado a arquivos de configuração (atualmente não utilizado).

## Como Começar

### Pré-requisitos

-   Python 3.9+
-   Docker e Docker Compose
-   `pip` para instalar pacotes Python

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url_do_repositorio>
    cd <diretorio_do_repositorio>
    ```

2.  **Instale as dependências:**
    Todos os pacotes Python necessários estão listados em `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### Executando o Sistema (Docker)

A maneira recomendada de executar o S.A.K.A. é usando o Docker Compose, que orquestra a configuração de múltiplos contêineres.

```bash
sudo docker compose up --build -d
```

Este comando irá:
-   Construir as imagens Docker para o Orquestrador e os agentes.
-   Iniciar todos os serviços definidos no `docker-compose.yml` em modo `detached`.
-   Configurar uma rede dedicada para a comunicação entre os serviços.

Você pode visualizar os logs de todos os serviços em execução com:
```bash
sudo docker compose logs -f
```

Para parar o sistema:
```bash
sudo docker compose down
```

### Executando para Desenvolvimento Local

Para desenvolvimento e testes, você pode executar os serviços localmente sem o Docker.

1.  **Inicie o Orquestrador:**
    Abra um terminal e execute:
    ```bash
    uvicorn src.orchestrator.main:app --host 0.0.0.0 --port 8000
    ```

2.  **Inicie um Agente (ex: Kamila):**
    Abra um segundo terminal. Você precisa definir variáveis de ambiente para que o agente possa ser alcançado pelo Orquestrador em `localhost`.
    ```bash
    export AGENT_HOST="localhost"
    export AGENT_PORT="8001" # Use uma porta diferente para cada agente
    export PYTHONPATH=.
    python -m src.agents.kamila.main
    ```

## Criando um Novo Agente

Um script auxiliar é fornecido para gerar rapidamente o código base para um novo agente.

```bash
python scripts/create_agent.py <NomeDoAgente> "<Descrição do Agente>"
```

**Exemplo:**
```bash
python scripts/create_agent.py Apollo "Um agente para analisar dados de erupções solares."
```

Isso criará:
-   `src/agents/apollo/`
-   `src/agents/apollo/__init__.py`
-   `src/agents/apollo/apollo.py` (o arquivo da classe do agente)
-   `src/agents/apollo/main.py` (o ponto de entrada do agente)

Após criar o agente, você pode adicioná-lo como um novo serviço no arquivo `docker-compose.yml` para integrá-lo ao sistema.
