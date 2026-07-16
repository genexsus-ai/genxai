"""Workflow execution engine for GenXAI."""

import asyncio
import copy
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from genxai.core.agent.base import Agent, AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.execution import ExecutionStore, WorkerQueueEngine
from genxai.core.graph.edges import ConditionalEdge, Edge
from genxai.core.graph.engine import Graph
from genxai.core.graph.interpolation import TemplateResolutionError, resolve_templates
from genxai.core.graph.nodes import (
    AgentNode,
    ConditionNode,
    FlowNode,
    InputNode,
    LoopNode,
    Node,
    NodeConfig,
    NodeType,
    OutputNode,
    SubgraphNode,
    ToolNode,
)
from genxai.core.memory.shared import SharedMemoryBus
from genxai.tools.builtin.computation.calculator import CalculatorTool
from genxai.tools.builtin.file.file_reader import FileReaderTool
from genxai.tools.registry import ToolRegistry
from genxai.utils.runtime_services import (
    AuditEvent,
    Permission,
    get_audit_log,
    get_current_user,
    get_policy_engine,
)

logger = logging.getLogger(__name__)


class EnhancedGraph(Graph):
    """Enhanced graph with agent execution support.
    
    This extends the base Graph class to provide real agent execution
    with tool integration. It's the recommended way to execute workflows
    in GenXAI.
    """

    async def _execute_node_logic(
        self, node: Any, state: dict[str, Any], max_iterations: int = 100
    ) -> Any:
        """Execute node logic with actual agent execution.

        Args:
            node: Node to execute
            state: Current state

        Returns:
            Result of node execution
        """
        if node.type == NodeType.INPUT:
            # IMPORTANT: Avoid returning the exact same `dict` object stored under
            # `state["input"]`. If we do, the engine will store that same object
            # under the input node id (e.g. "start"), creating shared references
            # which Python's `json.dumps` treats as circular.
            return copy.deepcopy(state.get("input"))

        elif node.type == NodeType.OUTPUT:
            # IMPORTANT: never return the live `state` dict. The engine stores the
            # node result back into `state[node_id]`, so returning `state` would
            # create a self-referential structure (circular reference) that can't
            # be JSON-serialized for persistence.
            # Also deep-copy to avoid shared references (json can't encode those),
            # and drop live service objects (providers) that aren't workflow data.
            from genxai.core.graph.engine import _SERVICE_STATE_KEYS

            return copy.deepcopy(
                {k: v for k, v in state.items() if k not in _SERVICE_STATE_KEYS}
            )

        elif node.type == NodeType.AGENT:
            # Get agent from registry
            agent_id = node.config.data.get("agent_id")
            if not agent_id:
                raise ValueError(f"Agent node '{node.id}' missing agent_id in config.data")

            agent = AgentRegistry.get(agent_id)
            if agent is None:
                raise ValueError(f"Agent '{agent_id}' not found in registry")

            # Node-level task takes priority; fall back to the run input's task.
            task = node.config.data.get("task") or state.get("task", "Process the input data")
            if isinstance(task, str):
                try:
                    task = resolve_templates(task, state)
                except TemplateResolutionError as exc:
                    raise ValueError(f"Agent node '{node.id}': {exc}") from exc

            # Execute agent with tools if available
            result = await self._execute_agent_with_tools(agent, task, state)

            return result

        else:
            return await super()._execute_node_logic(node, state, max_iterations)

    async def _execute_agent_with_tools(
        self, agent: Agent, task: str, state: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute agent with tool support using AgentRuntime.

        Args:
            agent: Agent to execute
            task: Task description
            state: Current state

        Returns:
            Execution result
        """
        logger.debug(f"Executing agent '{agent.id}' ({agent.config.role})")

        # Use AgentRuntime for full integration
        from genxai.core.agent.runtime import AgentRuntime

        # Pass both API keys to runtime so it can select the correct one based on model
        runtime = AgentRuntime(
            agent=agent,
            llm_provider=getattr(self, "llm_provider", None),
            openai_api_key=getattr(self, "openai_api_key", None),
            anthropic_api_key=getattr(self, "anthropic_api_key", None),
            enable_memory=True,
            shared_memory=getattr(self, "shared_memory", None),
        )

        # Load tools from registry
        if agent.config.tools:
            tools = {}
            for tool_name in agent.config.tools:
                tool = ToolRegistry.get(tool_name)
                if tool:
                    tools[tool_name] = tool
            runtime.set_tools(tools)
            logger.debug(f"Loaded {len(tools)} tools for agent")

        # Execute agent with full runtime support
        context = dict(state)
        if getattr(self, "shared_memory", None) is not None:
            context["shared_memory"] = self.shared_memory
        result = await runtime.execute(task, context=context)

        return result

    async def _execute_tool_for_task(
        self, tool: Any, tool_name: str, task: str, state: dict[str, Any]
    ) -> Any:
        """Execute a tool based on the task.

        Args:
            tool: Tool instance
            tool_name: Tool name
            task: Task description
            state: Current state

        Returns:
            Tool execution result or None
        """
        try:
            # Calculator tool
            if tool_name == "calculator":
                # Check if task involves calculation
                if any(op in task.lower() for op in ["calculate", "compute", "add", "multiply", "+"]):
                    # Extract expression from state or use default
                    expression = state.get("expression", "10 * 5 + 3")
                    logger.debug(f"Executing calculator: {expression}")
                    result = await tool.execute(expression=expression)
                    if result.success:
                        logger.debug(f"Calculator result: {result.data['result']}")
                        return result.data

            # File reader tool
            elif tool_name == "file_reader":
                # Check if task involves file reading
                if any(word in task.lower() for word in ["read", "file", "load"]):
                    # Get file path from state
                    file_path = state.get("file_path")

                    if file_path:
                        logger.debug(f"Reading file: {file_path}")
                        result = await tool.execute(path=file_path)
                        if result.success:
                            logger.debug(f"Read {result.data['lines']} lines")
                            return result.data

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")

        return None


class WorkflowExecutor:
    """Executes workflows using GenXAI engine.
    
    This is the main class for executing workflows programmatically.
    It handles agent creation, tool registration, graph building,
    and execution.
    
    Example:
        ```python
        executor = WorkflowExecutor(openai_api_key="sk-...")
        result = await executor.execute(nodes, edges, input_data)
        ```
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        register_builtin_tools: bool = True,
        queue_engine: WorkerQueueEngine | None = None,
        execution_store: ExecutionStore | None = None,
    ):
        """Initialize workflow executor.

        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            register_builtin_tools: Whether to register built-in tools
        """
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key

        self.queue_engine = queue_engine
        self.execution_store = execution_store or ExecutionStore()

        if register_builtin_tools:
            self._setup_tools()

    def _setup_tools(self) -> None:
        """Register built-in tools."""
        # Register calculator tool
        if not ToolRegistry.get("calculator"):
            calculator = CalculatorTool()
            ToolRegistry.register(calculator)
            logger.info("Registered calculator tool")

        # Register file reader tool
        if not ToolRegistry.get("file_reader"):
            file_reader = FileReaderTool()
            ToolRegistry.register(file_reader)
            logger.info("Registered file_reader tool")

    def _create_agents_from_nodes(self, nodes: list[dict[str, Any]]) -> None:
        """Create and register agents from workflow nodes.

        Args:
            nodes: List of workflow nodes
        """
        for node in nodes:
            if node.get("type") == "agent":
                agent_id = node.get("id")
                config = node.get("config", {})

                # Extract agent configuration
                role = config.get("role", "Agent")
                goal = config.get("goal", "Process tasks")
                backstory = config.get("backstory", "")
                tools = config.get("tools", [])
                llm_model = config.get("llm_model", "gpt-4")
                temperature = config.get("temperature", 0.7)

                memory = config.get("memory") or {}

                # Create agent
                agent = AgentFactory.create_agent(
                    id=agent_id,
                    role=role,
                    goal=goal,
                    backstory=backstory,
                    tools=tools,
                    llm_model=llm_model,
                    llm_temperature=temperature,
                    enable_memory=config.get("enable_memory", True),
                    memory_persistence_path=memory.get("persistence_path"),
                    memory_id=memory.get("memory_id"),
                )

                # Register agent
                AgentRegistry.register(agent)
                logger.info(f"Created and registered agent: {agent_id}")

    def _build_graph(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> EnhancedGraph:
        """Build GenXAI graph from workflow definition.

        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges

        Returns:
            Constructed graph
        """
        graph = EnhancedGraph(name="workflow")
        graph.openai_api_key = self.openai_api_key
        graph.anthropic_api_key = self.anthropic_api_key

        # Add nodes
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            config = node.get("config", {})

            # Support some common aliases used by the Studio UI
            # - "start" behaves like an input node
            # - "end" behaves like an output node
            if node_type in {"input", "start"}:
                graph.add_node(InputNode(id=node_id))
            elif node_type in {"output", "end"}:
                graph.add_node(OutputNode(id=node_id))
            elif node_type == "agent":
                graph.add_node(AgentNode(id=node_id, agent_id=node_id, task=config.get("task")))
            elif node_type == "tool":
                tool_name = config.get("tool_name") or config.get("name") or "tool"
                tool_params = config.get("tool_params") or {}
                graph.add_node(ToolNode(id=node_id, tool_name=tool_name, tool_params=tool_params))
            elif node_type in {"decision", "condition"}:
                # "condition" is the YAML DSL name (workflow_io); "decision" is
                # the Studio UI name. Both build the same node.
                condition = config.get("condition", "")
                graph.add_node(ConditionNode(id=node_id, condition=condition))
            elif node_type == "subgraph":
                workflow_id = config.get("workflow_id") or config.get("subgraph_id") or config.get("workflow")
                if workflow_id:
                    graph.add_node(SubgraphNode(id=node_id, workflow_id=workflow_id))
                else:
                    graph.add_node(
                        Node(
                            id=node_id,
                            type=NodeType.SUBGRAPH,
                            config=NodeConfig(type=NodeType.SUBGRAPH, data={"workflow_id": ""}),
                        )
                    )
                    logger.warning(f"Subgraph node '{node_id}' missing workflow_id")
            elif node_type == "human":
                graph.add_node(
                    Node(
                        id=node_id,
                        type=NodeType.HUMAN,
                        config=NodeConfig(
                            type=NodeType.HUMAN,
                            data={
                                key: config[key]
                                for key in (
                                    "prompt",
                                    "timeout_seconds",
                                    "default_response",
                                )
                                if config.get(key) not in (None, "")
                            },
                        ),
                    )
                )
            elif node_type == "loop":
                condition = config.get("condition", "")
                max_iterations = int(config.get("max_iterations", 5))
                body = config.get("body")
                graph.add_node(
                    LoopNode(id=node_id, condition=condition, max_iterations=max_iterations, body=body)
                )
            elif node_type == "flow":
                flow_node = FlowNode(
                    id=node_id,
                    flow_type=config.get("flow_type", ""),
                    agents=config.get("agents") or [],
                    params=config.get("params") or {},
                    task=config.get("task"),
                )
                # Pattern-specific state seeds (critic_task, bid_task, ...) and
                # an optional input template pass through to the executor.
                if config.get("state"):
                    flow_node.config.data["state"] = config["state"]
                if "input" in config:
                    flow_node.config.data["input"] = config["input"]
                graph.add_node(flow_node)
            else:
                logger.warning(f"Unknown node type: {node_type}")
                continue

            # Attach the per-node execution policy (retry/timeout/continue_on_error)
            execution_policy = config.get("execution")
            if execution_policy and node_id in graph.nodes:
                graph.nodes[node_id].config.data["execution"] = execution_policy
            # Per-item execution: run the node once per element of this list
            if config.get("for_each") and node_id in graph.nodes:
                graph.nodes[node_id].config.data["for_each"] = config["for_each"]

        # Add edges
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            condition = edge.get("condition")
            parallel = edge.get("parallel", False)

            if condition:
                # Conditional edge
                edge_obj = ConditionalEdge(
                    source=source,
                    target=target,
                    condition=lambda state, cond=condition: self._evaluate_condition(state, cond),
                )
            else:
                # Regular edge
                edge_obj = Edge(source=source, target=target)

            if parallel:
                edge_obj.metadata["parallel"] = True

            graph.add_edge(edge_obj)

        return graph

    def _evaluate_condition(self, state: dict[str, Any], condition: str) -> bool:
        """Evaluate an edge/decision condition string.

        Supported forms, tried in order:
          - ``not <expr>`` — negation of any supported form
          - ``<left> contains <right>`` — substring test on stringified left
          - ``<left> == <right>`` / ``<left> != <right>`` — loose equality
          - bare key present in state — legacy behavior (always True)
          - ``<dotted.path>`` — truthiness of the resolved value

        Operand tokens are quoted strings or numbers (literals), or dotted
        paths resolved through the state and its ``node_results`` (so
        ``qualify.output`` reaches that node's output). Conditions that
        cannot be evaluated are False.
        """
        cond = (condition or "").strip()
        if not cond:
            return True
        try:
            if cond.startswith("not "):
                return not self._evaluate_condition(state, cond[4:])
            for op in (" contains ", " == ", " != "):
                if op in cond:
                    left_raw, right_raw = cond.split(op, 1)
                    left = self._resolve_condition_token(state, left_raw.strip())
                    right = self._resolve_condition_token(state, right_raw.strip())
                    if op == " contains ":
                        return right is not None and str(right) in str(left)
                    equal = left == right or str(left) == str(right)
                    return equal if op == " == " else not equal
            if cond in state:
                # Legacy semantics: a bare key that exists in state passes.
                return True
            return bool(self._resolve_condition_token(state, cond))
        except Exception as e:
            logger.error(f"Error evaluating condition {condition!r}: {e}")
            return False

    @staticmethod
    def _resolve_condition_token(state: dict[str, Any], token: str) -> Any:
        """Resolve a condition operand: literal string/number or state path."""
        if len(token) >= 2 and token[0] == token[-1] and token[0] in ("'", '"'):
            return token[1:-1]
        try:
            return float(token) if "." in token else int(token)
        except ValueError:
            pass
        for root in (state, state.get("node_results") or {}):
            value: Any = root
            for part in token.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            if value is not None:
                return value
        return None

    async def execute(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        input_data: dict[str, Any],
        run_id: str | None = None,
        checkpoint_dir: str | None = None,
        resume_from: str | None = None,
        model_override: str | None = None,
        event_callback: Callable[[dict[str, Any]], Any] | None = None,
        shared_memory: bool = False,
        llm_provider: Any | None = None,
        subgraphs: dict[str, dict[str, Any]] | None = None,
        human_input_provider: Any | None = None,
        extra_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a workflow.

        Args:
            nodes: Workflow nodes
            edges: Workflow edges
            input_data: Input data for execution
            subgraphs: Nested workflow definitions ({workflow_id: {nodes, edges}})
                referenced by subgraph nodes
            human_input_provider: Async ``(node_id, prompt) -> Any`` that human
                nodes await for a person's response
            extra_state: Additional entries seeded into workflow state before
                execution (e.g. prior node results for single-node test runs)

        Returns:
            Execution result with status, result, and metadata
        """
        run_id = run_id or self.execution_store.generate_run_id()
        self.execution_store.create(run_id, workflow="workflow", status="running")

        try:
            logger.info("Starting workflow execution")

            # Apply model override if provided
            if model_override:
                for node in nodes:
                    if node.get("type") == "agent":
                        config = node.setdefault("config", {})
                        config["llm_model"] = model_override

            # Create agents from nodes
            self._create_agents_from_nodes(nodes)

            # Build graph
            graph = self._build_graph(nodes, edges)
            graph.llm_provider = llm_provider
            if shared_memory:
                graph.set_shared_memory(SharedMemoryBus())
                graph.shared_memory = graph.shared_memory
                graph.shared_memory_enabled = True

            # Validate graph
            graph.validate()
            logger.info(f"Graph validated: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

            checkpoint = None
            if resume_from and checkpoint_dir:
                checkpoint = graph.load_checkpoint(resume_from, Path(checkpoint_dir))

            # Execute graph
            user = get_current_user()
            if user is not None:
                get_policy_engine().check(user, "workflow:workflow", Permission.WORKFLOW_EXECUTE)
                get_audit_log().record(
                    AuditEvent(
                        action="workflow.execute",
                        actor_id=user.user_id,
                        resource_id="workflow:workflow",
                        status="allowed",
                    )
                )
            seed_state: dict[str, Any] = {}
            if subgraphs:
                seed_state["subgraphs"] = dict(subgraphs)
            if human_input_provider is not None:
                seed_state["human_input_provider"] = human_input_provider
            if extra_state:
                seed_state.update(extra_state)
            result = await graph.run(
                input_data=input_data,
                state=seed_state or None,
                resume_from=checkpoint,
                event_callback=event_callback,
            )

            logger.info("Workflow execution completed successfully")

            self.execution_store.update(
                run_id,
                status="success",
                result=result,
                completed=True,
            )
            return {
                "status": "success",
                "run_id": run_id,
                "result": result,
                "node_events": result.get("node_events", []),
                "nodes_executed": len(graph.nodes),
                "message": "Workflow executed successfully"
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            self.execution_store.update(
                run_id,
                status="error",
                error=str(e),
                completed=True,
            )
            # Preserve partial progress (completed nodes' results) so callers
            # can display it and retry-from-failure can replay it.
            partial_state = getattr(e, "workflow_state", None) or {}
            return {
                "status": "error",
                "run_id": run_id,
                "error": str(e),
                "result": {
                    "node_results": partial_state.get("node_results", {}),
                    "node_events": partial_state.get("node_events", []),
                },
                "message": f"Workflow execution failed: {str(e)}"
            }

        finally:
            # Cleanup: Clear registries for next execution
            AgentRegistry.clear()
            logger.info("Cleared agent registry")

    async def execute_queued(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        input_data: dict[str, Any],
        run_id: str | None = None,
        checkpoint_dir: str | None = None,
        resume_from: str | None = None,
        model_override: str | None = None,
    ) -> str:
        """Enqueue workflow execution using a worker queue engine."""
        if not self.queue_engine:
            self.queue_engine = WorkerQueueEngine()

        run_id = run_id or self.execution_store.generate_run_id()
        existing = self.execution_store.get(run_id)
        if existing and existing.status in {"running", "success"}:
            return run_id

        self.execution_store.create(run_id, workflow="workflow", status="queued")

        async def _handler(payload: dict[str, Any]) -> None:
            await self.execute(
                nodes=payload["nodes"],
                edges=payload["edges"],
                input_data=payload["input_data"],
                run_id=payload["run_id"],
                checkpoint_dir=payload.get("checkpoint_dir"),
                resume_from=payload.get("resume_from"),
                model_override=payload.get("model_override"),
            )

        await self.queue_engine.start()
        return await self.queue_engine.enqueue(
            {
                "nodes": nodes,
                "edges": edges,
                "input_data": input_data,
                "run_id": run_id,
                "checkpoint_dir": checkpoint_dir,
                "resume_from": resume_from,
                "model_override": model_override,
            },
            _handler,
            metadata={"workflow": "queued"},
            run_id=run_id,
        )


def execute_workflow_sync(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    input_data: dict[str, Any],
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    model_override: str | None = None,
    shared_memory: bool = False,
) -> dict[str, Any]:
    """Synchronous wrapper for workflow execution.
    
    This is a convenience function for executing workflows in
    synchronous contexts.

    Args:
        nodes: Workflow nodes
        edges: Workflow edges
        input_data: Input data
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key

    Returns:
        Execution result
    """
    executor = WorkflowExecutor(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key
    )

    # Run async execution in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            executor.execute(
                nodes,
                edges,
                input_data,
                model_override=model_override,
                shared_memory=shared_memory,
            )
        )
        return result
    finally:
        loop.close()


async def execute_workflow_async(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    input_data: dict[str, Any],
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    model_override: str | None = None,
    event_callback: Callable[[dict[str, Any]], Any] | None = None,
    shared_memory: bool = False,
    subgraphs: dict[str, dict[str, Any]] | None = None,
    human_input_provider: Any | None = None,
    extra_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Async convenience function for workflow execution.

    This is the correct entry point when you're *already* inside an asyncio
    event loop (e.g. FastAPI/Uvicorn request handlers).

    Args:
        nodes: Workflow nodes
        edges: Workflow edges
        input_data: Input data
        openai_api_key: OpenAI API key
        anthropic_api_key: Anthropic API key

    Returns:
        Execution result
    """
    executor = WorkflowExecutor(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
    )
    return await executor.execute(
        nodes,
        edges,
        input_data,
        model_override=model_override,
        event_callback=event_callback,
        shared_memory=shared_memory,
        subgraphs=subgraphs,
        human_input_provider=human_input_provider,
        extra_state=extra_state,
    )

