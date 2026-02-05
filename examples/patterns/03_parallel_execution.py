"""
Parallel Execution Pattern - Concurrent Agent Processing

This pattern demonstrates parallel execution where multiple agents
process the same input simultaneously. Results are then aggregated
to produce a comprehensive output.

Use Cases:
- Multi-perspective analysis
- Parallel data processing
- Consensus building
- Competitive evaluation
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge
from genxai.core.agent.base import AgentFactory


async def main():
    """Run parallel execution pattern example."""
    print("=" * 70)
    print("PARALLEL EXECUTION PATTERN - Concurrent Agent Processing")
    print("=" * 70)
    print()

    # Create agents for parallel processing
    print("Creating agents...")
    
    # Coordinator - Distributes work
    coordinator = AgentFactory.create_agent(
        id="coordinator",
        role="Task Coordinator",
        goal="Prepare and distribute tasks to parallel workers",
        backstory="Efficient organizer who ensures all workers have what they need",
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    # Parallel Worker Agents - Different perspectives
    technical_analyst = AgentFactory.create_agent(
        id="technical_analyst",
        role="Technical Analyst",
        goal="Analyze technical feasibility and implementation details",
        backstory="Senior engineer with deep technical expertise",
        tools=["code_analyzer", "architecture_validator"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    business_analyst = AgentFactory.create_agent(
        id="business_analyst",
        role="Business Analyst",
        goal="Evaluate business value and ROI",
        backstory="MBA with strong business acumen",
        tools=["roi_calculator", "market_analyzer"],
        llm_model="gpt-4",
        temperature=0.4,
    )
    
    risk_analyst = AgentFactory.create_agent(
        id="risk_analyst",
        role="Risk Analyst",
        goal="Identify and assess potential risks",
        backstory="Risk management expert with years of experience",
        tools=["risk_assessor", "compliance_checker"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    ux_analyst = AgentFactory.create_agent(
        id="ux_analyst",
        role="UX Analyst",
        goal="Evaluate user experience and usability",
        backstory="UX designer focused on user-centered design",
        tools=["usability_tester", "accessibility_checker"],
        llm_model="gpt-4",
        temperature=0.5,
    )
    
    # Aggregator - Combines results
    aggregator = AgentFactory.create_agent(
        id="aggregator",
        role="Results Aggregator",
        goal="Synthesize all analyses into comprehensive report",
        backstory="Expert at combining diverse perspectives into actionable insights",
        llm_model="gpt-4",
        temperature=0.4,
    )
    
    print(f"✓ Created {6} agents")
    print()

    # Build parallel execution graph
    print("Building parallel execution workflow...")
    graph = Graph(name="parallel_execution_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="coordinator_node", agent_id="coordinator"))
    graph.add_node(AgentNode(id="technical_node", agent_id="technical_analyst"))
    graph.add_node(AgentNode(id="business_node", agent_id="business_analyst"))
    graph.add_node(AgentNode(id="risk_node", agent_id="risk_analyst"))
    graph.add_node(AgentNode(id="ux_node", agent_id="ux_analyst"))
    graph.add_node(AgentNode(id="aggregator_node", agent_id="aggregator"))
    graph.add_node(OutputNode())
    
    # Add edges
    graph.add_edge(Edge(source="input", target="coordinator_node"))
    
    # Parallel edges from coordinator to all analysts
    graph.add_edge(Edge(
        source="coordinator_node",
        target="technical_node",
        metadata={"parallel": True}
    ))
    graph.add_edge(Edge(
        source="coordinator_node",
        target="business_node",
        metadata={"parallel": True}
    ))
    graph.add_edge(Edge(
        source="coordinator_node",
        target="risk_node",
        metadata={"parallel": True}
    ))
    graph.add_edge(Edge(
        source="coordinator_node",
        target="ux_node",
        metadata={"parallel": True}
    ))
    
    # All analysts feed into aggregator
    graph.add_edge(Edge(source="technical_node", target="aggregator_node"))
    graph.add_edge(Edge(source="business_node", target="aggregator_node"))
    graph.add_edge(Edge(source="risk_node", target="aggregator_node"))
    graph.add_edge(Edge(source="ux_node", target="aggregator_node"))
    
    # Aggregator to output
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
    print("Workflow Structure:")
    print("-" * 70)
    print("                      ┌─→ Technical Analyst ─┐")
    print("                      │                       │")
    print("Input → Coordinator ─┼─→ Business Analyst ─┼→ Aggregator → Output")
    print("                      │                       │")
    print("                      ├─→ Risk Analyst ─────┤")
    print("                      │                       │")
    print("                      └─→ UX Analyst ────────┘")
    print()
    print("Note: All analysts execute in PARALLEL")
    print("-" * 70)
    print()

    # Execute workflow
    print("Executing parallel workflow...")
    print("=" * 70)
    print()
    
    input_data = {
        "project": "New Mobile App Feature",
        "description": "Add real-time chat functionality to mobile app",
        "timeline": "3 months",
        "budget": "$150,000"
    }
    
    print(f"Project: {input_data['project']}")
    print(f"Description: {input_data['description']}")
    print(f"Timeline: {input_data['timeline']}")
    print(f"Budget: {input_data['budget']}")
    print()
    print("-" * 70)
    
    # Simulate parallel execution
    print()
    print("Coordinator: Distributing analysis tasks...")
    print("  → Prepared project brief for all analysts")
    print("  → Launching parallel analysis...")
    print()
    
    import time
    start_time = time.time()
    
    print("Parallel Execution in Progress:")
    print("-" * 70)
    
    # Simulate concurrent execution
    analyses = {
        "technical": {
            "agent": "Technical Analyst",
            "duration": 2.5,
            "findings": [
                "WebSocket implementation required",
                "Need to integrate with existing auth system",
                "Estimated 400 hours of development",
                "Requires backend API updates"
            ]
        },
        "business": {
            "agent": "Business Analyst",
            "duration": 2.3,
            "findings": [
                "Projected 25% increase in user engagement",
                "ROI: 180% over 12 months",
                "Competitive advantage in market",
                "Aligns with Q2 strategic goals"
            ]
        },
        "risk": {
            "agent": "Risk Analyst",
            "duration": 2.7,
            "findings": [
                "Data privacy concerns with real-time messaging",
                "Need GDPR compliance review",
                "Scalability risk with concurrent users",
                "Mitigation: Load testing and encryption"
            ]
        },
        "ux": {
            "agent": "UX Analyst",
            "duration": 2.4,
            "findings": [
                "Positive user feedback in surveys (85%)",
                "Requires intuitive notification system",
                "Accessibility considerations for screen readers",
                "Recommended: A/B testing for UI design"
            ]
        }
    }
    
    # Show parallel execution
    for key, analysis in analyses.items():
        print(f"[{analysis['agent']}] Starting analysis...")
    
    print()
    await asyncio.sleep(0.5)  # Simulate processing time
    
    for key, analysis in analyses.items():
        print(f"[{analysis['agent']}] Analysis complete ({analysis['duration']}s)")
    
    parallel_time = time.time() - start_time
    print()
    print(f"✓ All parallel analyses completed in {parallel_time:.2f}s")
    print("-" * 70)
    print()
    
    # Show individual results
    print("Individual Analysis Results:")
    print("=" * 70)
    print()
    
    for key, analysis in analyses.items():
        print(f"{analysis['agent']} Findings:")
        for finding in analysis['findings']:
            print(f"  • {finding}")
        print()
    
    # Aggregation
    print("-" * 70)
    print("Aggregator: Synthesizing all analyses...")
    print()
    
    print("Comprehensive Project Assessment:")
    print("=" * 70)
    print()
    print("RECOMMENDATION: PROCEED WITH CAUTION")
    print()
    print("Summary:")
    print("  The real-time chat feature shows strong business value with")
    print("  projected 25% engagement increase and 180% ROI. Technical")
    print("  implementation is feasible within the 3-month timeline.")
    print()
    print("Key Considerations:")
    print("  ✓ Strong business case and user demand")
    print("  ✓ Technically feasible with existing infrastructure")
    print("  ⚠ Data privacy and GDPR compliance required")
    print("  ⚠ Scalability testing needed before launch")
    print()
    print("Action Items:")
    print("  1. Conduct GDPR compliance review (Risk)")
    print("  2. Begin technical architecture design (Technical)")
    print("  3. Create A/B testing plan for UI (UX)")
    print("  4. Finalize budget allocation (Business)")
    print()
    print("=" * 70)
    print()

    # Performance comparison
    print("Performance Analysis:")
    print("-" * 70)
    sequential_time = sum(a['duration'] for a in analyses.values())
    speedup = sequential_time / parallel_time
    
    print(f"Sequential execution time: {sequential_time:.2f}s")
    print(f"Parallel execution time: {parallel_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x faster")
    print(f"Efficiency: {(speedup / len(analyses)) * 100:.1f}%")
    print()

    # Pattern characteristics
    print("=" * 70)
    print("PARALLEL EXECUTION PATTERN CHARACTERISTICS")
    print("=" * 70)
    print()
    print("Advantages:")
    print("  ✓ Significant time savings (up to N-x faster)")
    print("  ✓ Multiple perspectives on same problem")
    print("  ✓ Better resource utilization")
    print("  ✓ Fault tolerance (one failure doesn't stop others)")
    print("  ✓ Scalable (add more parallel workers)")
    print()
    print("Disadvantages:")
    print("  ✗ Requires more computational resources")
    print("  ✗ Aggregation complexity increases with workers")
    print("  ✗ Potential for conflicting results")
    print("  ✗ Coordination overhead")
    print()
    print("Best Used For:")
    print("  • Multi-perspective analysis")
    print("  • Independent data processing tasks")
    print("  • Consensus building")
    print("  • Competitive evaluation")
    print("  • Large-scale data processing")
    print()
    print("Implementation Tips:")
    print("  • Ensure tasks are truly independent")
    print("  • Use aggregator to resolve conflicts")
    print("  • Monitor resource usage")
    print("  • Implement timeout mechanisms")
    print("  • Consider partial results if some workers fail")
    print()


if __name__ == "__main__":
    asyncio.run(main())
