import pytest
from src.orchestrator.agent_registry import AgentRegistry
from src.orchestrator.models import Agent

@pytest.fixture
def registry():
    """Provides a clean AgentRegistry instance for each test."""
    return AgentRegistry()

def test_register_agent(registry: AgentRegistry):
    assert len(registry.list_agents()) == 0
    agent = Agent(id="test01", name="Test Agent", endpoint="http://localhost:8001")
    registry.register_agent(agent)
    assert len(registry.list_agents()) == 1
    assert registry.get_agent("test01") == agent

def test_register_duplicate_agent_raises_error(registry: AgentRegistry):
    agent1 = Agent(id="test01", name="Test Agent 1", endpoint="http://localhost:8001")
    agent2 = Agent(id="test01", name="Test Agent 2", endpoint="http://localhost:8002")
    registry.register_agent(agent1)
    with pytest.raises(ValueError, match="already registered"):
        registry.register_agent(agent2)

def test_unregister_agent(registry: AgentRegistry):
    agent = Agent(id="test01", name="Test Agent", endpoint="http://localhost:8001")
    registry.register_agent(agent)
    assert len(registry.list_agents()) == 1

    registry.unregister_agent("test01")
    assert len(registry.list_agents()) == 0

def test_unregister_nonexistent_agent_raises_error(registry: AgentRegistry):
    with pytest.raises(ValueError, match="not found"):
        registry.unregister_agent("nonexistent")

def test_get_agent(registry: AgentRegistry):
    agent = Agent(id="test01", name="Test Agent", endpoint="http://localhost:8001")
    registry.register_agent(agent)
    retrieved_agent = registry.get_agent("test01")
    assert retrieved_agent == agent

def test_get_nonexistent_agent_raises_error(registry: AgentRegistry):
    with pytest.raises(ValueError, match="not found"):
        registry.get_agent("nonexistent")

def test_list_agents(registry: AgentRegistry):
    agent1 = Agent(id="test01", name="Test Agent 1", endpoint="http://localhost:8001")
    agent2 = Agent(id="test02", name="Test Agent 2", endpoint="http://localhost:8002")

    assert registry.list_agents() == []

    registry.register_agent(agent1)
    assert registry.list_agents() == [agent1]

    registry.register_agent(agent2)
    # The order is not guaranteed, so we compare sets
    assert set(registry.list_agents()) == {agent1, agent2}
