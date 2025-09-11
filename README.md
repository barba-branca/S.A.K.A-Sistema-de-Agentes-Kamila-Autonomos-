# S.A.K.A. - Sistema de Agentes Kamila Autônomos

S.A.K.A. is a proof-of-concept autonomous AI startup composed of multiple specialized agents. The system is designed to be a scalable and modular platform for developing and coordinating AI agents for complex tasks, such as automated trading.

Each agent runs in an isolated Docker container and communicates through a central Orchestrator, making the system robust and scalable.

## Project Structure

The project is organized into the following main directories:

-   `src/`: Contains all the Python source code.
    -   `src/orchestrator/`: The central Orchestrator service that manages agents and routes communication.
    -   `src/agents/`: Each subdirectory contains the implementation of a specific agent (e.g., `kamila`, `orion`).
    -   `src/core/`: Shared components, including the `BaseAgent` class and other core services like the WhatsApp integration.
-   `tests/`: Contains unit tests for the project.
-   `scripts/`: Holds utility scripts, such as the `create_agent.py` script for generating new agent boilerplate.
-   `docs/`: For detailed documentation about the project's architecture and design.
-   `config/`: Intended for configuration files (currently unused).

## Getting Started

### Prerequisites

-   Python 3.9+
-   Docker and Docker Compose
-   `pip` for installing Python packages

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    All required Python packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

### Running the System (Docker)

The recommended way to run S.A.K.A. is by using Docker Compose, which orchestrates the multi-container setup.

```bash
sudo docker compose up --build -d
```

This command will:
-   Build the Docker images for the Orchestrator and the agents.
-   Start all services defined in `docker-compose.yml` in detached mode.
-   Set up a dedicated network for inter-service communication.

You can view the logs of all running services with:
```bash
sudo docker compose logs -f
```

To stop the system:
```bash
sudo docker compose down
```

### Running for Local Development

For development and testing, you can run the services locally without Docker.

1.  **Start the Orchestrator:**
    Open a terminal and run:
    ```bash
    uvicorn src.orchestrator.main:app --host 0.0.0.0 --port 8000
    ```

2.  **Start an Agent (e.g., Kamila):**
    Open a second terminal. You need to set environment variables so the agent can be reached by the Orchestrator on `localhost`.
    ```bash
    export AGENT_HOST="localhost"
    export AGENT_PORT="8001" # Use a different port for each agent
    export PYTHONPATH=.
    python -m src.agents.kamila.main
    ```

## Creating a New Agent

A helper script is provided to quickly generate the boilerplate code for a new agent.

```bash
python scripts/create_agent.py <AgentName> "<Agent Description>"
```

**Example:**
```bash
python scripts/create_agent.py Apollo "An agent for analyzing solar flare data."
```

This will create:
-   `src/agents/apollo/`
-   `src/agents/apollo/__init__.py`
-   `src/agents/apollo/apollo.py` (the agent's class file)
-   `src/agents/apollo/main.py` (the agent's entrypoint)

After creating the agent, you can add it as a new service in the `docker-compose.yml` file to integrate it into the system.
