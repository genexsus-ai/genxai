"""Node types and implementations for graph-based orchestration."""

from enum import Enum
from typing import Any, Dict, Optional, Protocol
from pydantic import BaseModel, Field, ConfigDict


class NodeType(str, Enum):
    """Types of nodes in the graph."""

    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    SUBGRAPH = "subgraph"
    HUMAN = "human"
    INPUT = "input"
    OUTPUT = "output"
    LOOP = "loop"


class NodeConfig(BaseModel):
    """Configuration for a node."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    type: NodeType
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeStatus(str, Enum):
    """Execution status of a node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Node(BaseModel):
    """Base node in the execution graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    type: NodeType
    config: NodeConfig
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


    def __repr__(self) -> str:
        """String representation of the node."""
        return f"Node(id={self.id}, type={self.type}, status={self.status})"

    def __hash__(self) -> int:
        """Hash function for node."""
        return hash(self.id)


class NodeExecutor(Protocol):
    """Protocol for node execution."""

    async def execute(self, node: Node, context: Dict[str, Any]) -> Any:
        """Execute the node with given context."""
        ...


class AgentNode(Node):
    """Node that executes an agent."""

    def __init__(
        self,
        id: str,
        agent_id: Optional[str] = None,
        agent: Optional[Any] = None,
        task: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize agent node.

        This supports two construction styles:
        1) Internal graph API: AgentNode(id="x", agent_id="agent_x")
        2) Integration-test/user API: AgentNode(id="x", agent=<Agent>, task="...")

        When `agent` is provided, we register it into AgentRegistry to make
        it discoverable by the execution layer.
        """
        # Lazy import to avoid circular imports
        from genxai.core.agent.registry import AgentRegistry

        resolved_agent_id = agent_id
        if agent is not None:
            resolved_agent_id = agent.id
            # Ensure agent is registered so EnhancedGraph can look it up.
            try:
                AgentRegistry.register(agent)
            except Exception:
                # If already registered, ignore.
                pass

        if not resolved_agent_id:
            raise TypeError("AgentNode requires either agent_id or agent")

        data: Dict[str, Any] = {"agent_id": resolved_agent_id}
        if task is not None:
            data["task"] = task

        super().__init__(
            id=id,
            type=NodeType.AGENT,
            config=NodeConfig(type=NodeType.AGENT, data=data),
            **kwargs,
        )


class ToolNode(Node):
    """Node that executes a tool."""

    def __init__(self, id: str, tool_name: str, **kwargs: Any) -> None:
        """Initialize tool node."""
        super().__init__(
            id=id,
            type=NodeType.TOOL,
            config=NodeConfig(type=NodeType.TOOL, data={"tool_name": tool_name}),
            **kwargs,
        )


class ConditionNode(Node):
    """Node that evaluates a condition."""

    def __init__(self, id: str, condition: str, **kwargs: Any) -> None:
        """Initialize condition node."""
        super().__init__(
            id=id,
            type=NodeType.CONDITION,
            config=NodeConfig(type=NodeType.CONDITION, data={"condition": condition}),
            **kwargs,
        )


class InputNode(Node):
    """Node that receives input."""

    def __init__(self, id: str = "input", **kwargs: Any) -> None:
        """Initialize input node."""
        super().__init__(
            id=id, type=NodeType.INPUT, config=NodeConfig(type=NodeType.INPUT), **kwargs
        )


class OutputNode(Node):
    """Node that produces output."""

    def __init__(self, id: str = "output", **kwargs: Any) -> None:
        """Initialize output node."""
        super().__init__(
            id=id, type=NodeType.OUTPUT, config=NodeConfig(type=NodeType.OUTPUT), **kwargs
        )


class SubgraphNode(Node):
    """Node that executes a nested workflow."""

    def __init__(self, id: str, workflow_id: str, **kwargs: Any) -> None:
        super().__init__(
            id=id,
            type=NodeType.SUBGRAPH,
            config=NodeConfig(type=NodeType.SUBGRAPH, data={"workflow_id": workflow_id}),
            **kwargs,
        )


class LoopNode(Node):
    """Node that represents a loop with a termination condition."""

    def __init__(self, id: str, condition: str, max_iterations: int = 5, **kwargs: Any) -> None:
        super().__init__(
            id=id,
            type=NodeType.LOOP,
            config=NodeConfig(
                type=NodeType.LOOP,
                data={"condition": condition, "max_iterations": max_iterations},
            ),
            **kwargs,
        )
