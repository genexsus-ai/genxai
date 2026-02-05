"""Preset agent wrappers for convenience usage."""

from __future__ import annotations

from typing import Any, Optional

from genxai.core.agent.base import Agent, AgentFactory, AgentType


class AssistantAgent(Agent):
    """Thin wrapper around AgentFactory for assistant-style agents."""

    @classmethod
    def create(
        cls,
        id: str,
        goal: str,
        role: str = "Assistant",
        **kwargs: Any,
    ) -> Agent:
        return AgentFactory.create_agent(
            id=id,
            role=role,
            goal=goal,
            agent_type=kwargs.pop("agent_type", AgentType.DELIBERATIVE),
            **kwargs,
        )


class UserProxyAgent(Agent):
    """Thin wrapper for user-proxy style agents.

    This is intended to be paired with a human-input tool and runtime execution.
    """

    @classmethod
    def create(
        cls,
        id: str,
        goal: str = "Provide user input",
        role: str = "User",
        tools: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        tool_list = tools or []
        return AgentFactory.create_agent(
            id=id,
            role=role,
            goal=goal,
            tools=tool_list,
            agent_type=kwargs.pop("agent_type", AgentType.REACTIVE),
            **kwargs,
        )