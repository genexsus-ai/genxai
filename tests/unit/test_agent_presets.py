"""Tests for preset agent wrappers."""

from genxai.agents.presets import AssistantAgent, UserProxyAgent
from genxai.core.agent.base import AgentType


def test_assistant_agent_defaults():
    assistant = AssistantAgent.create(id="assistant", goal="Help")
    assert assistant.id == "assistant"
    assert assistant.config.role == "Assistant"
    assert assistant.config.goal == "Help"
    assert assistant.config.agent_type == AgentType.DELIBERATIVE


def test_user_proxy_agent_defaults():
    user_proxy = UserProxyAgent.create(id="user_proxy")
    assert user_proxy.id == "user_proxy"
    assert user_proxy.config.role == "User"
    assert user_proxy.config.goal == "Provide user input"
    assert user_proxy.config.agent_type == AgentType.REACTIVE


def test_user_proxy_agent_tools_override():
    user_proxy = UserProxyAgent.create(id="user_proxy", tools=["human_input"])
    assert user_proxy.config.tools == ["human_input"]