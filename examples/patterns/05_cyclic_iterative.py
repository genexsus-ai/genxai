"""
Cyclic/Iterative Pattern - Feedback Loop with Refinement

This pattern demonstrates workflows with cycles and feedback loops,
where outputs are validated and refined iteratively until quality
standards are met.

Use Cases:
- Iterative content refinement
- Quality assurance loops
- Self-correction workflows
- Continuous improvement processes
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge, ConditionalEdge
from genxai.core.agent.base import AgentFactory


async def main():
    """Run cyclic/iterative pattern example."""
    print("=" * 70)
    print("CYCLIC/ITERATIVE PATTERN - Feedback Loop with Refinement")
    print("=" * 70)
    print()

    # Create agents for iterative workflow
    print("Creating agents...")
    
    # Generator Agent - Creates initial output
    generator = AgentFactory.create_agent(
        id="generator",
        role="Content Generator",
        goal="Create initial content based on requirements",
        backstory="Creative writer who generates first drafts quickly",
        llm_model="gpt-4",
        temperature=0.7,
    )
    
    # Validator Agent - Checks quality
    validator = AgentFactory.create_agent(
        id="validator",
        role="Quality Validator",
        goal="Validate content against quality standards",
        backstory="Meticulous reviewer with high standards",
        tools=["grammar_checker", "fact_checker", "quality_scorer"],
        llm_model="gpt-4",
        temperature=0.2,
    )
    
    # Refiner Agent - Improves based on feedback
    refiner = AgentFactory.create_agent(
        id="refiner",
        role="Content Refiner",
        goal="Improve content based on validation feedback",
        backstory="Expert editor who excels at iterative improvement",
        tools=["style_improver", "clarity_enhancer"],
        llm_model="gpt-4",
        temperature=0.5,
    )
    
    # Finalizer Agent - Prepares final output
    finalizer = AgentFactory.create_agent(
        id="finalizer",
        role="Content Finalizer",
        goal="Polish and format final approved content",
        backstory="Professional formatter who adds final touches",
        tools=["formatter", "publisher"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    print(f"✓ Created {4} agents")
    print()

    # Build cyclic graph
    print("Building cyclic/iterative workflow...")
    graph = Graph(name="cyclic_iterative_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="generator_node", agent_id="generator"))
    graph.add_node(AgentNode(id="validator_node", agent_id="validator"))
    graph.add_node(AgentNode(id="refiner_node", agent_id="refiner"))
    graph.add_node(AgentNode(id="finalizer_node", agent_id="finalizer"))
    graph.add_node(OutputNode())
    
    # Add edges
    graph.add_edge(Edge(source="input", target="generator_node"))
    graph.add_edge(Edge(source="generator_node", target="validator_node"))
    
    # Conditional routing based on validation
    # If quality is good, go to finalizer
    graph.add_edge(ConditionalEdge(
        source="validator_node",
        target="finalizer_node",
        condition=lambda state: state.get("quality_score", 0) >= 8.0
    ))
    
    # If quality is poor, go back to refiner (CYCLE)
    graph.add_edge(ConditionalEdge(
        source="validator_node",
        target="refiner_node",
        condition=lambda state: state.get("quality_score", 0) < 8.0
    ))
    
    # Refiner sends back to validator (CYCLE BACK)
    graph.add_edge(Edge(source="refiner_node", target="validator_node"))
    
    # Finalizer to output
    graph.add_edge(Edge(source="finalizer_node", target="output"))
    
    print(f"✓ Graph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print()

    # Validate graph
    print("Validating graph structure...")
    try:
        graph.validate()
        print("✓ Graph validation passed (cycles allowed)")
    except Exception as e:
        print(f"✗ Graph validation failed: {e}")
        return
    print()

    # Visualize workflow
    print("Workflow Structure:")
    print("-" * 70)
    print("                    ┌─────────────┐")
    print("                    │  Generator  │")
    print("                    └──────┬──────┘")
    print("                           │")
    print("                           ↓")
    print("                    ┌──────────────┐")
    print("              ┌────→│  Validator   │")
    print("              │     └──────┬───────┘")
    print("              │            │")
    print("              │     ┌──────┴──────┐")
    print("              │     │             │")
    print("              │     ↓ (score<8)   ↓ (score>=8)")
    print("              │  ┌────────┐   ┌──────────┐")
    print("              └──│Refiner │   │Finalizer │")
    print("                 └────────┘   └────┬─────┘")
    print("                                   │")
    print("                                   ↓")
    print("                              ┌─────────┐")
    print("                              │ Output  │")
    print("                              └─────────┘")
    print()
    print("Note: Refiner → Validator creates a FEEDBACK LOOP")
    print("-" * 70)
    print()

    # Execute workflow with iterations
    print("Executing cyclic workflow...")
    print("=" * 70)
    print()
    
    input_data = {
        "topic": "Benefits of AI in Education",
        "target_audience": "School administrators",
        "word_count": 500,
        "quality_threshold": 8.0
    }
    
    print(f"Topic: {input_data['topic']}")
    print(f"Target Audience: {input_data['target_audience']}")
    print(f"Word Count: {input_data['word_count']}")
    print(f"Quality Threshold: {input_data['quality_threshold']}/10")
    print()
    print("-" * 70)
    print()

    # Simulate iterative execution
    max_iterations = 5
    current_iteration = 0
    quality_scores = []
    
    print("ITERATION 1: Initial Generation")
    print("-" * 70)
    print("[Generator] Creating initial content...")
    await asyncio.sleep(0.3)
    print("  → Generated 487 words")
    print("  → Covered 5 key points")
    print()
    
    print("[Validator] Evaluating content...")
    await asyncio.sleep(0.2)
    quality_score = 6.5
    quality_scores.append(quality_score)
    print(f"  → Quality Score: {quality_score}/10")
    print("  → Issues found:")
    print("    • Lacks specific examples (2 needed)")
    print("    • Tone too technical for audience")
    print("    • Missing call-to-action")
    print(f"  → Decision: REFINE (score < {input_data['quality_threshold']})")
    print()
    
    current_iteration += 1
    
    print("ITERATION 2: First Refinement")
    print("-" * 70)
    print("[Refiner] Improving content based on feedback...")
    await asyncio.sleep(0.3)
    print("  → Added 2 concrete examples")
    print("  → Simplified technical language")
    print("  → Word count: 502")
    print()
    
    print("[Validator] Re-evaluating content...")
    await asyncio.sleep(0.2)
    quality_score = 7.2
    quality_scores.append(quality_score)
    print(f"  → Quality Score: {quality_score}/10")
    print("  → Improvements noted:")
    print("    ✓ Examples added")
    print("    ✓ Language simplified")
    print("  → Remaining issues:")
    print("    • Still missing call-to-action")
    print("    • Could use stronger opening")
    print(f"  → Decision: REFINE (score < {input_data['quality_threshold']})")
    print()
    
    current_iteration += 1
    
    print("ITERATION 3: Second Refinement")
    print("-" * 70)
    print("[Refiner] Further improvements...")
    await asyncio.sleep(0.3)
    print("  → Added compelling call-to-action")
    print("  → Strengthened opening paragraph")
    print("  → Enhanced transitions between sections")
    print("  → Word count: 498")
    print()
    
    print("[Validator] Final evaluation...")
    await asyncio.sleep(0.2)
    quality_score = 8.5
    quality_scores.append(quality_score)
    print(f"  → Quality Score: {quality_score}/10")
    print("  → All quality criteria met:")
    print("    ✓ Specific examples included")
    print("    ✓ Appropriate tone for audience")
    print("    ✓ Clear call-to-action")
    print("    ✓ Strong opening and closing")
    print("    ✓ Proper word count")
    print(f"  → Decision: APPROVE (score >= {input_data['quality_threshold']})")
    print()
    
    current_iteration += 1
    
    print("FINALIZATION")
    print("-" * 70)
    print("[Finalizer] Preparing final output...")
    await asyncio.sleep(0.2)
    print("  → Applied formatting standards")
    print("  → Added metadata")
    print("  → Generated PDF and HTML versions")
    print("  → Content ready for publication")
    print()
    
    print("=" * 70)
    print("FINAL OUTPUT")
    print("=" * 70)
    print()
    print("Title: Benefits of AI in Education")
    print("Target Audience: School Administrators")
    print("Word Count: 498")
    print("Quality Score: 8.5/10")
    print("Iterations Required: 3")
    print()
    print("-" * 70)
    print()
    print("Content Preview:")
    print()
    print("Artificial Intelligence is transforming education in unprecedented")
    print("ways, offering school administrators powerful tools to enhance")
    print("learning outcomes and operational efficiency...")
    print()
    print("[... 498 words total ...]")
    print()
    print("Ready to explore how AI can benefit your institution? Contact our")
    print("education technology team for a personalized consultation.")
    print()
    print("-" * 70)
    print()

    # Show iteration statistics
    print("=" * 70)
    print("ITERATION STATISTICS")
    print("=" * 70)
    print()
    print(f"Total Iterations: {current_iteration}")
    print(f"Refinement Cycles: {current_iteration - 1}")
    print(f"Final Quality Score: {quality_scores[-1]}/10")
    print()
    print("Quality Score Progression:")
    for i, score in enumerate(quality_scores, 1):
        bar = "█" * int(score) + "░" * (10 - int(score))
        status = "✓ APPROVED" if score >= input_data['quality_threshold'] else "⟳ REFINING"
        print(f"  Iteration {i}: [{bar}] {score}/10 - {status}")
    print()
    print(f"Improvement: +{quality_scores[-1] - quality_scores[0]:.1f} points")
    print(f"Success Rate: {(quality_scores[-1] / 10) * 100:.1f}%")
    print()

    # Pattern characteristics
    print("=" * 70)
    print("CYCLIC/ITERATIVE PATTERN CHARACTERISTICS")
    print("=" * 70)
    print()
    print("Advantages:")
    print("  ✓ Continuous quality improvement")
    print("  ✓ Self-correcting workflows")
    print("  ✓ Achieves high quality standards")
    print("  ✓ Learns from feedback")
    print("  ✓ Flexible iteration count")
    print("  ✓ Handles complex quality requirements")
    print()
    print("Disadvantages:")
    print("  ✗ Can be time-consuming")
    print("  ✗ Risk of infinite loops (need max iterations)")
    print("  ✗ Higher computational cost")
    print("  ✗ Requires good validation logic")
    print()
    print("Best Used For:")
    print("  • Content creation and refinement")
    print("  • Quality assurance workflows")
    print("  • Iterative problem solving")
    print("  • Self-improving systems")
    print("  • Complex validation requirements")
    print()
    print("Implementation Tips:")
    print("  • Always set max_iterations to prevent infinite loops")
    print("  • Track quality metrics across iterations")
    print("  • Provide specific feedback for refinement")
    print("  • Consider diminishing returns (stop if no improvement)")
    print("  • Log each iteration for debugging")
    print()
    print("Cycle Control Strategies:")
    print("  1. Quality threshold (score >= target)")
    print("  2. Maximum iterations (prevent infinite loops)")
    print("  3. Improvement delta (stop if change < threshold)")
    print("  4. Time limit (stop after X seconds)")
    print("  5. Manual approval (human-in-the-loop)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
