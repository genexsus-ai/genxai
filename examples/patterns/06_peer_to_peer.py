"""
Peer-to-Peer (P2P) Pattern Example

This pattern demonstrates decentralized agent communication where agents
interact directly with each other without a central manager or coordinator.
Agents make autonomous decisions about who to communicate with and when
to terminate the conversation.

Pattern Structure:
    Agent1 ←→ Agent2
      ↕         ↕
    Agent3 ←→ Agent4

Key Features:
- No central manager/coordinator
- Direct agent-to-agent communication
- Consensus-based decision making
- Multiple termination strategies
- Emergent behavior from interactions

Use Cases:
- Collaborative problem-solving
- Distributed decision-making
- Multi-agent negotiation
- Consensus building
- Peer review systems
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Termination Controller
# ============================================================================

class P2PTerminationController:
    """Controls termination conditions for P2P agent conversations."""
    
    def __init__(
        self,
        max_iterations: int = 10,
        timeout_seconds: float = 300,
        consensus_threshold: float = 0.66,
        convergence_window: int = 3,
        quality_threshold: float = 0.85
    ):
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds
        self.consensus_threshold = consensus_threshold
        self.convergence_window = convergence_window
        self.quality_threshold = quality_threshold
        self.start_time = datetime.now()
        
    def should_terminate(
        self,
        state: Dict[str, Any],
        agents: List[Any],
        iteration: int,
        message_history: List[Dict[str, Any]]
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if the P2P conversation should terminate.
        
        Returns:
            (should_terminate, reason)
        """
        # 1. Hard limit: Max iterations (safety)
        if iteration >= self.max_iterations:
            return True, f"Max iterations reached ({self.max_iterations})"
        
        # 2. Hard limit: Timeout (safety)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed >= self.timeout_seconds:
            return True, f"Timeout reached ({self.timeout_seconds}s)"
        
        # 3. Goal achievement
        if self._goal_achieved(state):
            return True, "Goal achieved"
        
        # 4. Consensus to terminate
        if self._consensus_reached(agents):
            return True, "Consensus to terminate"
        
        # 5. Convergence detection
        if self._detect_convergence(message_history):
            return True, "Conversation converged"
        
        # 6. Quality threshold met
        if self._quality_threshold_met(state):
            return True, "Quality threshold met"
        
        # 7. Deadlock detection
        if self._detect_deadlock(message_history):
            return True, "Deadlock detected"
        
        return False, None
    
    def _goal_achieved(self, state: Dict[str, Any]) -> bool:
        """Check if the goal has been achieved."""
        return state.get('goal_achieved', False)
    
    def _consensus_reached(self, agents: List[Any]) -> bool:
        """Check if agents have reached consensus to terminate."""
        if not agents:
            return False
        
        termination_votes = sum(1 for agent in agents if agent.wants_to_terminate)
        vote_ratio = termination_votes / len(agents)
        
        return vote_ratio >= self.consensus_threshold
    
    def _detect_convergence(self, message_history: List[Dict[str, Any]]) -> bool:
        """Detect if the conversation has converged (no new information)."""
        if len(message_history) < self.convergence_window:
            return False
        
        # Check last N messages for similarity
        recent_messages = message_history[-self.convergence_window:]
        
        # Simple convergence: check if messages are becoming repetitive
        unique_contents = set(msg.get('content', '')[:100] for msg in recent_messages)
        
        # If very few unique messages, conversation has converged
        return len(unique_contents) <= 2
    
    def _quality_threshold_met(self, state: Dict[str, Any]) -> bool:
        """Check if solution quality meets threshold."""
        quality = state.get('solution_quality', 0.0)
        return quality >= self.quality_threshold
    
    def _detect_deadlock(self, message_history: List[Dict[str, Any]]) -> bool:
        """Detect if agents are in a deadlock (circular arguments)."""
        if len(message_history) < 6:
            return False
        
        # Check for repeating patterns in recent messages
        recent = message_history[-6:]
        
        # Simple deadlock detection: same sender pattern repeating
        senders = [msg.get('sender', '') for msg in recent]
        
        # Check if pattern repeats (e.g., A->B->A->B->A->B)
        if len(senders) >= 6:
            pattern1 = senders[:3]
            pattern2 = senders[3:6]
            if pattern1 == pattern2:
                return True
        
        return False


# ============================================================================
# Simple Agent Implementation
# ============================================================================

class P2PAgent:
    """Simple agent for P2P communication demonstration."""
    
    def __init__(
        self,
        agent_id: str,
        role: str,
        expertise: str,
        personality: str = "collaborative"
    ):
        self.agent_id = agent_id
        self.role = role
        self.expertise = expertise
        self.personality = personality
        self.wants_to_terminate = False
        self.messages_received: List[Dict[str, Any]] = []
        self.contribution_count = 0
        self.satisfaction_level = 0.0
        
    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process incoming message from another agent."""
        self.messages_received.append(message)
        logger.info(f"{self.agent_id} received message from {message['sender']}")
        
    async def generate_response(
        self,
        context: Dict[str, Any],
        other_agents: List['P2PAgent']
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a response based on current context and other agents' inputs.
        
        In a real implementation, this would use an LLM to generate intelligent
        responses. For this demo, we simulate agent behavior.
        """
        self.contribution_count += 1
        
        # Simulate agent decision-making
        if self.contribution_count >= 3:
            # After 3 contributions, agent becomes more satisfied
            self.satisfaction_level = min(1.0, self.satisfaction_level + 0.3)
        
        # Decide if agent wants to terminate
        if self.satisfaction_level >= 0.8:
            self.wants_to_terminate = True
        
        # Generate message content (simulated)
        message = {
            'sender': self.agent_id,
            'role': self.role,
            'content': self._generate_content(context),
            'timestamp': datetime.now().isoformat(),
            'contribution_number': self.contribution_count,
            'satisfaction': self.satisfaction_level,
            'wants_to_terminate': self.wants_to_terminate
        }
        
        return message
    
    def _generate_content(self, context: Dict[str, Any]) -> str:
        """Generate message content based on role and expertise."""
        problem = context.get('problem', 'the problem')
        
        # Simulate different agent perspectives
        templates = {
            'analyst': f"Based on my analysis of {problem}, I suggest we consider...",
            'designer': f"From a design perspective on {problem}, we should...",
            'engineer': f"The technical approach to {problem} should involve...",
            'reviewer': f"Reviewing the proposals for {problem}, I think..."
        }
        
        template = templates.get(self.role, f"My perspective on {problem} is...")
        return f"{template} [Contribution #{self.contribution_count}]"
    
    def evaluate_solution(self, state: Dict[str, Any]) -> float:
        """Evaluate the current solution quality from this agent's perspective."""
        # Simulate evaluation (in real implementation, would use LLM)
        base_quality = min(1.0, self.contribution_count * 0.2)
        return base_quality
    
    def __repr__(self) -> str:
        return f"P2PAgent(id={self.agent_id}, role={self.role})"


# ============================================================================
# P2P Message Bus
# ============================================================================

class SimpleMessageBus:
    """Simple message bus for P2P agent communication."""
    
    def __init__(self):
        self.message_history: List[Dict[str, Any]] = []
        
    async def broadcast(self, message: Dict[str, Any], agents: List[P2PAgent]) -> None:
        """Broadcast message to all agents except sender."""
        self.message_history.append(message)
        
        sender_id = message['sender']
        for agent in agents:
            if agent.agent_id != sender_id:
                await agent.process_message(message)
    
    async def send_to(
        self,
        message: Dict[str, Any],
        recipient: P2PAgent
    ) -> None:
        """Send message to specific agent."""
        self.message_history.append(message)
        await recipient.process_message(message)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get message history."""
        return self.message_history.copy()


# ============================================================================
# P2P Workflow Orchestrator
# ============================================================================

class P2PWorkflow:
    """Orchestrates P2P agent workflow with multiple termination strategies."""
    
    def __init__(
        self,
        agents: List[P2PAgent],
        termination_controller: P2PTerminationController,
        message_bus: SimpleMessageBus
    ):
        self.agents = agents
        self.termination_controller = termination_controller
        self.message_bus = message_bus
        self.state: Dict[str, Any] = {
            'goal_achieved': False,
            'solution_quality': 0.0,
            'iteration': 0
        }
        
    async def run(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the P2P workflow.
        
        Args:
            initial_context: Initial problem/context for agents
            
        Returns:
            Final state with results
        """
        logger.info("=" * 80)
        logger.info("Starting P2P Workflow")
        logger.info(f"Agents: {[agent.agent_id for agent in self.agents]}")
        logger.info(f"Problem: {initial_context.get('problem', 'N/A')}")
        logger.info("=" * 80)
        
        self.state['context'] = initial_context
        iteration = 0
        
        while True:
            iteration += 1
            self.state['iteration'] = iteration
            
            logger.info(f"\n--- Iteration {iteration} ---")
            
            # Each agent generates a response based on current context
            for agent in self.agents:
                message = await agent.generate_response(
                    context=self.state['context'],
                    other_agents=self.agents
                )
                
                if message:
                    # Broadcast to other agents
                    await self.message_bus.broadcast(message, self.agents)
                    logger.info(
                        f"  {agent.agent_id}: {message['content'][:80]}... "
                        f"(satisfaction: {message['satisfaction']:.2f})"
                    )
            
            # Update solution quality based on agent evaluations
            quality_scores = [agent.evaluate_solution(self.state) for agent in self.agents]
            self.state['solution_quality'] = sum(quality_scores) / len(quality_scores)
            
            # Check if goal is achieved (simple heuristic)
            if self.state['solution_quality'] >= 0.8:
                self.state['goal_achieved'] = True
            
            # Check termination conditions
            should_terminate, reason = self.termination_controller.should_terminate(
                state=self.state,
                agents=self.agents,
                iteration=iteration,
                message_history=self.message_bus.get_history()
            )
            
            if should_terminate:
                logger.info(f"\n{'=' * 80}")
                logger.info(f"Termination: {reason}")
                logger.info(f"{'=' * 80}")
                break
            
            # Small delay to simulate processing time
            await asyncio.sleep(0.1)
        
        # Finalize results
        return self._finalize_results()
    
    def _finalize_results(self) -> Dict[str, Any]:
        """Aggregate final results from all agents."""
        return {
            'iterations': self.state['iteration'],
            'solution_quality': self.state['solution_quality'],
            'goal_achieved': self.state['goal_achieved'],
            'total_messages': len(self.message_bus.get_history()),
            'agent_contributions': {
                agent.agent_id: {
                    'contributions': agent.contribution_count,
                    'satisfaction': agent.satisfaction_level,
                    'wanted_to_terminate': agent.wants_to_terminate
                }
                for agent in self.agents
            },
            'message_history': self.message_bus.get_history()
        }


# ============================================================================
# Example Usage
# ============================================================================

async def example_collaborative_problem_solving():
    """
    Example: Collaborative Problem Solving
    
    Four agents with different expertise collaborate to solve a problem
    without a central coordinator. They communicate peer-to-peer and
    reach consensus on when to terminate.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Collaborative Problem Solving (P2P)")
    print("=" * 80)
    
    # Create agents with different roles
    agents = [
        P2PAgent(
            agent_id="analyst_1",
            role="analyst",
            expertise="data analysis",
            personality="analytical"
        ),
        P2PAgent(
            agent_id="designer_1",
            role="designer",
            expertise="UX design",
            personality="creative"
        ),
        P2PAgent(
            agent_id="engineer_1",
            role="engineer",
            expertise="software engineering",
            personality="pragmatic"
        ),
        P2PAgent(
            agent_id="reviewer_1",
            role="reviewer",
            expertise="quality assurance",
            personality="critical"
        )
    ]
    
    # Create termination controller with multiple strategies
    termination_controller = P2PTerminationController(
        max_iterations=8,
        timeout_seconds=60,
        consensus_threshold=0.75,  # 75% of agents must agree
        convergence_window=3,
        quality_threshold=0.85
    )
    
    # Create message bus
    message_bus = SimpleMessageBus()
    
    # Create workflow
    workflow = P2PWorkflow(
        agents=agents,
        termination_controller=termination_controller,
        message_bus=message_bus
    )
    
    # Run workflow
    initial_context = {
        'problem': 'Design a new user onboarding flow',
        'constraints': ['mobile-first', 'accessible', 'fast'],
        'goal': 'Create comprehensive onboarding solution'
    }
    
    results = await workflow.run(initial_context)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Iterations: {results['iterations']}")
    print(f"Solution Quality: {results['solution_quality']:.2f}")
    print(f"Goal Achieved: {results['goal_achieved']}")
    print(f"Total Messages: {results['total_messages']}")
    print("\nAgent Contributions:")
    for agent_id, stats in results['agent_contributions'].items():
        print(f"  {agent_id}:")
        print(f"    - Contributions: {stats['contributions']}")
        print(f"    - Satisfaction: {stats['satisfaction']:.2f}")
        print(f"    - Wanted to terminate: {stats['wanted_to_terminate']}")


async def example_consensus_building():
    """
    Example: Consensus Building
    
    Three agents negotiate and build consensus on a decision.
    Demonstrates consensus-based termination.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Consensus Building (P2P)")
    print("=" * 80)
    
    agents = [
        P2PAgent(
            agent_id="stakeholder_1",
            role="analyst",
            expertise="business strategy",
            personality="strategic"
        ),
        P2PAgent(
            agent_id="stakeholder_2",
            role="engineer",
            expertise="technical feasibility",
            personality="practical"
        ),
        P2PAgent(
            agent_id="stakeholder_3",
            role="designer",
            expertise="user experience",
            personality="user-focused"
        )
    ]
    
    termination_controller = P2PTerminationController(
        max_iterations=6,
        consensus_threshold=1.0,  # Require unanimous consent
        quality_threshold=0.9
    )
    
    message_bus = SimpleMessageBus()
    
    workflow = P2PWorkflow(
        agents=agents,
        termination_controller=termination_controller,
        message_bus=message_bus
    )
    
    initial_context = {
        'problem': 'Choose technology stack for new project',
        'options': ['React + Node.js', 'Vue + Python', 'Angular + Java'],
        'goal': 'Reach unanimous decision'
    }
    
    results = await workflow.run(initial_context)
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Iterations: {results['iterations']}")
    print(f"Consensus Reached: {all(s['wanted_to_terminate'] for s in results['agent_contributions'].values())}")
    print(f"Solution Quality: {results['solution_quality']:.2f}")


async def main():
    """Run all examples."""
    await example_collaborative_problem_solving()
    await example_consensus_building()
    
    print("\n" + "=" * 80)
    print("P2P Pattern Demonstration Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. Agents communicate directly without a central manager")
    print("2. Multiple termination strategies ensure conversations end appropriately")
    print("3. Consensus-based decision making enables emergent behavior")
    print("4. Quality thresholds and iteration limits provide safety")
    print("5. P2P patterns are ideal for collaborative and distributed tasks")


if __name__ == "__main__":
    asyncio.run(main())
