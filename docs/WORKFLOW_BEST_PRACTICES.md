# GenXAI Workflow Best Practices

This guide provides comprehensive best practices for designing, implementing, and maintaining workflows in the GenXAI framework.

## Table of Contents

1. [Design Principles](#design-principles)
2. [Pattern Selection](#pattern-selection)
3. [State Management](#state-management)
4. [Error Handling](#error-handling)
5. [Performance Optimization](#performance-optimization)
6. [Memory Management](#memory-management)
7. [Tool Selection](#tool-selection)
8. [Testing Strategies](#testing-strategies)
9. [Monitoring & Debugging](#monitoring--debugging)
10. [Security Considerations](#security-considerations)
11. [Scalability Patterns](#scalability-patterns)
12. [CDW Pattern Best Practices](#cdw-pattern-best-practices)

---

## Design Principles

### 1. Single Responsibility Principle

Each agent should have one clear, well-defined responsibility.

**✅ Good:**
```python
# Specialized agents
classifier = Agent(role="Request Classifier", goal="Categorize requests")
processor = Agent(role="Data Processor", goal="Process classified data")
```

**❌ Bad:**
```python
# Agent doing too much
super_agent = Agent(
    role="Do Everything Agent",
    goal="Classify, process, validate, and report"
)
```

### 2. Separation of Concerns

Keep coordination, delegation, execution, and aggregation separate.

**✅ Good (CDW Pattern):**
```python
coordinator → delegator → workers → aggregator
```

**❌ Bad:**
```python
# Single agent doing coordination AND execution
mega_agent → output
```

### 3. Fail Fast, Fail Gracefully

Validate inputs early and handle failures appropriately.

```python
# Validate graph before execution
try:
    graph.validate()
except GraphExecutionError as e:
    logger.error(f"Graph validation failed: {e}")
    return error_response

# Set max iterations to prevent infinite loops
result = await graph.run(input_data, max_iterations=100)
```

### 4. Idempotency

Workflows should produce the same result when run multiple times with the same input.

```python
# Use deterministic settings for reproducibility
agent = AgentFactory.create_agent(
    id="processor",
    temperature=0.0,  # Deterministic
    seed=42  # Reproducible
)
```

---

## Pattern Selection

### Decision Matrix

| Requirement | Recommended Pattern |
|-------------|-------------------|
| Simple linear flow | Sequential |
| Different paths based on conditions | Conditional Branching |
| Independent parallel tasks | Parallel Execution |
| Complex multi-specialist project | CDW |
| Quality refinement needed | Cyclic/Iterative |
| Large-scale distributed processing | Map-Reduce |
| Long-running transactions | Saga |

### Pattern Combination

Patterns can be combined for complex workflows:

```python
# CDW + Conditional Branching
coordinator → delegator → [conditional routing] → workers → aggregator

# Parallel + Cyclic
parallel_workers → aggregator → validator → (if fail) → refiner → validator
```

---

## State Management

### 1. Use Schema Validation

Define clear state schemas to prevent errors.

```python
from genxai.core.state.schema import StateSchema

schema = StateSchema(
    required_fields=["input", "category", "priority"],
    optional_fields=["metadata", "history"],
    field_types={
        "priority": int,
        "category": str
    }
)

state_manager = StateManager(schema=schema)
```

### 2. Checkpoint Critical States

Save state at important milestones for recovery.

```python
# Before expensive operations
state_manager.checkpoint("before_analysis")

try:
    result = await expensive_operation()
except Exception as e:
    # Restore from checkpoint
    state_manager.restore("before_analysis")
    logger.error(f"Operation failed: {e}")
```

### 3. Version State Changes

Track state evolution for debugging and auditing.

```python
# Enable versioning
state_manager = StateManager(enable_versioning=True)

# Access history
history = state_manager.get_history()
for version in history:
    print(f"Version {version.id}: {version.changes}")
```

### 4. Clean Up State

Remove unnecessary data to prevent memory bloat.

```python
# Remove temporary data after use
state_manager.remove("temp_calculations")
state_manager.remove("intermediate_results")

# Keep only essential data
state_manager.keep_only(["final_result", "metadata"])
```

---

## Error Handling

### 1. Implement Retry Logic

Use exponential backoff for transient failures.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm_with_retry(agent, input_data):
    return await agent.execute(input_data)
```

### 2. Circuit Breaker Pattern

Prevent cascading failures.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
```

### 3. Graceful Degradation

Provide fallback options when components fail.

```python
try:
    result = await primary_agent.execute(input_data)
except Exception as e:
    logger.warning(f"Primary agent failed: {e}, using fallback")
    result = await fallback_agent.execute(input_data)
```

### 4. Timeout Handling

Prevent workflows from hanging indefinitely.

```python
import asyncio

try:
    result = await asyncio.wait_for(
        graph.run(input_data),
        timeout=300  # 5 minutes
    )
except asyncio.TimeoutError:
    logger.error("Workflow execution timed out")
    # Handle timeout appropriately
```

---

## Performance Optimization

### 1. Use Parallel Execution

Execute independent tasks concurrently.

```python
# Mark edges as parallel
graph.add_edge(Edge(
    source="delegator",
    target="worker1",
    metadata={"parallel": True}
))
```

### 2. Implement Caching

Cache expensive computations and LLM responses.

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    return embedding_model.encode(text)

# Or use Redis for distributed caching
cache = RedisCache(host="localhost", port=6379)
result = await cache.get_or_compute(key, expensive_function)
```

### 3. Batch Processing

Process multiple items together when possible.

```python
# Instead of processing one at a time
for item in items:
    result = await process_item(item)

# Batch process
results = await process_items_batch(items, batch_size=10)
```

### 4. Lazy Loading

Load resources only when needed.

```python
class LazyAgent:
    def __init__(self, config):
        self.config = config
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = load_llm(self.config)
        return self._llm
```

### 5. Connection Pooling

Reuse database and API connections.

```python
# Use connection pool
from sqlalchemy import create_engine
engine = create_engine(
    "postgresql://...",
    pool_size=10,
    max_overflow=20
)
```

---

## Memory Management

### Shared Memory (Workflow Level)

You can enable a shared memory bus for all agents in a workflow. This lets agents
read/write a shared state during execution. See the no-code example at
`examples/nocode/shared_memory_workflow.yaml`.

You can also set workflow-level memory defaults that apply to all agents unless
explicitly overridden on the agent itself:

```yaml
workflow:
  name: "Shared Memory Example"
  memory:
    enabled: true
    type: "short_term"
  agents:
    - id: "agent_one"
      role: "Agent One"
      memory:
        enabled: false  # overrides workflow defaults
```

**Workflow YAML example:**

```yaml
workflow:
  name: "Shared Memory Example"
  memory:
    shared: true
  agents:
    - id: "agent_one"
      role: "Agent One"
      goal: "Collaborate"
  graph:
    nodes:
      - id: "start"
        type: "input"
      - id: "agent_one"
        type: "agent"
      - id: "end"
        type: "output"
    edges:
      - from: "start"
        to: "agent_one"
      - from: "agent_one"
        to: "end"
```

When enabled, the shared memory contents are injected into the agent prompt and
can also be accessed in runtime context.

### 1. Choose Appropriate Memory Types

Use the right memory type for each use case.

```python
# Short-term: Recent conversation context
agent.memory = "short_term"  # Last N messages

# Long-term: Persistent knowledge
agent.memory = "long_term"  # Vector database

# Episodic: Past experiences
agent.memory = "episodic"  # Graph database

# Procedural: Learned skills
agent.memory = "procedural"  # Skill trees

# Semantic: Factual knowledge
agent.memory = "semantic"  # Knowledge graph
```

### 2. Implement Memory Consolidation

Periodically optimize memory storage.

```python
# Run consolidation during low-traffic periods
async def consolidate_memory():
    # Move important short-term to long-term
    important_memories = await short_term.get_important(threshold=0.8)
    await long_term.store_batch(important_memories)
    
    # Forget low-importance memories
    await short_term.forget(importance_threshold=0.3)
    
    # Extract patterns from episodic
    patterns = await episodic.extract_patterns()
    await semantic.store_facts(patterns)
```

### 3. Set Memory Limits

Prevent unbounded memory growth.

```python
memory_config = {
    "short_term": {
        "max_items": 100,
        "eviction_policy": "LRU"
    },
    "long_term": {
        "max_size_mb": 1000,
        "compression": True
    }
}
```

### 4. Use Memory Efficiently

Query memory strategically.

```python
# Use semantic search instead of full scan
relevant_memories = await memory.search(
    query="customer complaints",
    top_k=5,
    filters={"category": "support"}
)

# Use memory selectively
if task_requires_history:
    context = await memory.get_context(task_id)
```

---

## Tool Selection

### 1. Match Tools to Agent Roles

Provide agents with tools relevant to their responsibilities.

```python
# Research agent
research_agent = Agent(
    role="Researcher",
    tools=["web_search", "document_reader", "summarizer"]
)

# Analysis agent
analysis_agent = Agent(
    role="Analyst",
    tools=["calculator", "statistical_analyzer", "visualizer"]
)
```

### 2. Implement Tool Validation

Validate tool inputs before execution.

```python
class CalculatorTool(Tool):
    def validate_input(self, expression: str) -> bool:
        # Check for dangerous operations
        dangerous_patterns = ["__", "eval", "exec", "import"]
        return not any(p in expression for p in dangerous_patterns)
    
    async def execute(self, expression: str):
        if not self.validate_input(expression):
            raise ToolValidationError("Invalid expression")
        return eval(expression)
```

### 3. Tool Composition

Combine simple tools for complex operations.

```python
# Composite tool
class ResearchAndAnalyzeTool(Tool):
    def __init__(self):
        self.search_tool = WebSearchTool()
        self.analyzer_tool = DataAnalyzerTool()
    
    async def execute(self, query: str):
        # Search
        results = await self.search_tool.execute(query)
        # Analyze
        analysis = await self.analyzer_tool.execute(results)
        return analysis
```

### 4. Tool Metrics

Track tool usage and performance.

```python
class MetricsTrackingTool(Tool):
    def __init__(self, base_tool):
        self.base_tool = base_tool
        self.metrics = {
            "calls": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0
        }
    
    async def execute(self, *args, **kwargs):
        start_time = time.time()
        self.metrics["calls"] += 1
        
        try:
            result = await self.base_tool.execute(*args, **kwargs)
            self.metrics["successes"] += 1
            return result
        except Exception as e:
            self.metrics["failures"] += 1
            raise e
        finally:
            self.metrics["total_time"] += time.time() - start_time
```

---

## Testing Strategies

### 1. Unit Tests

Test individual agents in isolation.

```python
import pytest

@pytest.mark.asyncio
async def test_classifier_agent():
    agent = AgentFactory.create_agent(
        id="classifier",
        role="Classifier"
    )
    
    result = await agent.execute({
        "text": "My app crashed"
    })
    
    assert result["category"] == "technical"
    assert result["priority"] in ["low", "normal", "high"]
```

### 2. Integration Tests

Test agent interactions and workflows.

```python
@pytest.mark.asyncio
async def test_support_workflow():
    graph = create_support_workflow()
    
    result = await graph.run({
        "request": "Billing issue"
    })
    
    assert result["status"] == "resolved"
    assert "billing" in result["handler"]
```

### 3. End-to-End Tests

Test complete workflows with real data.

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_workflow():
    # Setup
    input_data = load_test_data("customer_request.json")
    
    # Execute
    result = await run_production_workflow(input_data)
    
    # Verify
    assert result["quality_score"] >= 8.0
    assert result["response_time"] < 30.0
```

### 4. Load Tests

Test performance under load.

```python
import asyncio

async def load_test():
    tasks = []
    for i in range(100):
        task = asyncio.create_task(
            graph.run({"request": f"Test {i}"})
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Analyze results
    success_rate = sum(1 for r in results if r["status"] == "success") / len(results)
    avg_time = sum(r["time"] for r in results) / len(results)
    
    assert success_rate >= 0.95
    assert avg_time < 5.0
```

---

## Monitoring & Debugging

### 1. Structured Logging

Use structured logging for better observability.

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "workflow_started",
    workflow_id=workflow_id,
    input_size=len(input_data),
    timestamp=datetime.now().isoformat()
)
```

### 2. Distributed Tracing

Track requests across agents.

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("workflow_execution") as span:
    span.set_attribute("workflow.id", workflow_id)
    span.set_attribute("workflow.type", "cdw")
    
    result = await graph.run(input_data)
    
    span.set_attribute("workflow.status", result["status"])
```

### 3. Metrics Collection

Track key performance indicators.

```python
from prometheus_client import Counter, Histogram

workflow_executions = Counter(
    "workflow_executions_total",
    "Total workflow executions",
    ["workflow_type", "status"]
)

workflow_duration = Histogram(
    "workflow_duration_seconds",
    "Workflow execution duration"
)

# Use metrics
with workflow_duration.time():
    result = await graph.run(input_data)
    workflow_executions.labels(
        workflow_type="cdw",
        status=result["status"]
    ).inc()
```

### 4. Debug Mode

Enable detailed debugging when needed.

```python
# Enable debug mode
graph = Graph(name="workflow", debug=True)

# Debug output shows:
# - Node execution order
# - State changes
# - Edge evaluations
# - Timing information
```

---

## Security Considerations

### 1. Input Validation

Validate and sanitize all inputs.

```python
from pydantic import BaseModel, validator

class WorkflowInput(BaseModel):
    text: str
    category: str
    
    @validator("text")
    def validate_text(cls, v):
        if len(v) > 10000:
            raise ValueError("Text too long")
        # Remove dangerous patterns
        dangerous = ["<script>", "javascript:", "eval("]
        if any(d in v.lower() for d in dangerous):
            raise ValueError("Invalid input")
        return v
```

### 2. Access Control

Implement role-based access control.

```python
class WorkflowAccessControl:
    def __init__(self):
        self.permissions = {
            "admin": ["create", "read", "update", "delete", "execute"],
            "user": ["read", "execute"],
            "viewer": ["read"]
        }
    
    def check_permission(self, user_role: str, action: str) -> bool:
        return action in self.permissions.get(user_role, [])
```

### 3. Data Encryption

Encrypt sensitive data at rest and in transit.

```python
from cryptography.fernet import Fernet

class EncryptedStateManager(StateManager):
    def __init__(self, encryption_key):
        super().__init__()
        self.cipher = Fernet(encryption_key)
    
    def set(self, key: str, value: Any):
        encrypted_value = self.cipher.encrypt(
            json.dumps(value).encode()
        )
        super().set(key, encrypted_value)
    
    def get(self, key: str):
        encrypted_value = super().get(key)
        decrypted = self.cipher.decrypt(encrypted_value)
        return json.loads(decrypted.decode())
```

### 4. Rate Limiting

Prevent abuse and resource exhaustion.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
async def execute_workflow(request):
    return await graph.run(request.input_data)
```

---

## Scalability Patterns

### 1. Horizontal Scaling

Scale by adding more instances.

```python
# Stateless workflow execution
# Can run on multiple workers
async def execute_workflow(workflow_id, input_data):
    graph = load_workflow(workflow_id)
    result = await graph.run(input_data)
    return result

# Deploy with Kubernetes
# kubectl scale deployment workflow-executor --replicas=10
```

### 2. Load Balancing

Distribute work across workers.

```python
from celery import Celery

app = Celery('workflows', broker='redis://localhost:6379')

@app.task
def execute_workflow_task(workflow_id, input_data):
    return asyncio.run(execute_workflow(workflow_id, input_data))

# Submit tasks
for input_data in batch:
    execute_workflow_task.delay(workflow_id, input_data)
```

### 3. Caching Strategy

Implement multi-level caching.

```python
# L1: In-memory cache (fast, small)
# L2: Redis cache (medium, medium)
# L3: Database (slow, large)

async def get_with_cache(key):
    # Try L1
    if key in memory_cache:
        return memory_cache[key]
    
    # Try L2
    value = await redis_cache.get(key)
    if value:
        memory_cache[key] = value
        return value
    
    # Try L3
    value = await database.get(key)
    if value:
        await redis_cache.set(key, value)
        memory_cache[key] = value
    
    return value
```

### 4. Async Processing

Use message queues for async workflows.

```python
# Producer
async def submit_workflow(input_data):
    message = {
        "workflow_id": "customer_support",
        "input_data": input_data,
        "callback_url": "https://api.example.com/callback"
    }
    await message_queue.publish("workflows", message)
    return {"status": "queued", "job_id": generate_id()}

# Consumer
async def process_workflow_queue():
    async for message in message_queue.consume("workflows"):
        result = await execute_workflow(
            message["workflow_id"],
            message["input_data"]
        )
        await notify_callback(message["callback_url"], result)
```

---

## CDW Pattern Best Practices

### 1. Coordinator Responsibilities

The coordinator should focus on high-level oversight.

```python
coordinator = Agent(
    role="Project Coordinator",
    goal="Ensure project success and quality",
    responsibilities=[
        "Define success criteria",
        "Monitor overall progress",
        "Ensure quality standards",
        "Handle escalations"
    ],
    # Coordinator should NOT do detailed work
    tools=["project_tracker", "quality_checker"]
)
```

### 2. Delegator Strategies

Implement intelligent task delegation.

```python
class SmartDelegator:
    def delegate_tasks(self, project, workers):
        tasks = self.decompose_project(project)
        
        # Consider worker capabilities
        assignments = {}
        for task in tasks:
            best_worker = self.find_best_worker(task, workers)
            assignments[task.id] = best_worker
        
        # Balance workload
        assignments = self.balance_workload(assignments, workers)
        
        return assignments
    
    def find_best_worker(self, task, workers):
        scores = []
        for worker in workers:
            score = self.calculate_fit_score(task, worker)
            scores.append((worker, score))
        return max(scores, key=lambda x: x[1])[0]
```

### 3. Worker Specialization

Create highly specialized workers.

```python
# Good: Specialized workers
research_worker = Agent(
    role="Research Specialist",
    goal="Conduct thorough research",
    tools=["web_search", "academic_search", "document_reader"]
)

# Bad: Generic worker
generic_worker = Agent(
    role="General Worker",
    goal="Do whatever is needed",
    tools=["everything"]  # Too broad
)
```

### 4. Aggregation Strategies

Implement smart result aggregation.

```python
class IntelligentAggregator:
    async def aggregate(self, worker_results):
        # Validate all results
        validated = [r for r in worker_results if self.validate(r)]
        
        # Resolve conflicts
        if self.has_conflicts(validated):
            resolved = await self.resolve_conflicts(validated)
        else:
            resolved = validated
        
        # Synthesize final output
        final = self.synthesize(resolved)
        
        # Add metadata
        final["metadata"] = {
            "worker_count": len(worker_results),
            "validation_rate": len(validated) / len(worker_results),
            "confidence": self.calculate_confidence(validated)
        }
        
        return final
```

### 5. Dynamic Worker Scaling

Scale workers based on workload.

```python
class DynamicWorkerPool:
    def __init__(self, min_workers=2, max_workers=10):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.workers = []
    
    async def scale_workers(self, task_queue_size):
        target_workers = min(
            max(self.min_workers, task_queue_size // 5),
            self.max_workers
        )
        
        if len(self.workers) < target_workers:
            # Scale up
            for _ in range(target_workers - len(self.workers)):
                worker = await self.create_worker()
                self.workers.append(worker)
        elif len(self.workers) > target_workers:
            # Scale down
            excess = len(self.workers) - target_workers
            for _ in range(excess):
                worker = self.workers.pop()
                await worker.shutdown()
```

---

## Summary

Following these best practices will help you build robust, scalable, and maintainable workflows with GenXAI:

1. ✅ **Design**: Follow SOLID principles, separate concerns
2. ✅ **Patterns**: Choose the right pattern for your use case
3. ✅ **State**: Manage state carefully with validation and checkpoints
4. ✅ **Errors**: Handle failures gracefully with retries and fallbacks
5. ✅ **Performance**: Optimize with caching, batching, and parallelization
6. ✅ **Memory**: Use appropriate memory types and consolidation
7. ✅ **Tools**: Match tools to agents, validate inputs
8. ✅ **Testing**: Comprehensive unit, integration, and E2E tests
9. ✅ **Monitoring**: Structured logging, tracing, and metrics
10. ✅ **Security**: Validate inputs, encrypt data, control access
11. ✅ **Scale**: Horizontal scaling, load balancing, async processing
12. ✅ **CDW**: Proper separation of coordinator, delegator, workers

---

**For more information, see:**
- [Workflow Patterns](../examples/patterns/README.md)
- [Architecture Guide](../ARCHITECTURE.md)
- [API Reference](./API.md)
