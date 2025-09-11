# S.A.K.A. System Architecture

This document provides a detailed overview of the S.A.K.A. system architecture, its core components, and the communication flow between them.

## High-Level Overview

S.A.K.A. is designed as a distributed, multi-agent system. The architecture is centered around a central **Orchestrator** that manages a fleet of specialized **Agents**. Each component (the orchestrator and every agent) runs in its own isolated Docker container, ensuring scalability and separation of concerns.

The core principles of the architecture are:
-   **Modularity:** Each agent is a self-contained unit with a specific purpose.
-   **Scalability:** The containerized nature allows for running multiple instances of agents or adding new agents easily.
-   **Centralized Coordination:** The Orchestrator acts as a service discovery and communication hub, preventing a "spaghetti" of direct agent-to-agent connections.
-   **Event-Driven Communication:** Agents primarily react to messages and events, allowing for asynchronous operations.

### System Flowchart

The system follows a hierarchical structure where Kamila (CEO) coordinates the other agents. The Orchestrator facilitates the communication and management of these agents.

*(The user provided a flowchart image that illustrates this structure. Kamila is at the top, receiving input from Orion (CFO) and advising Polaris. Orion, in turn, gets data from Sentinel (Risk), Gaia (Diversification), and Aethertrader. Aethertrader is assisted by Athena (Sentiment) and Hermes (Execution). The Orchestrator is a central service that interacts with all agents for management and logging.)*

## Core Components

### 1. Orchestrator

The Orchestrator is the central nervous system of S.A.K.A. It is a FastAPI application with several key responsibilities:

-   **Agent Registry:** It maintains a dynamic list of all active agents, including their IDs, names, and API endpoints.
-   **Service Discovery:** When one agent wants to communicate with another, it asks the Orchestrator for the target's location.
-   **Message Routing:** It exposes an endpoint (`/agents/{target_agent_id}/message`) that allows agents to send messages to each other without needing to know their direct network addresses. The Orchestrator forwards the message to the correct agent.
-   **Agent Lifecycle Management:** The Orchestrator is designed to be the component through which Kamila will eventually create and terminate other agents automatically.

### 2. Agents

Each agent is a Python application built upon the `BaseAgent` class. This base class provides the common functionality needed to operate within the S.A.K.A. ecosystem.

-   **`BaseAgent` Class:** Found in `src/core/agent.py`, this class provides:
    -   An integrated FastAPI server to receive messages.
    -   A `register_with_orchestrator()` method to announce its presence.
    -   A `send_message()` method to communicate with other agents via the Orchestrator.

-   **Specialized Agents:** Each agent inherits from `BaseAgent` and implements its own specific logic, primarily within the `handle_message` method.

#### Agent Roles:

-   **Kamila (CEO):** The primary decision-making agent. She coordinates the other agents, validates strategies, and is responsible for sending daily reports.
-   **Polaris (Advisor):** A strategic advisor. Kamila consults Polaris before executing critical decisions.
-   **Orion (CFO/Macro Analyst):** Analyzes macroeconomic data, news, and financial reports to provide strategic input.
-   **Aethertrader (Trade Manager):** Responsible for executing trades that have been approved by Kamila.
-   **Athena (Sentiment Analyst):** Scans news and social media to gauge market sentiment.
-   **Sentinel (Risk Manager):** Monitors the portfolio for risk, managing stop-losses and overall exposure.
-   **Hermes (Execution Optimizer):** A specialist agent that assists Aethertrader by finding the optimal way to execute a trade, minimizing slippage.
-   **Cronos (Temporal Analyst):** Analyzes market cycles and timing to avoid trading in unfavorable conditions.
-   **Gaia (Diversification Manager):** Manages a separate, diversified portfolio to generate passive revenue and reduce overall drawdown.

## Inter-Agent Communication Flow

1.  **Registration:** When an agent starts, it calls `register_with_orchestrator()`, sending its ID, name, and endpoint (e.g., `http://kamila:8000`) to the Orchestrator.
2.  **Message Sending:** Agent A wants to send a message to Agent B.
3.  Agent A calls its own `send_message("agent-b", {"key": "value"})` method.
4.  This method constructs a POST request to the Orchestrator's endpoint: `http://orchestrator:8000/agents/agent-b/message`.
5.  **Message Forwarding:** The Orchestrator receives the request. It looks up "agent-b" in its registry to find its endpoint (e.g., `http://agent-b:8000`).
6.  The Orchestrator forwards the message by making a POST request to `http://agent-b:8000/message`.
7.  **Message Reception:** Agent B's integrated FastAPI server receives the message at its `/message` endpoint.
8.  The `handle_message` method in Agent B is triggered, allowing it to process the message and take action.
