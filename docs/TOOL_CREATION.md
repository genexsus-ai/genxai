# Tool Creation Guide

This guide explains how to create tools in GenXAI and register them so agents
can use them at runtime. For detailed architecture, see `TOOLS_DESIGN.md`.

---

## 1) Create a Custom Tool (Code)

```python
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory
from genxai.tools.registry import ToolRegistry

class TitleCaseTool(Tool):
    def __init__(self):
        super().__init__(
            metadata=ToolMetadata(
                name="title_case",
                description="Convert text to title case",
                category=ToolCategory.CUSTOM,
                tags=["text", "format"],
            ),
            parameters=[
                ToolParameter(
                    name="text",
                    type="string",
                    description="Input text",
                    required=True,
                )
            ],
        )

    async def _execute(self, **kwargs):
        return {"result": kwargs["text"].title()}

ToolRegistry.register(TitleCaseTool())
```

---

## 2) Attach Tools to an Agent

```python
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry

agent = AgentFactory.create_agent(
    id="formatter",
    role="Formatter",
    goal="Format text",
    tools=["title_case"],
)

runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
runtime.set_tools({"title_case": ToolRegistry.get("title_case")})
```

---

## 3) Create Tools via CLI

```bash
genxai tool create \
  --name my_tool \
  --description "My custom tool" \
  --category custom \
  --template api_call \
  --config '{"url": "https://api.example.com", "method": "GET"}'
```

---

## 4) Best Practices

1. **Validate Inputs** to prevent unsafe execution.
2. **Keep Tool Scope Narrow** for clarity and reuse.
3. **Describe Tools Clearly** so LLMs can choose them.
4. **Add Tags** for discovery and organization.

---

## 5) See Also

- `TOOLS_DESIGN.md` for full architecture
- `docs/CLI_USAGE.md` for CLI examples
