"""Graph execution engine for orchestrating agent workflows."""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict, deque
import logging
import time
import copy
from pathlib import Path

from genxai.core.graph.nodes import Node, NodeConfig, NodeStatus, NodeType
from genxai.core.agent.registry import AgentRegistry
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry
from genxai.core.graph.edges import Edge
from genxai.core.memory.shared import SharedMemoryBus
from genxai.core.graph.checkpoints import (
    WorkflowCheckpoint,
    WorkflowCheckpointManager,
    create_checkpoint,
)
from genxai.utils.enterprise_compat import (
    record_exception,
    record_workflow_execution,
    record_workflow_node_execution,
    span,
)

logger = logging.getLogger(__name__)


class GraphExecutionError(Exception):
    """Exception raised during graph execution."""

    pass


class Graph:
    """Main graph class for orchestrating agent workflows."""

    def __init__(self, name: str = "workflow") -> None:
        """Initialize the graph.

        Args:
            name: Name of the workflow graph
        """
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency_list: Dict[str, List[Edge]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self.shared_memory: Optional[SharedMemoryBus] = None

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: Node to add

        Raises:
            ValueError: If node with same ID already exists
        """
        if node.id in self.nodes:
            raise ValueError(f"Node with id '{node.id}' already exists")

        self.nodes[node.id] = node
        logger.debug(f"Added node: {node.id} (type: {node.type})")

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph.

        Args:
            edge: Edge to add

        Raises:
            ValueError: If source or target node doesn't exist
        """
        if edge.source not in self.nodes:
            raise ValueError(f"Source node '{edge.source}' not found")
        if edge.target not in self.nodes:
            raise ValueError(f"Target node '{edge.target}' not found")

        self.edges.append(edge)
        self._adjacency_list[edge.source].append(edge)
        self._reverse_adjacency[edge.target].append(edge.source)
        logger.debug(f"Added edge: {edge.source} -> {edge.target}")

    def set_shared_memory(self, shared_memory: Optional[SharedMemoryBus]) -> None:
        """Attach a shared memory bus to the graph for agent execution."""
        self.shared_memory = shared_memory

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID.

        Args:
            node_id: ID of the node

        Returns:
            Node if found, None otherwise
        """
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get all outgoing edges from a node.

        Args:
            node_id: ID of the node

        Returns:
            List of outgoing edges
        """
        return self._adjacency_list.get(node_id, [])

    def get_incoming_nodes(self, node_id: str) -> List[str]:
        """Get all nodes with edges pointing to this node.

        Args:
            node_id: ID of the node

        Returns:
            List of incoming node IDs
        """
        return self._reverse_adjacency.get(node_id, [])

    def validate(self) -> bool:
        """Validate the graph structure.

        Returns:
            True if graph is valid

        Raises:
            GraphExecutionError: If graph is invalid
        """
        # Check for at least one node
        if not self.nodes:
            raise GraphExecutionError("Graph must have at least one node")

        # Check for cycles (optional - we allow cycles)
        # Check for disconnected components
        visited = self._dfs_visit(next(iter(self.nodes.keys())))
        if len(visited) != len(self.nodes):
            logger.warning("Graph has disconnected components")

        # Check that all edges reference valid nodes
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise GraphExecutionError(
                    f"Edge references non-existent node: {edge.source} -> {edge.target}"
                )

        logger.info(f"Graph '{self.name}' validated successfully")
        return True

    def _dfs_visit(self, start_node: str) -> Set[str]:
        """Perform DFS traversal from start node.

        Args:
            start_node: Starting node ID

        Returns:
            Set of visited node IDs
        """
        visited: Set[str] = set()
        stack = [start_node]

        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue

            visited.add(node_id)

            # Add neighbors (both outgoing and incoming for undirected check)
            for edge in self.get_outgoing_edges(node_id):
                if edge.target not in visited:
                    stack.append(edge.target)

            for incoming in self.get_incoming_nodes(node_id):
                if incoming not in visited:
                    stack.append(incoming)

        return visited

    def topological_sort(self) -> List[str]:
        """Perform topological sort on the graph.

        Returns:
            List of node IDs in topological order

        Raises:
            GraphExecutionError: If graph has cycles
        """
        in_degree = {node_id: 0 for node_id in self.nodes}

        for edge in self.edges:
            in_degree[edge.target] += 1

        queue: deque[str] = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result: List[str] = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for edge in self.get_outgoing_edges(node_id):
                in_degree[edge.target] -= 1
                if in_degree[edge.target] == 0:
                    queue.append(edge.target)

        if len(result) != len(self.nodes):
            raise GraphExecutionError("Graph contains cycles - cannot perform topological sort")

        return result

    async def run(
        self,
        input_data: Any,
        max_iterations: int = 100,
        state: Optional[Dict[str, Any]] = None,
        resume_from: Optional[WorkflowCheckpoint] = None,
        llm_provider: Any = None,
        event_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the graph workflow.

        Args:
            input_data: Input data for the workflow
            max_iterations: Maximum number of iterations (for cycle detection)
            state: Initial state dictionary

        Returns:
            Final state after execution

        Raises:
            GraphExecutionError: If execution fails
        """
        if not self.nodes:
            raise GraphExecutionError("Cannot run empty graph")

        self.validate()

        start_time = time.time()
        status = "success"

        # Initialize state
        if resume_from:
            state = resume_from.state.copy()
            state["input"] = input_data
            state.setdefault("iterations", 0)
        else:
            if state is None:
                state = {}
            state["input"] = input_data
            state["iterations"] = 0
        state.setdefault("node_events", [])

        if resume_from:
            for node_id, status in resume_from.node_statuses.items():
                if node_id in self.nodes:
                    self.nodes[node_id].status = NodeStatus(status)

        # Find entry points (nodes with no incoming edges)
        entry_points = [
            node_id for node_id in self.nodes if not self.get_incoming_nodes(node_id)
        ]

        if not entry_points:
            # If no clear entry point, look for INPUT node
            entry_points = [
                node_id for node_id, node in self.nodes.items() if node.type == NodeType.INPUT
            ]

        if not entry_points:
            raise GraphExecutionError("No entry point found in graph")

        logger.info(f"Starting graph execution: {self.name}")
        logger.debug(f"Entry points: {entry_points}")

        if llm_provider is not None:
            state["llm_provider"] = llm_provider

        # Execute from entry points
        try:
            with span("genxai.workflow.execute", {"workflow_id": self.name}):
                for entry_point in entry_points:
                    await self._execute_node(entry_point, state, max_iterations, event_callback)
        except Exception as exc:
            status = "error"
            record_exception(exc)
            raise
        finally:
            duration = time.time() - start_time
            record_workflow_execution(
                workflow_id=self.name,
                duration=duration,
                status=status,
            )

        logger.info(f"Graph execution completed: {self.name}")
        state["node_events"] = state.get("node_events", [])
        return state

    def create_checkpoint(self, name: str, state: Dict[str, Any]) -> WorkflowCheckpoint:
        """Create a checkpoint from current workflow state."""
        node_statuses = {node_id: node.status for node_id, node in self.nodes.items()}
        return create_checkpoint(name=name, workflow=self.name, state=state, node_statuses=node_statuses)

    def save_checkpoint(self, name: str, state: Dict[str, Any], path: Path) -> Path:
        """Persist a checkpoint to disk."""
        manager = WorkflowCheckpointManager(path)
        checkpoint = self.create_checkpoint(name=name, state=state)
        return manager.save(checkpoint)

    def load_checkpoint(self, name: str, path: Path) -> WorkflowCheckpoint:
        """Load a checkpoint from disk."""
        manager = WorkflowCheckpointManager(path)
        return manager.load(name)

    async def _execute_node(
        self,
        node_id: str,
        state: Dict[str, Any],
        max_iterations: int,
        event_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> None:
        """Execute a single node and its descendants.

        Args:
            node_id: ID of the node to execute
            state: Current state
            max_iterations: Maximum iterations allowed

        Raises:
            GraphExecutionError: If execution fails or max iterations exceeded
        """
        if state.get("iterations", 0) >= max_iterations:
            raise GraphExecutionError(f"Maximum iterations ({max_iterations}) exceeded")

        state["iterations"] = state.get("iterations", 0) + 1

        node = self.nodes[node_id]

        # Skip if already completed
        if node.status == NodeStatus.COMPLETED:
            return

        # Mark as running
        node.status = NodeStatus.RUNNING
        logger.debug(f"Executing node: {node_id}")
        node_start = time.time()
        running_event = {
            "node_id": node_id,
            "status": NodeStatus.RUNNING.value,
            "timestamp": time.time(),
        }
        state.setdefault("node_events", []).append(running_event)
        if event_callback:
            callback_result = event_callback(running_event)
            if asyncio.iscoroutine(callback_result):
                await callback_result

        try:
            # Execute node (placeholder - will be implemented with actual executors)
            with span(
                "genxai.workflow.node",
                {"workflow_id": self.name, "node_id": node_id, "node_type": node.type.value},
            ):
                result = await self._execute_node_logic(node, state, max_iterations)
            node.result = result
            node.status = NodeStatus.COMPLETED
            logger.debug(f"Node completed: {node_id}")

            node_duration_ms = int((time.time() - node_start) * 1000)

            record_workflow_node_execution(
                workflow_id=self.name,
                node_id=node_id,
                status="success",
            )
            completed_event = {
                "node_id": node_id,
                "status": NodeStatus.COMPLETED.value,
                "timestamp": time.time(),
                "duration_ms": node_duration_ms,
            }
            state.setdefault("node_events", []).append(completed_event)
            if event_callback:
                callback_result = event_callback(completed_event)
                if asyncio.iscoroutine(callback_result):
                    await callback_result

            state.setdefault("node_results", {})[node_id] = {
                "output": result,
                "status": NodeStatus.COMPLETED.value,
                "duration_ms": node_duration_ms,
            }

            # Update state with result
            state[node_id] = result

            # Get outgoing edges and evaluate conditions
            outgoing_edges = self.get_outgoing_edges(node_id)

            # Separate parallel and sequential edges
            parallel_edges = [e for e in outgoing_edges if e.metadata.get("parallel", False)]
            sequential_edges = [e for e in outgoing_edges if not e.metadata.get("parallel", False)]

            # Execute parallel edges concurrently
            if parallel_edges:
                tasks = []
                for edge in parallel_edges:
                    if edge.evaluate_condition(state):
                        tasks.append(self._execute_node(edge.target, state, max_iterations, event_callback))
                if tasks:
                    await self._gather_with_config(tasks, state)

            # Execute sequential edges in order
            for edge in sorted(sequential_edges, key=lambda e: e.priority):
                if edge.evaluate_condition(state):
                    await self._execute_node(edge.target, state, max_iterations, event_callback)

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            logger.error(f"Node execution failed: {node_id} - {e}")
            node_duration_ms = int((time.time() - node_start) * 1000)
            record_workflow_node_execution(
                workflow_id=self.name,
                node_id=node_id,
                status="error",
            )
            failed_event = {
                "node_id": node_id,
                "status": NodeStatus.FAILED.value,
                "timestamp": time.time(),
                "error": str(e),
                "duration_ms": node_duration_ms,
            }
            state.setdefault("node_events", []).append(failed_event)
            if event_callback:
                callback_result = event_callback(failed_event)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            state.setdefault("node_results", {})[node_id] = {
                "output": None,
                "status": NodeStatus.FAILED.value,
                "duration_ms": node_duration_ms,
                "error": str(e),
            }
            raise GraphExecutionError(f"Node {node_id} failed: {e}") from e

    async def _execute_node_logic(
        self, node: Node, state: Dict[str, Any], max_iterations: int
    ) -> Any:
        """Execute the actual logic of a node.

        Args:
            node: Node to execute
            state: Current state

        Returns:
            Result of node execution
        """
        if node.type == NodeType.INPUT:
            return copy.deepcopy(state.get("input"))

        if node.type == NodeType.OUTPUT:
            return copy.deepcopy(state)

        if node.type == NodeType.AGENT:
            return await self._execute_agent_node(node, state)

        if node.type == NodeType.TOOL:
            return await self._execute_tool_node(node, state)

        if node.type == NodeType.SUBGRAPH:
            return await self._execute_subgraph_node(node, state, max_iterations)

        if node.type == NodeType.LOOP:
            return await self._execute_loop_node(node, state, max_iterations)

        # Default fallback for unsupported nodes
        return {"node_id": node.id, "type": node.type.value}

    async def _execute_agent_node(self, node: Node, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AgentNode using AgentRuntime.

        Args:
            node: Agent node to execute
            state: Current workflow state

        Returns:
            Agent execution result
        """
        agent_id = node.config.data.get("agent_id")
        if not agent_id:
            raise GraphExecutionError(
                f"Agent node '{node.id}' missing agent_id in config.data"
            )

        agent = AgentRegistry.get(agent_id)
        if agent is None:
            raise GraphExecutionError(f"Agent '{agent_id}' not found in registry")

        task = node.config.data.get("task") or state.get("task") or "Process input"

        llm_provider = state.get("llm_provider")
        runtime = AgentRuntime(
            agent=agent,
            llm_provider=llm_provider,
            enable_memory=True,
            shared_memory=self.shared_memory,
        )
        if agent.config.tools:
            tools: Dict[str, Any] = {}
            for tool_name in agent.config.tools:
                tool = ToolRegistry.get(tool_name)
                if tool:
                    tools[tool_name] = tool
            runtime.set_tools(tools)

        context = dict(state)
        if self.shared_memory is not None:
            context["shared_memory"] = self.shared_memory
        return await self._execute_with_config(runtime, task=task, context=context, state=state)

    def _get_execution_config(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config = state.get("execution_config") or {}
        return {
            "timeout_seconds": config.get("timeout_seconds", 120.0),
            "retry_count": config.get("retry_count", 3),
            "backoff_base": config.get("backoff_base", 1.0),
            "backoff_multiplier": config.get("backoff_multiplier", 2.0),
            "cancel_on_failure": config.get("cancel_on_failure", True),
        }

    async def _execute_with_config(
        self,
        runtime: AgentRuntime,
        task: str,
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Any:
        config = self._get_execution_config(state)
        delay = config["backoff_base"]
        for attempt in range(config["retry_count"] + 1):
            try:
                coro = runtime.execute(task=task, context=context)
                timeout = config["timeout_seconds"]
                if timeout:
                    return await asyncio.wait_for(coro, timeout=timeout)
                return await coro
            except asyncio.CancelledError:
                raise
            except Exception:
                if attempt >= config["retry_count"]:
                    raise
                await asyncio.sleep(delay)
                delay *= config["backoff_multiplier"]

    async def _gather_with_config(self, coros: List[Any], state: Dict[str, Any]) -> List[Any]:
        config = self._get_execution_config(state)
        tasks = [asyncio.create_task(coro) for coro in coros]
        if not tasks:
            return []
        if not config["cancel_on_failure"]:
            return await asyncio.gather(*tasks, return_exceptions=True)

        results: List[Any] = [None] * len(tasks)
        index_map = {task: idx for idx, task in enumerate(tasks)}
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

        for task in done:
            idx = index_map[task]
            exc = task.exception()
            if exc:
                for pending_task in pending:
                    pending_task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                raise exc
            results[idx] = task.result()

        if pending:
            pending_results = await asyncio.gather(*pending, return_exceptions=True)
            for task, result in zip(pending, pending_results):
                results[index_map[task]] = result

        return results

    async def _execute_tool_node(self, node: Node, state: Dict[str, Any]) -> Any:
        """Execute a ToolNode using ToolRegistry.

        Args:
            node: Tool node to execute
            state: Current workflow state

        Returns:
            Tool execution result
        """
        tool_name = node.config.data.get("tool_name")
        if not tool_name:
            raise GraphExecutionError(
                f"Tool node '{node.id}' missing tool_name in config.data"
            )

        tool = ToolRegistry.get(tool_name)
        if tool is None:
            raise GraphExecutionError(f"Tool '{tool_name}' not found in registry")

        tool_params = node.config.data.get("tool_params", {})
        if tool_params is None:
            tool_params = {}
        if not isinstance(tool_params, dict):
            raise GraphExecutionError(
                f"Tool node '{node.id}' tool_params must be a dict"
            )

        result = await tool.execute(**tool_params)
        return result.model_dump() if hasattr(result, "model_dump") else result

    async def _execute_subgraph_node(
        self, node: Node, state: Dict[str, Any], max_iterations: int
    ) -> Any:
        """Execute a nested workflow defined in the state metadata."""
        workflow_id = node.config.data.get("workflow_id")
        if not workflow_id:
            raise GraphExecutionError(
                f"Subgraph node '{node.id}' missing workflow_id in config.data"
            )

        subgraphs = state.get("subgraphs", {})
        workflow_def = subgraphs.get(workflow_id)
        if not workflow_def and "subgraphs" in state:
            workflow_def = state["subgraphs"].get(workflow_id)
        if not workflow_def and "metadata" in state:
            workflow_def = state.get("metadata", {}).get("subgraphs", {}).get(workflow_id)
        if not workflow_def:
            raise GraphExecutionError(
                f"Subgraph workflow '{workflow_id}' not found in state.subgraphs"
            )

        subgraph = Graph(name=f"subgraph:{workflow_id}")
        for node_def in workflow_def.get("nodes", []):
            node_type = node_def.get("type")
            node_id = node_def.get("id")
            if node_type == "input":
                subgraph.add_node(Node(id=node_id, type=NodeType.INPUT, config=NodeConfig(type=NodeType.INPUT)))
            elif node_type == "output":
                subgraph.add_node(Node(id=node_id, type=NodeType.OUTPUT, config=NodeConfig(type=NodeType.OUTPUT)))
            elif node_type == "agent":
                subgraph.add_node(Node(id=node_id, type=NodeType.AGENT, config=NodeConfig(type=NodeType.AGENT, data=node_def.get("config", {}))))
            elif node_type == "tool":
                subgraph.add_node(Node(id=node_id, type=NodeType.TOOL, config=NodeConfig(type=NodeType.TOOL, data=node_def.get("config", {}))))
            else:
                subgraph.add_node(Node(id=node_id, type=NodeType.CONDITION, config=NodeConfig(type=NodeType.CONDITION, data=node_def.get("config", {}))))

        for edge_def in workflow_def.get("edges", []):
            subgraph.add_edge(Edge(source=edge_def["source"], target=edge_def["target"], condition=edge_def.get("condition")))

        result_state = await subgraph.run(
            input_data=state.get("input"),
            max_iterations=max_iterations,
            state={"parent_state": state},
        )
        return {"workflow_id": workflow_id, "state": result_state}

    async def _execute_loop_node(
        self, node: Node, state: Dict[str, Any], max_iterations: int
    ) -> Any:
        """Execute a loop node by iterating until condition is met."""
        condition_key = node.config.data.get("condition")
        loop_limit = int(node.config.data.get("max_iterations", 5))
        loop_iterations = 0
        results = []

        while loop_iterations < loop_limit:
            loop_iterations += 1
            state_key = f"loop_{node.id}_iteration"
            state[state_key] = loop_iterations
            results.append({"iteration": loop_iterations})
            if condition_key and state.get(condition_key):
                break
            if state.get("iterations", 0) >= max_iterations:
                break

        return {"iterations": loop_iterations, "results": results}

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "name": self.name,
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type.value,
                    "config": node.config.model_dump(),
                    "status": node.status.value,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "metadata": edge.metadata,
                    "priority": edge.priority,
                }
                for edge in self.edges
            ],
        }

    def __repr__(self) -> str:
        """String representation of the graph."""
        return f"Graph(name={self.name}, nodes={len(self.nodes)}, edges={len(self.edges)})"

    def draw_ascii(self) -> str:
        """Generate ASCII art representation of the graph.

        Returns:
            String containing ASCII art visualization of the graph
        """
        if not self.nodes:
            return "Empty graph"

        lines = []
        lines.append(f"Graph: {self.name}")
        lines.append("=" * 60)
        lines.append("")

        # Find entry points
        entry_points = [
            node_id for node_id in self.nodes if not self.get_incoming_nodes(node_id)
        ]

        if not entry_points:
            entry_points = [
                node_id
                for node_id, node in self.nodes.items()
                if node.type == NodeType.INPUT
            ]

        if not entry_points and self.nodes:
            entry_points = [next(iter(self.nodes.keys()))]

        # Build tree structure
        visited = set()
        for entry in entry_points:
            self._draw_node_tree(entry, lines, visited, prefix="", is_last=True)

        lines.append("")
        lines.append("=" * 60)
        lines.append(f"Total Nodes: {len(self.nodes)} | Total Edges: {len(self.edges)}")

        return "\n".join(lines)

    def _draw_node_tree(
        self, node_id: str, lines: List[str], visited: Set[str], prefix: str, is_last: bool
    ) -> None:
        """Recursively draw node tree structure.

        Args:
            node_id: Current node ID
            lines: List to append output lines to
            visited: Set of visited node IDs
            prefix: Current line prefix for indentation
            is_last: Whether this is the last child
        """
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Draw current node
        connector = "└── " if is_last else "├── "
        status_symbol = {
            NodeStatus.PENDING: "○",
            NodeStatus.RUNNING: "◐",
            NodeStatus.COMPLETED: "●",
            NodeStatus.FAILED: "✗",
            NodeStatus.SKIPPED: "⊘",
        }.get(node.status, "?")

        node_line = f"{prefix}{connector}{status_symbol} {node.id} [{node.type.value}]"
        lines.append(node_line)

        # Avoid infinite loops in cyclic graphs
        if node_id in visited:
            extension = "    " if is_last else "│   "
            lines.append(f"{prefix}{extension}↻ (cycle detected)")
            return

        visited.add(node_id)

        # Get outgoing edges
        outgoing = self.get_outgoing_edges(node_id)
        if not outgoing:
            return

        # Group edges by type
        parallel_edges = [e for e in outgoing if e.metadata.get("parallel", False)]
        sequential_edges = [e for e in outgoing if not e.metadata.get("parallel", False)]

        # Draw parallel edges
        if parallel_edges:
            extension = "    " if is_last else "│   "
            lines.append(f"{prefix}{extension}║")
            lines.append(f"{prefix}{extension}╠══ [PARALLEL]")

            for i, edge in enumerate(parallel_edges):
                is_last_parallel = i == len(parallel_edges) - 1 and not sequential_edges
                new_prefix = prefix + ("    " if is_last else "│   ")
                condition_marker = " (conditional)" if edge.condition else ""
                lines.append(f"{new_prefix}║")
                self._draw_node_tree(
                    edge.target, lines, visited.copy(), new_prefix, is_last_parallel
                )

        # Draw sequential edges
        for i, edge in enumerate(sequential_edges):
            is_last_edge = i == len(sequential_edges) - 1
            new_prefix = prefix + ("    " if is_last else "│   ")
            condition_marker = " (?)" if edge.condition else ""

            if edge.condition:
                lines.append(f"{new_prefix}│")
                lines.append(f"{new_prefix}├── [IF condition]")

            self._draw_node_tree(edge.target, lines, visited.copy(), new_prefix, is_last_edge)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram syntax for the graph.

        Returns:
            String containing Mermaid flowchart syntax
        """
        if not self.nodes:
            return "graph TD\n    empty[Empty Graph]"

        lines = ["graph TD"]

        # Define nodes with appropriate shapes
        for node_id, node in self.nodes.items():
            label = f"{node_id}\\n[{node.type.value}]"

            # Choose shape based on node type
            if node.type == NodeType.INPUT:
                shape = f'    {node_id}(["{label}"])'
            elif node.type == NodeType.OUTPUT:
                shape = f'    {node_id}(["{label}"])'
            elif node.type == NodeType.CONDITION:
                shape = f'    {node_id}{{{{{label}}}}}'
            elif node.type == NodeType.AGENT:
                shape = f'    {node_id}["{label}"]'
            elif node.type == NodeType.TOOL:
                shape = f'    {node_id}["{label}"]'
            else:
                shape = f'    {node_id}["{label}"]'

            lines.append(shape)

        lines.append("")

        # Define edges
        for edge in self.edges:
            if edge.condition:
                lines.append(f"    {edge.source} -->|conditional| {edge.target}")
            elif edge.metadata.get("parallel", False):
                lines.append(f"    {edge.source} -.parallel.-> {edge.target}")
            else:
                lines.append(f"    {edge.source} --> {edge.target}")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Generate GraphViz DOT format for the graph.

        Returns:
            String containing DOT format graph definition
        """
        if not self.nodes:
            return "digraph empty { }"

        lines = [f'digraph "{self.name}" {{']
        lines.append("    rankdir=TB;")
        lines.append("    node [fontname=Arial, fontsize=10];")
        lines.append("    edge [fontname=Arial, fontsize=9];")
        lines.append("")

        # Define node styles by type
        node_styles = {
            NodeType.INPUT: 'shape=ellipse, style=filled, fillcolor=lightblue',
            NodeType.OUTPUT: 'shape=ellipse, style=filled, fillcolor=lightgreen',
            NodeType.CONDITION: 'shape=diamond, style=filled, fillcolor=lightyellow',
            NodeType.AGENT: 'shape=box, style="rounded,filled", fillcolor=lightcoral',
            NodeType.TOOL: 'shape=box, style=filled, fillcolor=lightgray',
            NodeType.HUMAN: 'shape=box, style=filled, fillcolor=lightpink',
            NodeType.SUBGRAPH: 'shape=box3d, style=filled, fillcolor=lavender',
        }

        # Define nodes
        for node_id, node in self.nodes.items():
            style = node_styles.get(node.type, 'shape=box')
            label = f"{node_id}\\n[{node.type.value}]"

            # Add status indicator
            if node.status != NodeStatus.PENDING:
                label += f"\\n({node.status.value})"

            lines.append(f'    {node_id} [label="{label}", {style}];')

        lines.append("")

        # Define edges
        for edge in self.edges:
            attrs = []

            if edge.condition:
                attrs.append('label="conditional"')
                attrs.append('style=dashed')

            if edge.metadata.get("parallel", False):
                attrs.append('label="parallel"')
                attrs.append('color=blue')

            if edge.priority != 0:
                attrs.append(f'weight={edge.priority}')

            attr_str = ", ".join(attrs) if attrs else ""
            if attr_str:
                lines.append(f"    {edge.source} -> {edge.target} [{attr_str}];")
            else:
                lines.append(f"    {edge.source} -> {edge.target};")

        lines.append("}")

        return "\n".join(lines)

    def print_structure(self) -> None:
        """Print a simple text summary of the graph structure."""
        print(f"\nGraph: {self.name}")
        print("=" * 60)
        print(f"Nodes: {len(self.nodes)}")
        print(f"Edges: {len(self.edges)}")
        print()

        if self.nodes:
            print("Node List:")
            print("-" * 60)
            for node_id, node in self.nodes.items():
                status = node.status.value
                print(f"  • {node_id:20} [{node.type.value:10}] ({status})")
            print()

        if self.edges:
            print("Edge List:")
            print("-" * 60)
            for edge in self.edges:
                condition = "conditional" if edge.condition else "unconditional"
                parallel = " [PARALLEL]" if edge.metadata.get("parallel", False) else ""
                print(f"  • {edge.source:15} → {edge.target:15} ({condition}){parallel}")
            print()

        # Find entry and exit points
        entry_points = [
            node_id for node_id in self.nodes if not self.get_incoming_nodes(node_id)
        ]
        exit_points = [
            node_id for node_id in self.nodes if not self.get_outgoing_edges(node_id)
        ]

        if entry_points:
            print(f"Entry Points: {', '.join(entry_points)}")
        if exit_points:
            print(f"Exit Points: {', '.join(exit_points)}")

        print("=" * 60)
        print()


class WorkflowEngine(Graph):
    """Public, user-facing workflow engine.

    This is a thin compatibility wrapper around :class:`~genxai.core.graph.engine.Graph`
    to match the API expected by integration tests and external users.
    """

    def __init__(self, name: str = "workflow") -> None:
        super().__init__(name=name)

    async def execute(self, start_node: str, llm_provider: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """Execute a workflow starting from a given node.

        Notes:
            - WorkflowEngine uses the core Graph execution pipeline, which now
              executes AgentNode + ToolNode via AgentRuntime/ToolRegistry.
            - Integration tests pass `llm_provider`, but Graph does not need it.
              It's accepted here for compatibility.
        """
        # Initialize state with start node as the only entry point.
        state: Dict[str, Any] = kwargs.pop("state", {}) if "state" in kwargs else {}
        input_data = kwargs.pop("input_data", None)
        if input_data is not None:
            state["input"] = input_data

        # Ensure max_iterations propagates.
        max_iterations = kwargs.pop("max_iterations", 100)

        if llm_provider is not None:
            state["llm_provider"] = llm_provider

        # Execute from specified start node.
        await self._execute_node(start_node, state, max_iterations)
        return {
            "status": "completed",
            "node_results": {k: v for k, v in state.items() if k not in {"iterations"}},
            "state": state,
        }
