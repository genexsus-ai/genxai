from typing import Any, Dict

from genxai.core.agent.base import AgentFactory
from genxai.core.agent.registry import AgentRegistry
from genxai.core.graph.edges import Edge
from genxai.core.graph.executor import EnhancedGraph
from genxai.core.agent.runtime import AgentRuntime
from genxai.core.graph.nodes import NodeType, NodeStatus
from genxai.tools.registry import ToolRegistry


class StreamingEnhancedGraph(EnhancedGraph):
    async def _execute_node(
        self,
        node_id: str,
        state: Dict[str, Any],
        max_iterations: int,
        event_callback=None,
    ) -> None:
        node = self.nodes.get(node_id)
        if node and node_id == "coordinator_node" and node.status == NodeStatus.COMPLETED:
            if "review_node" in state and not state.get("_coordinator_reentry_done"):
                state["_coordinator_reentry_done"] = True
                node.status = NodeStatus.PENDING
                node.result = None
                node.error = None
        await super()._execute_node(node_id, state, max_iterations, event_callback)

    async def _execute_node_logic(self, node: Any, state: Dict[str, Any], max_iterations: int = 100) -> Any:
        if node.type == NodeType.AGENT:
            agent_id = node.config.data.get("agent_id")
            if not agent_id:
                raise ValueError(f"Agent node '{node.id}' missing agent_id in config.data")

            agent = AgentRegistry.get(agent_id)
            if agent is None:
                raise ValueError(f"Agent '{agent_id}' not found in registry")

            task = state.get("task", "Process the input data")

            runtime = AgentRuntime(
                agent=agent,
                llm_provider=getattr(self, "llm_provider", None),
                openai_api_key=getattr(self, "openai_api_key", None),
                anthropic_api_key=getattr(self, "anthropic_api_key", None),
                enable_memory=True,
                shared_memory=getattr(self, "shared_memory", None),
            )

            if agent.config.tools:
                tools = {}
                for tool_name in agent.config.tools:
                    tool = ToolRegistry.get(tool_name)
                    if tool:
                        tools[tool_name] = tool
                runtime.set_tools(tools)

            context = dict(state)
            if getattr(self, "shared_memory", None) is not None:
                context["shared_memory"] = getattr(self, "shared_memory")

            chunks: list[str] = []
            async for chunk in runtime.stream_execute(task, context=context):
                chunks.append(chunk)
                event_callback = getattr(self, "event_callback", None)
                if event_callback and callable(event_callback):
                    await event_callback({
                        "node_id": node.id,
                        "event": "token",
                        "status": "streaming",
                        "message": chunk,
                        "output": chunk,
                        "text_output": chunk,
                    })
            return "".join(chunks)

        return await super()._execute_node_logic(node, state, max_iterations)
from genxai.core.graph.nodes import AgentNode, InputNode, OutputNode

from app.tools.real_travel_tools import register_real_travel_tools


def build_travel_workflow() -> EnhancedGraph:
    register_real_travel_tools()

    coordinator = AgentFactory.create_agent(
        id="coordinator_agent",
        role="Travel Coordinator",
        goal=(
            "Oversee the travel planning workflow and ensure quality. "
            "At the final review step, evaluate the full plan plus summary and return strict JSON "
            "with keys: approved (boolean), reason (string), required_changes (array of strings, optional)."
        ),
        backstory=(
            "Former concierge director who has coordinated complex international itineraries "
            "for executive teams and expects polished, end-to-end travel experiences."
        ),
        llm_model="gpt-4o",
        temperature=0.2,
    )
    delegator = AgentFactory.create_agent(
        id="delegator_agent",
        role="Travel Delegator",
        goal="Break down travel tasks and assign to specialist agents",
        backstory=(
            "Seasoned operations lead who thrives on decomposing large travel requests into "
            "clear, parallel workstreams for specialists."
        ),
        llm_model="gpt-4o-mini",
        temperature=0.2,
    )
    intake = AgentFactory.create_agent(
        id="intake_agent",
        role="Travel Intake Specialist",
        goal="Normalize traveler preferences",
        backstory=(
            "Customer success veteran known for turning messy trip requests into crisp, "
            "actionable travel briefs that teams can execute on quickly."
        ),
        llm_model="gpt-4o-mini",
        temperature=0.2,
    )
    researcher = AgentFactory.create_agent(
        id="research_agent",
        role="Travel Researcher",
        goal="Gather transport, hotel, and activity options",
        backstory=(
            "Detail-driven travel scout with a global vendor network who validates flight, "
            "lodging, and activity options against real-time constraints."
        ),
        tools=["flight_status_search", "hotel_poi_search", "activity_poi_search"],
        llm_model="gpt-4o-mini",
        temperature=0.3,
    )
    budgeter = AgentFactory.create_agent(
        id="budget_agent",
        role="Budget Analyst",
        goal=(
            "Check costs against budget and summarize spend. "
            "Return JSON with keys: summary (string), breakdown (object of category to amount), "
            "notes (string)."
        ),
        backstory=(
            "Former travel finance analyst who keeps itineraries within policy while flagging "
            "high-impact tradeoffs and savings opportunities."
        ),
        llm_model="gpt-4o-mini",
        temperature=0.2,
    )
    itinerary = AgentFactory.create_agent(
        id="itinerary_agent",
        role="Itinerary Designer",
        goal=(
            "Create a day-by-day travel plan. Return JSON with a days array: "
            "[{day:number, theme:string, details:string}]."
        ),
        backstory=(
            "Boutique travel planner celebrated for weaving logistics and experiences into "
            "cohesive, story-driven day-by-day journeys."
        ),
        llm_model="gpt-4o-mini",
        temperature=0.4,
    )
    reviewer = AgentFactory.create_agent(
        id="reviewer_agent",
        role="Quality Reviewer",
        goal=(
            "Ensure plan meets safety, budget, and preference constraints. "
            "Return JSON with keys: summary (string), recommendations (array of strings), notes (string), "
            "highlights (array of strings), daily_recommendations (array of objects with day and activities)."
        ),
        backstory=(
            "Risk-aware QA specialist who audits travel plans for policy compliance, safety gaps, "
            "and missed traveler preferences."
        ),
        llm_model="gpt-4o",
        temperature=0.2,
    )
    for agent in [
        coordinator,
        delegator,
        intake,
        researcher,
        budgeter,
        itinerary,
        reviewer,
    ]:
        AgentRegistry.register(agent)

    graph = StreamingEnhancedGraph(name="travel_planning")
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="coordinator_node", agent_id="coordinator_agent"))
    graph.add_node(AgentNode(id="delegator_node", agent_id="delegator_agent"))
    graph.add_node(AgentNode(id="intake_node", agent_id="intake_agent"))
    graph.add_node(AgentNode(id="research_node", agent_id="research_agent"))
    graph.add_node(AgentNode(id="budget_node", agent_id="budget_agent"))
    graph.add_node(AgentNode(id="itinerary_node", agent_id="itinerary_agent"))
    graph.add_node(AgentNode(id="review_node", agent_id="reviewer_agent"))
    graph.add_node(OutputNode())

    graph.add_edge(Edge(source="input", target="coordinator_node"))
    graph.add_edge(
        Edge(
            source="coordinator_node",
            target="delegator_node",
            condition=lambda state: "review_node" not in state,
        )
    )

    graph.add_edge(
        Edge(source="delegator_node", target="intake_node", metadata={"parallel": True})
    )
    graph.add_edge(
        Edge(source="delegator_node", target="research_node", metadata={"parallel": True})
    )
    graph.add_edge(
        Edge(source="delegator_node", target="budget_node", metadata={"parallel": True})
    )
    graph.add_edge(
        Edge(source="delegator_node", target="itinerary_node", metadata={"parallel": True})
    )

    graph.add_edge(Edge(source="intake_node", target="review_node"))
    graph.add_edge(Edge(source="research_node", target="review_node"))
    graph.add_edge(Edge(source="budget_node", target="review_node"))
    graph.add_edge(Edge(source="itinerary_node", target="review_node"))
    graph.add_edge(Edge(source="review_node", target="coordinator_node"))
    graph.add_edge(
        Edge(
            source="coordinator_node",
            target="output",
            condition=lambda state: "review_node" in state,
        )
    )

    return graph


async def run_travel_workflow(input_data: Dict[str, Any], event_callback=None) -> Dict[str, Any]:
    graph = build_travel_workflow()
    graph.validate()
    if event_callback:
        graph.event_callback = event_callback
    result = await graph.run(input_data=input_data, event_callback=event_callback)
    return result


