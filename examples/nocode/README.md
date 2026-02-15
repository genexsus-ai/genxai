# No-Code Workflow Templates

These YAML templates are designed for the GenXAI Studio and the OSS CLI (`genxai workflow`)
to provide quick-start, visual workflows without writing code.

## Reusable Agent Definitions

Reusable agent templates are available in `examples/nocode/agents/`. Each file defines an
`agents` list that can be referenced by workflows or used as a starting point for authoring
new workflows.

## Available Templates

1. **Customer Support** (`customer_support.yaml`)
   - Classify and route support requests
2. **Content Generation** (`content_generation.yaml`)
   - Research → Draft → Edit pipeline
3. **Data Validation Pipeline** (`data_pipeline.yaml`)
   - Validate, transform, and output structured data
4. **User Proxy Workflow** (`user_proxy_workflow.yaml`)
   - Collect human input via a tool step before the assistant agent runs
5. **Shared Memory Workflow** (`shared_memory_workflow.yaml`)
   - Demonstrates shared memory enabled across agents

## How to Use

```bash
genxai workflow run examples/nocode/customer_support.yaml \
  --input '{"message": "My billing failed"}'
```

Shared memory example:
```bash
genxai workflow run examples/nocode/shared_memory_workflow.yaml \
  --input '{"task": "Draft a short response"}'
```

> Note: Some templates may reference Studio-only features in enterprise builds, but
> the OSS CLI can run standard workflow YAML via `genxai workflow run`.

## Customize

- Adjust agent roles and models
- Add tools per agent
- Add conditional edges for routing
- Replace models with Ollama for local execution

## Using Shared Agents

Each workflow now includes an `agents_ref` field to point at a shared agent file.
You can load and register those agents programmatically:

```python
from pathlib import Path
from genxai.core.graph import load_workflow_yaml, register_workflow_agents

workflow = load_workflow_yaml(Path("examples/nocode/content_generation.yaml"))
register_workflow_agents(workflow)
```