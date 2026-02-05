"""
Conditional Branching Pattern - Decision-Based Routing

This pattern demonstrates conditional routing where workflow execution
branches based on runtime conditions. Different agents are executed
depending on the classification or decision made by a router agent.

Use Cases:
- Customer support ticket routing
- Content categorization and processing
- Risk assessment and handling
- Multi-tier service levels
"""

import asyncio
from genxai.core.graph.engine import Graph
from genxai.core.graph.nodes import InputNode, OutputNode, AgentNode
from genxai.core.graph.edges import Edge, ConditionalEdge
from genxai.core.agent.base import AgentFactory


async def main():
    """Run conditional branching pattern example."""
    print("=" * 70)
    print("CONDITIONAL BRANCHING PATTERN - Decision-Based Routing")
    print("=" * 70)
    print()

    # Create agents
    print("Creating agents...")
    
    # Classifier Agent - Routes to appropriate handler
    classifier = AgentFactory.create_agent(
        id="classifier",
        role="Request Classifier",
        goal="Analyze and categorize incoming requests",
        backstory="Expert at understanding request types and priorities",
        llm_model="gpt-4",
        temperature=0.2,
    )
    
    # Technical Support Agent
    technical_agent = AgentFactory.create_agent(
        id="technical_support",
        role="Technical Support Specialist",
        goal="Resolve technical issues and bugs",
        backstory="Senior engineer with deep technical knowledge",
        tools=["code_analyzer", "debugger", "documentation_search"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    # Billing Support Agent
    billing_agent = AgentFactory.create_agent(
        id="billing_support",
        role="Billing Support Specialist",
        goal="Handle billing inquiries and payment issues",
        backstory="Financial expert with customer service skills",
        tools=["payment_processor", "invoice_generator"],
        llm_model="gpt-4",
        temperature=0.3,
    )
    
    # General Support Agent
    general_agent = AgentFactory.create_agent(
        id="general_support",
        role="General Support Agent",
        goal="Handle general inquiries and questions",
        backstory="Friendly customer service representative",
        tools=["faq_search", "knowledge_base"],
        llm_model="gpt-4",
        temperature=0.5,
    )
    
    # Escalation Agent
    escalation_agent = AgentFactory.create_agent(
        id="escalation",
        role="Senior Support Manager",
        goal="Handle escalated and complex issues",
        backstory="Experienced manager who can handle difficult situations",
        llm_model="gpt-4",
        temperature=0.4,
    )
    
    print(f"✓ Created {5} agents")
    print()

    # Build conditional branching graph
    print("Building conditional branching workflow...")
    graph = Graph(name="conditional_branching_workflow")
    
    # Add nodes
    graph.add_node(InputNode())
    graph.add_node(AgentNode(id="classifier_node", agent_id="classifier"))
    graph.add_node(AgentNode(id="technical_node", agent_id="technical_support"))
    graph.add_node(AgentNode(id="billing_node", agent_id="billing_support"))
    graph.add_node(AgentNode(id="general_node", agent_id="general_support"))
    graph.add_node(AgentNode(id="escalation_node", agent_id="escalation"))
    graph.add_node(OutputNode())
    
    # Add edges
    graph.add_edge(Edge(source="input", target="classifier_node"))
    
    # Conditional routing based on classification
    graph.add_edge(ConditionalEdge(
        source="classifier_node",
        target="technical_node",
        condition=lambda state: state.get("category") == "technical"
    ))
    
    graph.add_edge(ConditionalEdge(
        source="classifier_node",
        target="billing_node",
        condition=lambda state: state.get("category") == "billing"
    ))
    
    graph.add_edge(ConditionalEdge(
        source="classifier_node",
        target="general_node",
        condition=lambda state: state.get("category") == "general"
    ))
    
    graph.add_edge(ConditionalEdge(
        source="classifier_node",
        target="escalation_node",
        condition=lambda state: state.get("priority") == "urgent"
    ))
    
    # All paths lead to output
    graph.add_edge(Edge(source="technical_node", target="output"))
    graph.add_edge(Edge(source="billing_node", target="output"))
    graph.add_edge(Edge(source="general_node", target="output"))
    graph.add_edge(Edge(source="escalation_node", target="output"))
    
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
    print("                    ┌─→ Technical Support")
    print("                    │")
    print("Input → Classifier ─┼─→ Billing Support")
    print("                    │")
    print("                    ├─→ General Support")
    print("                    │")
    print("                    └─→ Escalation (if urgent)")
    print("                         ↓")
    print("                       Output")
    print("-" * 70)
    print()

    # Test different scenarios
    test_cases = [
        {
            "request": "My application crashes when I click the submit button",
            "expected_category": "technical",
            "expected_priority": "normal"
        },
        {
            "request": "I was charged twice for my subscription",
            "expected_category": "billing",
            "expected_priority": "normal"
        },
        {
            "request": "How do I reset my password?",
            "expected_category": "general",
            "expected_priority": "low"
        },
        {
            "request": "URGENT: Production system is down, losing revenue!",
            "expected_category": "technical",
            "expected_priority": "urgent"
        }
    ]
    
    print("Testing conditional routing with different scenarios...")
    print("=" * 70)
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print("-" * 70)
        print(f"Request: {test_case['request']}")
        print()
        
        # Simulate classification
        category = test_case['expected_category']
        priority = test_case['expected_priority']
        
        print(f"Classifier Analysis:")
        print(f"  → Category: {category}")
        print(f"  → Priority: {priority}")
        print()
        
        # Determine routing
        if priority == "urgent":
            route = "Escalation Agent"
            handler = "Senior Support Manager"
        elif category == "technical":
            route = "Technical Support"
            handler = "Technical Support Specialist"
        elif category == "billing":
            route = "Billing Support"
            handler = "Billing Support Specialist"
        else:
            route = "General Support"
            handler = "General Support Agent"
        
        print(f"Routing Decision:")
        print(f"  → Routed to: {route}")
        print(f"  → Handler: {handler}")
        print()
        
        # Simulate response
        responses = {
            "technical": "I've analyzed the issue. The crash is caused by a validation error. "
                        "I'll create a bug report and provide a workaround.",
            "billing": "I've reviewed your account. I can confirm the duplicate charge. "
                      "I'm processing a refund that will appear in 3-5 business days.",
            "general": "To reset your password, click 'Forgot Password' on the login page. "
                      "You'll receive an email with reset instructions.",
            "urgent": "I'm escalating this to our engineering team immediately. "
                     "We'll have someone on the issue within 15 minutes."
        }
        
        response_key = "urgent" if priority == "urgent" else category
        print(f"Response:")
        print(f"  {responses[response_key]}")
        print()
        print("✓ Request handled successfully")
        print("=" * 70)
        print()

    # Pattern characteristics
    print("=" * 70)
    print("CONDITIONAL BRANCHING PATTERN CHARACTERISTICS")
    print("=" * 70)
    print()
    print("Advantages:")
    print("  ✓ Flexible routing based on runtime conditions")
    print("  ✓ Specialized agents for different scenarios")
    print("  ✓ Efficient resource utilization (only needed agents run)")
    print("  ✓ Easy to add new branches/conditions")
    print()
    print("Disadvantages:")
    print("  ✗ Requires good classification logic")
    print("  ✗ Can become complex with many conditions")
    print("  ✗ Debugging can be harder (multiple paths)")
    print()
    print("Best Used For:")
    print("  • Customer support routing")
    print("  • Content categorization")
    print("  • Risk-based processing")
    print("  • Multi-tier service levels")
    print("  • Dynamic workflow selection")
    print()
    
    print("Condition Types Supported:")
    print("  • Category-based: Route by type (technical, billing, etc.)")
    print("  • Priority-based: Route by urgency (low, normal, urgent)")
    print("  • Value-based: Route by thresholds (amount > 1000)")
    print("  • Complex logic: Combine multiple conditions")
    print()


if __name__ == "__main__":
    asyncio.run(main())
