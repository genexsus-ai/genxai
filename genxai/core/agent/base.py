"""Base agent class and configuration."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents."""

    REACTIVE = "reactive"
    DELIBERATIVE = "deliberative"
    LEARNING = "learning"
    COLLABORATIVE = "collaborative"
    AUTONOMOUS = "autonomous"


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    model_config = ConfigDict(use_enum_values=True)

    role: str = Field(..., description="Role of the agent")
    goal: str = Field(..., description="Goal the agent should achieve")
    backstory: str = Field(default="", description="Background story for the agent")
    
    # LLM configuration
    llm_provider: str = Field(default="openai", description="LLM provider to use")
    llm_model: str = Field(default="gpt-4", description="LLM model name")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: Optional[int] = Field(default=None, description="Max tokens for response")
    
    # Tools
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    allow_tool_creation: bool = Field(default=False, description="Allow dynamic tool creation")
    
    # Memory
    enable_memory: bool = Field(default=True, description="Enable memory system")
    memory_type: str = Field(default="short_term", description="Type of memory to use")
    
    # Behavior
    agent_type: AgentType = Field(default=AgentType.REACTIVE)
    max_iterations: int = Field(default=10, description="Max iterations for agent execution")
    verbose: bool = Field(default=False, description="Enable verbose logging")

    # Ranking
    enable_llm_ranking: bool = Field(
        default=False,
        description="Enable LLM-based ranking utility for downstream selection",
    )
    
    # Guardrails
    max_execution_time: Optional[float] = Field(default=None, description="Max execution time in seconds")
    allowed_domains: List[str] = Field(default_factory=list, description="Allowed domains for web access")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)



class Agent(BaseModel):
    """Base agent class."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    id: str = Field(..., description="Unique agent identifier")
    config: AgentConfig
    
    # Runtime state
    _execution_count: int = 0
    _total_tokens: int = 0
    _last_result: Optional[Any] = None


    def __init__(self, id: str, config: AgentConfig, **kwargs: Any) -> None:
        """Initialize agent.

        Args:
            id: Agent identifier
            config: Agent configuration
            **kwargs: Additional arguments
        """
        super().__init__(id=id, config=config, **kwargs)
        logger.info(f"Agent initialized: {self.id} (role: {self.config.role})")

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task.

        This is a placeholder that will be implemented by AgentRuntime.

        Args:
            task: Task description
            context: Execution context

        Returns:
            Execution result
        """
        self._execution_count += 1
        
        logger.info(f"Agent {self.id} executing task: {task}")
        
        # Placeholder implementation
        result = {
            "agent_id": self.id,
            "task": task,
            "status": "completed",
            "output": f"Agent {self.config.role} processed: {task}",
            "execution_count": self._execution_count,
        }
        
        self._last_result = result
        return result

    async def reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on execution result.

        Args:
            result: Execution result to reflect on

        Returns:
            Reflection insights
        """
        logger.debug(f"Agent {self.id} reflecting on result")
        
        return {
            "agent_id": self.id,
            "reflection": "Reflection placeholder",
            "improvements": [],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics.

        Returns:
            Agent statistics
        """
        return {
            "id": self.id,
            "role": self.config.role,
            "execution_count": self._execution_count,
            "total_tokens": self._total_tokens,
            "agent_type": self.config.agent_type,
        }

    def reset_stats(self) -> None:
        """Reset agent statistics."""
        self._execution_count = 0
        self._total_tokens = 0
        self._last_result = None
        logger.info(f"Agent {self.id} statistics reset")

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "config": self.config.dict(),
            "stats": self.get_stats(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"Agent(id={self.id}, role={self.config.role}, type={self.config.agent_type})"


class AgentFactory:
    """Factory for creating agents."""

    @staticmethod
    def create_agent(
        id: str,
        role: str,
        goal: str,
        **kwargs: Any,
    ) -> Agent:
        """Create an agent with given configuration.

        Args:
            id: Agent identifier
            role: Agent role
            goal: Agent goal
            **kwargs: Additional configuration

        Returns:
            Configured agent
        """
        config = AgentConfig(
            role=role,
            goal=goal,
            **kwargs,
        )
        
        return Agent(id=id, config=config)

    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> Agent:
        """Create agent from dictionary.

        Args:
            data: Agent data

        Returns:
            Agent instance
        """
        config = AgentConfig(**data.get("config", {}))
        return Agent(id=data["id"], config=config)
