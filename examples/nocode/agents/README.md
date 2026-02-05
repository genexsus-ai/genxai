# Agent Definitions (No-Code Examples)

This directory contains **reusable agent definitions** used by the no-code workflow examples in `examples/nocode/`.

## Structure

- `content_agents.yaml` – agents for content generation workflows
- `support_agents.yaml` – agents for customer support workflows
- `data_agents.yaml` – agents for data validation/processing workflows
- `common_agents.yaml` – shared/utility agents that can be reused

## Format

Each file contains an `agents` list with the following fields:

- `id`: unique agent identifier
- `role`: human-readable role name
- `goal`: objective of the agent
- `backstory`: background/context (optional)
- `llm_provider`: LLM provider (default: `openai`)
- `llm_model`: LLM model (default: `gpt-4`)
- `llm_temperature`: generation temperature
- `tools`: list of tool names the agent can access
- `memory`: memory configuration (optional)
- `behavior`: agent behavior configuration (optional)

## Usage

These files are intended as **reference templates**. Workflows can either inline agents (as in current examples) or import these definitions depending on how you choose to implement loading.

If you later add a loader for external agent definitions, this directory becomes the shared agent catalog for no-code workflows.
