"""Edge types and implementations for graph connections."""

from enum import Enum
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class Edge(BaseModel):
    """Edge connecting two nodes in the graph."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: str
    target: str
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0  # For ordering multiple edges from same source


    def __repr__(self) -> str:
        """String representation of the edge."""
        condition_str = "conditional" if self.condition else "unconditional"
        return f"Edge({self.source} -> {self.target}, {condition_str})"

    def __hash__(self) -> int:
        """Hash function for edge."""
        return hash((self.source, self.target))

    def evaluate_condition(self, state: Dict[str, Any]) -> bool:
        """Evaluate the edge condition with given state."""
        if self.condition is None:
            return True
        try:
            return self.condition(state)
        except Exception:
            return False


class EdgeType(str, Enum):
    """High-level edge type used by the public WorkflowEngine API.

    The core engine implements sequencing/parallelism via metadata flags.
    This enum is a compatibility layer for integration tests + user-facing APIs.
    """

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class WorkflowEdge(Edge):
    """Compatibility edge that accepts from_node/to_node/edge_type."""

    def __init__(
        self,
        from_node: str,
        to_node: str,
        edge_type: EdgeType = EdgeType.SEQUENTIAL,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        **kwargs: Any,
    ) -> None:
        metadata = dict(kwargs.pop("metadata", {}) or {})

        if edge_type == EdgeType.PARALLEL:
            metadata["parallel"] = True
        
        super().__init__(
            source=from_node,
            target=to_node,
            condition=condition,
            metadata=metadata,
            **kwargs,
        )



class ConditionalEdge(Edge):
    """Edge with a condition that must be satisfied."""

    def __init__(
        self,
        source: str,
        target: str,
        condition: Callable[[Dict[str, Any]], bool],
        **kwargs: Any,
    ) -> None:
        """Initialize conditional edge."""
        super().__init__(source=source, target=target, condition=condition, **kwargs)


class ParallelEdge(Edge):
    """Edge that allows parallel execution."""

    def __init__(self, source: str, target: str, **kwargs: Any) -> None:
        """Initialize parallel edge."""
        super().__init__(
            source=source,
            target=target,
            metadata={"parallel": True, **kwargs.get("metadata", {})},
            **{k: v for k, v in kwargs.items() if k != "metadata"},
        )


# Backwards compatible alias for integration tests
# They import: from genxai.core.graph.edges import Edge, EdgeType
# and instantiate Edge(from_node=..., to_node=..., edge_type=...)
_EdgePydantic = Edge


def Edge(*args: Any, **kwargs: Any):  # type: ignore
    """Factory for edges.

    - If called with `source`/`target` it behaves like the pydantic Edge model.
    - If called with `from_node`/`to_node` (and optional `edge_type`) it returns
      a WorkflowEdge.
    """

    if "from_node" in kwargs or "to_node" in kwargs:
        from_node = kwargs.pop("from_node")
        to_node = kwargs.pop("to_node")
        edge_type = kwargs.pop("edge_type", EdgeType.SEQUENTIAL)
        condition = kwargs.pop("condition", None)
        return WorkflowEdge(
            from_node=from_node,
            to_node=to_node,
            edge_type=edge_type,
            condition=condition,
            **kwargs,
        )

    return _EdgePydantic(*args, **kwargs)
