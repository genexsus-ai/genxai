"""Agent registry for managing agent instances."""

from typing import Dict, Optional, List
import logging

from genxai.core.agent.base import Agent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Global registry for managing agent instances."""

    _agents: Dict[str, Agent] = {}

    @classmethod
    def register(cls, agent: Agent) -> None:
        """Register an agent.

        Args:
            agent: Agent instance to register

        Raises:
            ValueError: If agent with same ID already exists
        """
        if agent.id in cls._agents:
            logger.warning(f"Agent '{agent.id}' already registered, overwriting")
        
        cls._agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.id} (role: {agent.config.role})")

    @classmethod
    def get(cls, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance if found, None otherwise
        """
        agent = cls._agents.get(agent_id)
        if agent is None:
            logger.warning(f"Agent '{agent_id}' not found in registry")
        return agent

    @classmethod
    def unregister(cls, agent_id: str) -> bool:
        """Unregister an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was unregistered, False if not found
        """
        if agent_id in cls._agents:
            del cls._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    @classmethod
    def list_all(cls) -> List[str]:
        """List all registered agent IDs.

        Returns:
            List of agent IDs
        """
        return list(cls._agents.keys())

    @classmethod
    def get_all(cls) -> Dict[str, Agent]:
        """Get all registered agents.

        Returns:
            Dictionary of agent ID to agent instance
        """
        return cls._agents.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents."""
        count = len(cls._agents)
        cls._agents.clear()
        logger.info(f"Cleared {count} agents from registry")

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        return {
            "total_agents": len(cls._agents),
            "agent_ids": cls.list_all(),
        }
