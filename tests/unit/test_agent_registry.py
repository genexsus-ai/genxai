"""Tests for agent registry."""

import pytest
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry


def test_agent_registry_register():
    """Test registering an agent."""
    AgentRegistry.clear()
    
    agent = AgentFactory.create_agent(
        id="test_agent",
        role="Test",
        goal="Test",
        llm_model="gpt-4"
    )
    
    AgentRegistry.register(agent)
    
    assert AgentRegistry.get("test_agent") is not None
    AgentRegistry.clear()


def test_agent_registry_get():
    """Test getting an agent from registry."""
    AgentRegistry.clear()
    
    agent = AgentFactory.create_agent(
        id="test_agent",
        role="Test",
        goal="Test",
        llm_model="gpt-4"
    )
    
    AgentRegistry.register(agent)
    retrieved = AgentRegistry.get("test_agent")
    
    assert retrieved is not None
    assert retrieved.id == "test_agent"
    AgentRegistry.clear()


def test_agent_registry_get_nonexistent():
    """Test getting nonexistent agent."""
    AgentRegistry.clear()
    result = AgentRegistry.get("nonexistent")
    assert result is None


def test_agent_registry_list_all():
    """Test listing all agents."""
    AgentRegistry.clear()
    
    agent1 = AgentFactory.create_agent(id="agent1", role="Test", goal="Test", llm_model="gpt-4")
    agent2 = AgentFactory.create_agent(id="agent2", role="Test", goal="Test", llm_model="gpt-4")
    
    AgentRegistry.register(agent1)
    AgentRegistry.register(agent2)
    
    all_agents = AgentRegistry.list_all()
    assert len(all_agents) == 2
    AgentRegistry.clear()


def test_agent_registry_clear():
    """Test clearing registry."""
    AgentRegistry.clear()
    
    agent = AgentFactory.create_agent(id="test", role="Test", goal="Test", llm_model="gpt-4")
    AgentRegistry.register(agent)
    
    AgentRegistry.clear()
    assert len(AgentRegistry.list_all()) == 0


def test_agent_registry_unregister():
    """Test unregistering an agent."""
    AgentRegistry.clear()
    
    agent = AgentFactory.create_agent(id="test", role="Test", goal="Test", llm_model="gpt-4")
    AgentRegistry.register(agent)
    
    AgentRegistry.unregister("test")
    assert AgentRegistry.get("test") is None
    AgentRegistry.clear()
