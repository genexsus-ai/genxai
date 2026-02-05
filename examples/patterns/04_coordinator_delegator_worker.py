"""
Coordinator-Delegator-Worker (CDW) Pattern

This pattern demonstrates the CDW architecture where:
- COORDINATOR: Oversees the entire process and ensures quality
- DELEGATOR: Breaks down tasks and assigns to appropriate workers
- WORKERS: Specialized agents that execute specific tasks
- AGGREGATOR: Combines worker results into final output

Use Cases:
- Complex project management
- Distributed task processing
- Multi-specialist collaboration
- Large-scale data processing
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory


async def main():
    """Run Coordinator-Delegator-Worker pattern example."""
    print("=" * 70)
    print("COORDINATOR-DELEGATOR-WORKER (CDW) PATTERN")
    print("=" * 70)
    print()

    # Create agents for CDW pattern
    print("Creating CDW agents...")
    print()
    
    # COORDINATOR - Oversees entire process
    print("1. COORDINATOR LAYER")
    coordinator = AgentFactory.create_agent(
        id="coordinator",
        role="Project Coordinator",
        goal="Oversee entire workflow and ensure quality standards",
        backstory="Experienced project manager with holistic view of operations",
        llm_model="gpt-4",
        temperature=0.3,
        memory="episodic"  # Learns from past projects
    )
    print(f"   ✓ Created: {coordinator.config.role}")
    print()
    
    # DELEGATOR - Task breakdown and assignment
    print("2. DELEGATOR LAYER")
    delegator = AgentFactory.create_agent(
        id="delegator",
        role="Task Delegator",
        goal="Break down complex tasks and assign to appropriate workers",
        backstory="Expert at task decomposition and resource allocation",
        tools=["task_analyzer", "workload_balancer", "priority_calculator"],
        llm_model="gpt-4",
        temperature=0.2,
        memory="procedural"  # Remembers delegation strategies
    )
    print(f"   ✓ Created: {delegator.config.role}")
    print()
    
    # WORKERS - Specialized execution agents
    print("3. WORKER LAYER")
    
    worker_research = AgentFactory.create_agent(
        id="worker_research",
        role="Research Specialist",
        goal="Conduct thorough research and gather information",
        backstory="PhD researcher with expertise in information gathering",
        tools=["web_search", "document_reader", "data_extractor"],
        llm_model="gpt-4",
        temperature=0.4,
    )
    print(f"   ✓ Created: {worker_research.config.role}")
    
    worker_analysis = AgentFactory.create_agent(
        id="worker_analysis",
        role="Data Analysis Specialist",
        goal="Analyze data and extract meaningful insights",
        backstory="Data scientist with strong analytical skills",
        tools=["calculator", "statistical_analyzer", "visualizer"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    print(f"   ✓ Created: {worker_analysis.config.role}")
    
    worker_writing = AgentFactory.create_agent(
        id="worker_writing",
        role="Content Writing Specialist",
        goal="Create high-quality written content",
        backstory="Professional writer with excellent communication skills",
        tools=["grammar_checker", "style_guide", "formatter"],
        llm_model="gpt-4",
        temperature=0.6,
    )
    print(f"   ✓ Created: {worker_writing.config.role}")
    
    worker_review = AgentFactory.create_agent(
        id="worker_review",
        role="Quality Review Specialist",
        goal="Review and validate all outputs for quality",
        backstory="Quality assurance expert with attention to detail",
        tools=["validator", "fact_checker", "compliance_checker"],
        llm_model="gpt-4",
        temperature=0.2,
    )
    print(f"   ✓ Created: {worker_review.config.role}")
    print()
    
    # AGGREGATOR - Combines results
    print("4. AGGREGATOR LAYER")
    aggregator = AgentFactory.create_agent(
        id="aggregator",
        role="Results Aggregator",
        goal="Synthesize all worker outputs into cohesive final product",
        backstory="Expert at combining diverse inputs into unified deliverable",
        tools=["merger", "synthesizer", "formatter"],
        llm_model="gpt-4",
        temperature=0.4,
    )
    print(f"   ✓ Created: {aggregator.config.role}")
    print()
    
    print(f"Total agents created: 7")
    print()

    # Build CDW graph
    print("Building CDW workflow graph...")
    graph = Graph(name="cdw_pattern_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="coordinator_node", agent_id="coordinator"))
    graph.add_node(AgentNode(id="delegator_node", agent_id="delegator"))
    graph.add_node(AgentNode(id="worker_research_node", agent_id="worker_research"))
    graph.add_node(AgentNode(id="worker_analysis_node", agent_id="worker_analysis"))
    graph.add_node(AgentNode(id="worker_writing_node", agent_id="worker_writing"))
    graph.add_node(AgentNode(id="worker_review_node", agent_id="worker_review"))
    graph.add_node(AgentNode(id="aggregator_node", agent_id="aggregator"))
    graph.add_node(OutputNode())
    
    # Add edges - CDW flow
    graph.add_edge(Edge(source="input", target="coordinator_node"))
    graph.add_edge(Edge(source="coordinator_node", target="delegator_node"))
    
    # Delegator to Workers (PARALLEL)
    graph.add_edge(Edge(
        source="delegator_node",
        target="worker_research_node",
        metadata={"parallel": True, "task": "research"}
    ))
    graph.add_edge(Edge(
        source="delegator_node",
        target="worker_analysis_node",
        metadata={"parallel": True, "task": "analysis"}
    ))
    graph.add_edge(Edge(
        source="delegator_node",
        target="worker_writing_node",
        metadata={"parallel": True, "task": "writing"}
    ))
    
    # Workers to Review Worker (Sequential validation)
    graph.add_edge(Edge(source="worker_research_node", target="worker_review_node"))
    graph.add_edge(Edge(source="worker_analysis_node", target="worker_review_node"))
    graph.add_edge(Edge(source="worker_writing_node", target="worker_review_node"))
    
    # Review to Aggregator
    graph.add_edge(Edge(source="worker_review_node", target="aggregator_node"))
    
    # Aggregator to Output
    graph.add_edge(Edge(source="aggregator_node", target="output"))
    
    print(f"✓ Graph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print()

    # Validate graph
    print("Validating graph structure...")
    try:
        graph.validate()
        print("✓ Graph validation passed")
    except Exception as e:
        print(f"✗ Graph validation failed: {e}")
        return
    print()

    # Visualize workflow
    print("CDW Workflow Structure:")
    print("=" * 70)
    print()
    print("                    ┌─────────────────┐")
    print("                    │  COORDINATOR    │")
    print("                    │ (Project Mgmt)  │")
    print("                    └────────┬────────┘")
    print("                             │")
    print("                    ┌────────┴────────┐")
    print("                    │   DELEGATOR     │")
    print("                    │ (Task Splitter) │")
    print("                    └────────┬────────┘")
    print("                             │")
    print("            ┌────────────────┼────────────────┐")
    print("            ↓                ↓                ↓")
    print("      ┌──────────┐     ┌──────────┐    ┌──────────┐")
    print("      │ WORKER 1 │     │ WORKER 2 │    │ WORKER 3 │")
    print("      │Research  │     │ Analysis │    │ Writing  │")
    print("      └────┬─────┘     └────┬─────┘    └────┬─────┘")
    print("           │                │               │")
    print("           └────────────────┼───────────────┘")
    print("                            ↓")
    print("                      ┌──────────┐")
    print("                      │ WORKER 4 │")
    print("                      │  Review  │")
    print("                      └────┬─────┘")
    print("                           │")
    print("                      ┌────┴─────┐")
    print("                      │AGGREGATOR│")
    print("                      └────┬─────┘")
    print("                           │")
    print("                      ┌────┴─────┐")
    print("                      │  OUTPUT  │")
    print("                      └──────────┘")
    print()
    print("=" * 70)
    print()

    # Execute workflow
    print("Executing CDW workflow...")
    print("=" * 70)
    print()
    
    input_data = {
        "project": "Market Analysis Report",
        "topic": "AI in Healthcare Industry",
        "deadline": "5 days",
        "requirements": [
            "Current market size and trends",
            "Key players and competitive landscape",
            "Growth projections for next 5 years",
            "Regulatory considerations"
        ]
    }
    
    print(f"Project: {input_data['project']}")
    print(f"Topic: {input_data['topic']}")
    print(f"Deadline: {input_data['deadline']}")
    print(f"Requirements: {len(input_data['requirements'])} items")
    print()
    print("-" * 70)
    print()

    # Simulate CDW execution
    print("PHASE 1: COORDINATION")
    print("-" * 70)
    print("[Coordinator] Analyzing project requirements...")
    print("  → Project scope: Market analysis report")
    print("  → Complexity: Medium-High")
    print("  → Estimated effort: 40 hours")
    print("  → Quality standards: Executive-level presentation")
    print("  → Passing to Delegator...")
    print()
    
    await asyncio.sleep(0.3)
    
    print("PHASE 2: DELEGATION")
    print("-" * 70)
    print("[Delegator] Breaking down project into tasks...")
    print()
    print("Task Assignments:")
    print("  1. Research Specialist:")
    print("     • Gather market data and statistics")
    print("     • Identify key industry players")
    print("     • Research regulatory landscape")
    print("     Estimated: 15 hours")
    print()
    print("  2. Analysis Specialist:")
    print("     • Analyze market trends")
    print("     • Calculate growth projections")
    print("     • Perform competitive analysis")
    print("     Estimated: 12 hours")
    print()
    print("  3. Writing Specialist:")
    print("     • Draft executive summary")
    print("     • Create detailed report sections")
    print("     • Design visualizations")
    print("     Estimated: 10 hours")
    print()
    print("[Delegator] Launching parallel worker execution...")
    print()
    
    await asyncio.sleep(0.3)
    
    print("PHASE 3: WORKER EXECUTION (PARALLEL)")
    print("-" * 70)
    
    # Simulate parallel worker execution
    workers_status = [
        "[Research Specialist] Starting research...",
        "[Analysis Specialist] Starting analysis...",
        "[Writing Specialist] Starting writing..."
    ]
    
    for status in workers_status:
        print(status)
    
    print()
    await asyncio.sleep(0.5)
    
    # Worker results
    print("[Research Specialist] ✓ Research complete")
    print("  → Collected data from 15 sources")
    print("  → Identified 8 major players")
    print("  → Documented 12 regulatory requirements")
    print()
    
    print("[Analysis Specialist] ✓ Analysis complete")
    print("  → Market size: $28.5B (2025)")
    print("  → CAGR: 38.4% (2025-2030)")
    print("  → Top 3 segments identified")
    print()
    
    print("[Writing Specialist] ✓ Writing complete")
    print("  → Executive summary: 2 pages")
    print("  → Detailed report: 25 pages")
    print("  → Created 8 visualizations")
    print()
    
    await asyncio.sleep(0.3)
    
    print("PHASE 4: QUALITY REVIEW")
    print("-" * 70)
    print("[Review Specialist] Validating all outputs...")
    print()
    print("Quality Checks:")
    print("  ✓ Data accuracy verified")
    print("  ✓ Citations properly formatted")
    print("  ✓ Calculations validated")
    print("  ✓ Grammar and style checked")
    print("  ✓ Compliance requirements met")
    print()
    print("[Review Specialist] ✓ All quality checks passed")
    print()
    
    await asyncio.sleep(0.3)
    
    print("PHASE 5: AGGREGATION")
    print("-" * 70)
    print("[Aggregator] Synthesizing all outputs...")
    print()
    print("Combining:")
    print("  • Research findings → Background section")
    print("  • Analysis results → Market insights section")
    print("  • Written content → Executive summary")
    print("  • Review feedback → Final polish")
    print()
    print("[Aggregator] ✓ Final report generated")
    print()
    
    print("=" * 70)
    print("FINAL OUTPUT")
    print("=" * 70)
    print()
    print("Market Analysis Report: AI in Healthcare Industry")
    print("-" * 70)
    print()
    print("Executive Summary:")
    print("  The AI in Healthcare market is experiencing explosive growth,")
    print("  valued at $28.5B in 2025 with a projected CAGR of 38.4%.")
    print("  Key drivers include diagnostic accuracy improvements, cost")
    print("  reduction, and personalized medicine advancements.")
    print()
    print("Key Findings:")
    print("  • Market Size: $28.5B (2025) → $150B (2030)")
    print("  • Top Players: IBM Watson, Google Health, Microsoft Healthcare")
    print("  • Growth Drivers: Diagnostic AI, Drug Discovery, Patient Care")
    print("  • Challenges: Data privacy, regulatory compliance, integration")
    print()
    print("Recommendations:")
    print("  1. Focus on diagnostic AI segment (highest growth)")
    print("  2. Ensure HIPAA compliance from day one")
    print("  3. Partner with established healthcare providers")
    print("  4. Invest in explainable AI for regulatory approval")
    print()
    print("Report Statistics:")
    print("  • Pages: 27")
    print("  • Data Sources: 15")
    print("  • Visualizations: 8")
    print("  • Quality Score: 95/100")
    print()
    print("=" * 70)
    print()

    # Pattern characteristics
    print("=" * 70)
    print("CDW PATTERN CHARACTERISTICS")
    print("=" * 70)
    print()
    print("Advantages:")
    print("  ✓ Clear separation of responsibilities")
    print("  ✓ Scalable (add more workers as needed)")
    print("  ✓ Specialized expertise for each task")
    print("  ✓ Parallel execution for efficiency")
    print("  ✓ Quality oversight at multiple levels")
    print("  ✓ Fault tolerance (worker failures isolated)")
    print("  ✓ Easy to monitor and debug")
    print()
    print("Disadvantages:")
    print("  ✗ More complex than simple patterns")
    print("  ✗ Coordination overhead")
    print("  ✗ Requires good task decomposition")
    print("  ✗ More agents = more resource usage")
    print()
    print("Best Used For:")
    print("  • Complex multi-step projects")
    print("  • Tasks requiring multiple specializations")
    print("  • Large-scale data processing")
    print("  • Quality-critical workflows")
    print("  • Distributed team simulations")
    print()
    print("Key Roles:")
    print("  • COORDINATOR: Strategic oversight, quality assurance")
    print("  • DELEGATOR: Task breakdown, resource allocation")
    print("  • WORKERS: Specialized execution")
    print("  • AGGREGATOR: Result synthesis")
    print()
    print("Variations:")
    print("  • Dynamic worker pool (scale workers based on load)")
    print("  • Hierarchical CDW (multi-level delegation)")
    print("  • Competitive CDW (multiple workers compete)")
    print("  • Feedback loop CDW (iterative refinement)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
