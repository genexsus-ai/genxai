# LLM Integration Guide

**Status:** ✅ Implemented  
**Version:** 1.0.0  
**Last Updated:** January 30, 2026

---

## Overview

GenXAI now has **full LLM integration** with agents! Agents can now call real LLM providers (starting with OpenAI) to generate intelligent responses.

### What's New

✅ **LLM Provider Factory** - Automatically creates and manages LLM providers  
✅ **Agent Runtime Integration** - Agents now call real LLMs instead of placeholders  
✅ **Enhanced Prompt Building** - System prompts with agent personality and type  
✅ **Token Tracking** - Automatic tracking of token usage per agent  
✅ **Error Handling** - Graceful fallbacks and clear error messages  
✅ **Multiple Models** - Support for GPT-4, GPT-3.5-turbo, and more  
✅ **Schema-Based Tool Calling** - OpenAI function calling with tool schemas

---

## Quick Start

### 1. Set Your API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 2. Create an Agent with LLM

```python
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

# Create agent
agent = AgentFactory.create_agent(
    id="assistant",
    role="Helpful Assistant",
    goal="Answer questions accurately",
    llm_model="gpt-3.5-turbo",
    temperature=0.7,
)

# Create runtime (automatically connects to LLM)
runtime = AgentRuntime(agent=agent)

# Execute task
result = await runtime.execute(
    task="What is the capital of France?"
)

print(result['output'])  # Real LLM response!
```

---

## Features

### Automatic Provider Creation

The `AgentRuntime` automatically creates an LLM provider based on the agent's configuration:

```python
# Agent config specifies the model
agent = AgentFactory.create_agent(
    id="my_agent",
    role="Assistant",
    goal="Help users",
    llm_model="gpt-4",  # Provider created automatically
    temperature=0.8,
    llm_max_tokens=1000,
)

# Runtime creates OpenAI provider automatically
runtime = AgentRuntime(agent=agent)
```

### Manual Provider Creation

You can also create providers manually:

```python
from genxai.llm.factory import LLMProviderFactory

# Create provider
provider = LLMProviderFactory.create_provider(
    model="gpt-4",
    api_key="your-key",
    temperature=0.7,
    max_tokens=2000,
)

# Use with agent
runtime = AgentRuntime(agent=agent, llm_provider=provider)
```

### Supported Models

#### OpenAI
- `gpt-4` - Most capable model
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-4o` - Optimized GPT-4
- `gpt-3.5-turbo` - Fast and cost-effective
- Any model starting with `gpt-`

#### Anthropic Claude ✨ NEW
- `claude-3-opus-20240229` - Most capable Claude model
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240229` - Fast and efficient
- Any model starting with `claude-`

#### Google Gemini ✨ NEW
- `gemini-pro` - Versatile model for text
- `gemini-pro-vision` - Multi-modal (text + images)
- `gemini-ultra` - Most capable (when available)
- Any model starting with `gemini-`

#### Cohere ✨ NEW
- `command` - General purpose model
- `command-light` - Faster variant
- `command-r` - Retrieval-optimized
- `command-r-plus` - Enhanced retrieval
- Any model starting with `command-`

Coming soon:
- LM Studio integration
- Azure OpenAI
- AWS Bedrock

### Provider Comparison

| Provider | Strengths | Best For | Cost | Speed |
|----------|-----------|----------|------|-------|
| **OpenAI** | Most popular, reliable | General purpose, coding | $$$ | Fast |
| **Anthropic** | Long context, safety | Analysis, research | $$$ | Medium |
| **Google** | Multi-modal, free tier | Vision tasks, prototyping | $$ | Fast |
| **Cohere** | Retrieval, embeddings | Search, RAG applications | $$ | Fast |
| **Ollama** | Local models, offline | Private/on-prem | $ | Fast |

### Using Different Providers

#### Anthropic Claude Example

```python
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

# Create agent with Claude
agent = AgentFactory.create_agent(
    id="analyst",
    role="Data Analyst",
    goal="Analyze complex datasets",
    llm_model="claude-3-opus-20240229",  # Use Claude Opus
    temperature=0.7,
)

# Set API key
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

# Execute
runtime = AgentRuntime(agent=agent)
result = await runtime.execute(
    task="Analyze this sales data and provide insights"
)
```

#### Google Gemini Example

```python
# Create agent with Gemini
agent = AgentFactory.create_agent(
    id="vision_agent",
    role="Image Analyzer",
    goal="Describe and analyze images",
    llm_model="gemini-pro-vision",  # Multi-modal model
    temperature=0.5,
)

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIza..."

runtime = AgentRuntime(agent=agent)
result = await runtime.execute(
    task="Describe what you see in this image"
)
```

#### Cohere Example

```python
# Create agent with Cohere
agent = AgentFactory.create_agent(
    id="search_agent",
    role="Search Assistant",
    goal="Find and summarize information",
    llm_model="command-r-plus",  # Retrieval-optimized
    temperature=0.6,
)

# Set API key
os.environ["COHERE_API_KEY"] = "..."

runtime = AgentRuntime(agent=agent)
result = await runtime.execute(
    task="Search for recent AI developments"
)
```

#### Ollama (Local) Example

```python
# Create agent with Ollama (local)
agent = AgentFactory.create_agent(
    id="local_agent",
    role="Local Analyst",
    goal="Process requests locally",
    llm_model="llama3",  # Ollama model name
    temperature=0.6,
)

# Optional: customize Ollama base URL
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

runtime = AgentRuntime(agent=agent)
result = await runtime.execute(
    task="Summarize this report in 3 bullets."
)
```

#### Provider Fallback

```python
from genxai.llm.factory import LLMProviderFactory

# Create provider with fallback
provider = LLMProviderFactory.create_provider(
    model="gpt-4",
    fallback_models=["claude-3-opus-20240229", "gemini-pro"],
    temperature=0.7,
)

# If GPT-4 fails, automatically tries Claude, then Gemini
```

### Agent Types & System Prompts

Different agent types get specialized system prompts:

```python
# Deliberative agent - thinks before acting
agent = AgentFactory.create_agent(
    id="planner",
    role="Strategic Planner",
    goal="Create detailed plans",
    agent_type="deliberative",  # Adds planning instructions
)

# Learning agent - improves over time
agent = AgentFactory.create_agent(
    id="learner",
    role="Student",
    goal="Learn from feedback",
    agent_type="learning",  # Adds learning instructions
)

# Collaborative agent - works with others
agent = AgentFactory.create_agent(
    id="team_member",
    role="Team Member",
    goal="Coordinate with team",
    agent_type="collaborative",  # Adds collaboration instructions
)
```

### Personality & Backstory

Give agents unique personalities:

```python
agent = AgentFactory.create_agent(
    id="pirate",
    role="Pirate Captain",
    goal="Speak like a pirate",
    backstory="You are Captain Blackbeard, a legendary pirate.",
    temperature=0.9,  # Higher for more creative responses
)
```

### Token Tracking

Token usage is automatically tracked:

```python
result = await runtime.execute(task="Hello!")

# Check token usage
print(f"Tokens used: {agent._total_tokens}")
print(f"This request: {result['output']}")
```

### Batch Execution

Execute multiple tasks in parallel:

```python
tasks = [
    "What is 2 + 2?",
    "What is the capital of Spain?",
    "Who wrote Hamlet?",
]

results = await runtime.batch_execute(tasks)

for task, result in zip(tasks, results):
    print(f"Q: {task}")
    print(f"A: {result['output']}\n")
```

---

## Schema-Based Tool Calling (OpenAI)

GenXAI can pass tool schemas directly to OpenAI models that support function
calling. This avoids brittle regex parsing and lets models call tools via the
native tool calling API.

```python
import os
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - auto-register tools

agent = AgentFactory.create_agent(
    id="tool_agent",
    role="Math Helper",
    goal="Use tools when needed",
    tools=["calculator"],
    llm_model="gpt-4",
)

runtime = AgentRuntime(agent=agent, api_key=os.getenv("OPENAI_API_KEY"))
tools = {tool.metadata.name: tool for tool in ToolRegistry.list_all()}
runtime.set_tools(tools)

result = await runtime.execute(
    task="Use the calculator tool to compute 42 * 7."
)
print(result["output"])
```

## API Reference

### LLMProviderFactory

```python
class LLMProviderFactory:
    @classmethod
    def create_provider(
        cls,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        fallback_models: Optional[list[str]] = None,
        **kwargs
    ) -> LLMProvider
```

**Methods:**
- `create_provider()` - Create an LLM provider instance
- `supports_model(model)` - Check if a model is supported
- `list_available_providers()` - List all available providers
- `register_provider(name, class)` - Register a custom provider

### AgentRuntime

```python
class AgentRuntime:
    def __init__(
        self,
        agent: Agent,
        llm_provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
    )
```

**Methods:**
- `execute(task, context, timeout)` - Execute a single task
- `batch_execute(tasks, context)` - Execute multiple tasks in parallel
- `set_llm_provider(provider)` - Set/change LLM provider
- `set_tools(tools)` - Set available tools
- `set_memory(memory)` - Set memory system

---

## Configuration

### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GOOGLE_API_KEY="AIza..."

# Cohere
export COHERE_API_KEY="..."

# Ollama (optional)
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_API_KEY=""  # Usually not needed
```

### Getting API Keys

#### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and save securely

#### Anthropic
1. Visit https://console.anthropic.com/
2. Go to API Keys section
3. Create new key

#### Google (Gemini)
1. Visit https://makersuite.google.com/app/apikey
2. Create API key
3. Enable Generative AI API

#### Cohere
1. Visit https://dashboard.cohere.com/api-keys
2. Create new API key
3. Choose appropriate tier

### Agent Configuration

```python
agent = AgentFactory.create_agent(
    id="my_agent",
    role="Assistant",
    goal="Help users",
    backstory="Optional background story",
    
    # LLM settings
    llm_model="gpt-3.5-turbo",
    llm_temperature=0.7,
    llm_max_tokens=1000,
    
    # Agent behavior
    agent_type="reactive",  # reactive, deliberative, learning, collaborative
    max_iterations=10,
    verbose=True,
    
    # Guardrails
    max_execution_time=30.0,  # seconds
)
```

---

## Examples

### Example 1: Multi-Provider Comparison

```python
"""Compare responses from different providers."""

import asyncio
from genxai.core.agent.base import AgentFactory
from genxai.core.agent.runtime import AgentRuntime

async def compare_providers():
    """Compare same task across providers."""
    
    task = "Explain quantum computing in simple terms"
    
    # Test with different providers
    models = [
        "gpt-4",
        "claude-3-opus-20240229",
        "gemini-pro",
        "command-r-plus",
    ]
    
    for model in models:
        agent = AgentFactory.create_agent(
            id=f"agent_{model}",
            role="Science Explainer",
            goal="Explain complex topics simply",
            llm_model=model,
        )
        
        runtime = AgentRuntime(agent=agent)
        result = await runtime.execute(task=task)
        
        print(f"\n{'='*60}")
        print(f"Provider: {model}")
        print(f"{'='*60}")
        print(result['output'])
        print(f"Tokens: {agent._total_tokens}")

asyncio.run(compare_providers())
```

### Example 2: Provider-Specific Features

```python
"""Use provider-specific features."""

# Claude: Long context analysis
agent = AgentFactory.create_agent(
    id="claude_analyst",
    role="Document Analyzer",
    goal="Analyze long documents",
    llm_model="claude-3-opus-20240229",
    llm_max_tokens=4096,  # Claude supports long outputs
)

# Gemini: Multi-modal
agent = AgentFactory.create_agent(
    id="gemini_vision",
    role="Image Analyzer",
    goal="Analyze images",
    llm_model="gemini-pro-vision",
)

# Cohere: Retrieval-optimized
agent = AgentFactory.create_agent(
    id="cohere_search",
    role="Search Agent",
    goal="Find relevant information",
    llm_model="command-r-plus",
)
```

### Example 3: Cost Optimization

```python
"""Use cheaper models for simple tasks."""

# Simple tasks: Use GPT-3.5 or Command-Light
simple_agent = AgentFactory.create_agent(
    id="simple",
    role="Assistant",
    goal="Answer simple questions",
    llm_model="gpt-3.5-turbo",  # Cheaper
)

# Complex tasks: Use GPT-4 or Claude Opus
complex_agent = AgentFactory.create_agent(
    id="complex",
    role="Analyst",
    goal="Deep analysis",
    llm_model="claude-3-opus-20240229",  # More capable
)
```

See `examples/code/llm_agent_example.py` for complete examples:

1. **Simple Agent** - Basic question answering
2. **Agent with Personality** - Pirate captain with backstory
3. **Deliberative Agent** - Strategic planner
4. **Batch Execution** - Multiple tasks in parallel
5. **Agent with Context** - Customer service with conversation history

Run examples:
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  # Optional
export GOOGLE_API_KEY="your-key"     # Optional
export COHERE_API_KEY="your-key"     # Optional

python examples/code/llm_agent_example.py
```

---

## Testing

### Unit Tests

```bash
# Test LLM factory
pytest tests/unit/test_llm_factory.py -v
```

### Integration Tests

```bash
# Test with real OpenAI API (requires API key)
export OPENAI_API_KEY="your-key"
pytest tests/integration/test_llm_integration.py -v
```

---

## Error Handling

### No API Key

```python
# Without API key, agent will raise RuntimeError
try:
    result = await runtime.execute(task="Hello")
except RuntimeError as e:
    print(f"Error: {e}")
    # Error: Agent my_agent has no LLM provider. 
    # Provide an API key or set OPENAI_API_KEY environment variable.
```

### API Failures

```python
# LLM calls are wrapped with error handling
try:
    result = await runtime.execute(task="Hello")
except RuntimeError as e:
    print(f"LLM call failed: {e}")
```

### Fallback Models

```python
# Specify fallback models
provider = LLMProviderFactory.create_provider(
    model="gpt-4",
    fallback_models=["gpt-3.5-turbo"],  # Falls back if gpt-4 fails
)
```

---

## Performance

### Response Times

Typical response times (excluding LLM latency):
- Agent initialization: < 10ms
- Prompt building: < 5ms
- Token tracking: < 1ms
- Total overhead: < 20ms

### Token Usage

Monitor token usage to control costs:

```python
# Before
initial_tokens = agent._total_tokens

# Execute
result = await runtime.execute(task="Long task...")

# After
tokens_used = agent._total_tokens - initial_tokens
print(f"This task used {tokens_used} tokens")
```

---

## Best Practices

### 1. Use Appropriate Models

```python
# For simple tasks - faster and cheaper
agent.config.llm_model = "gpt-3.5-turbo"

# For complex reasoning - more capable
agent.config.llm_model = "gpt-4"
```

### 2. Adjust Temperature

```python
# For factual/consistent responses
agent.config.llm_temperature = 0.3

# For creative responses
agent.config.llm_temperature = 0.9
```

### 3. Set Token Limits

```python
# Prevent runaway costs
agent.config.llm_max_tokens = 500
```

### 4. Use Timeouts

```python
# Prevent hanging
agent.config.max_execution_time = 30.0  # seconds
```

### 5. Batch When Possible

```python
# More efficient than sequential
results = await runtime.batch_execute(tasks)
```

---

## Troubleshooting

### "No LLM provider available"

**Cause:** API key not set  
**Solution:** Set appropriate environment variable:
- OpenAI: `OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- Google: `GOOGLE_API_KEY`
- Cohere: `COHERE_API_KEY`

### "No provider found for model"

**Cause:** Unsupported model name  
**Solution:** Use supported models:
- OpenAI: `gpt-4`, `gpt-3.5-turbo`, etc.
- Anthropic: `claude-3-opus-20240229`, etc.
- Google: `gemini-pro`, etc.
- Cohere: `command`, `command-r`, etc.

### "Package not installed"

**Cause:** Provider package not installed  
**Solution:** Install required packages:
```bash
# Install all LLM providers
pip install genxai[llm]

# Or install individually
pip install anthropic
pip install google-generativeai
pip install cohere
```

### "LLM call failed"

**Cause:** API error (rate limit, invalid key, etc.)  
**Solution:** Check API key, rate limits, and OpenAI status

### Slow responses

**Cause:** LLM latency  
**Solution:** Use faster models (gpt-3.5-turbo), reduce max_tokens, or implement caching

---

## Roadmap

### ✅ Completed

- [x] **OpenAI** - GPT-4, GPT-3.5-turbo
- [x] **Anthropic Claude** - Claude 3 Opus, Sonnet, Haiku
- [x] **Google Gemini** - Gemini Pro, Ultra, Vision
- [x] **Cohere** - Command, Command-R, Command-R-Plus
- [x] **Ollama** - Local models (llama3, mistral, phi3)
- [x] **Provider Factory** - Automatic provider selection
- [x] **Lazy Loading** - Efficient provider initialization

### Coming Soon

- [ ] **LM Studio** - Local model integration
- [ ] **Azure OpenAI** - Enterprise OpenAI deployment
- [ ] **AWS Bedrock** - Claude, Llama via AWS
- [ ] **Response Caching** - Cache LLM responses for repeated queries
- [ ] **Streaming UI** - Real-time streaming in Studio
- [x] **Function Calling** - Native tool use with OpenAI function calling
- [ ] **Cost Tracking** - Detailed cost analysis per agent/task
- [ ] **Rate Limiting** - Automatic rate limit handling
- [ ] **Retry Logic** - Exponential backoff for failures

---

## Migration Guide

### From Placeholder to Real LLM

**Before (Placeholder):**
```python
runtime = AgentRuntime(agent=agent)
result = await runtime.execute(task="Hello")
# Output: "[Placeholder LLM response for: Hello...]"
```

**After (Real LLM):**
```python
# Just set OPENAI_API_KEY!
export OPENAI_API_KEY="sk-..."

runtime = AgentRuntime(agent=agent)
result = await runtime.execute(task="Hello")
# Output: "Hello! How can I assist you today?"
```

No code changes required! Just set your API key and agents automatically use real LLMs.

---

## Contributing

Want to add support for more LLM providers?

1. Create a new provider class in `genxai/llm/providers/`
2. Inherit from `LLMProvider` base class
3. Implement `generate()` and `generate_stream()` methods
4. Register with `LLMProviderFactory`
5. Add tests

See `genxai/llm/providers/openai.py` for reference implementation.

---

## Support

- **Documentation:** [docs/](../docs/)
- **Examples:** [examples/code/](../examples/code/)
- **Issues:** GitHub Issues
- **Discord:** (Coming soon)

---

## Provider Installation

### Quick Install (All Providers)

```bash
pip install genxai[llm]
```

### Individual Providers

```bash
# OpenAI only
pip install openai

# Anthropic only
pip install anthropic

# Google only
pip install google-generativeai

# Cohere only
pip install cohere

# Ollama (local HTTP client)
pip install httpx
```

---

## Best Practices

### 1. Choose the Right Provider

```python
# For coding tasks
llm_model="gpt-4"  # Best for code generation

# For long documents
llm_model="claude-3-opus-20240229"  # 200K context window

# For vision tasks
llm_model="gemini-pro-vision"  # Multi-modal

# For search/RAG
llm_model="command-r-plus"  # Retrieval-optimized
```

### 2. Use Environment Variables

```python
# Don't hardcode API keys!
# ❌ Bad
agent.config.llm_api_key = "sk-..."

# ✅ Good
import os
os.environ["OPENAI_API_KEY"] = "sk-..."
```

### 3. Implement Fallbacks

```python
# Always have a backup
provider = LLMProviderFactory.create_provider(
    model="gpt-4",
    fallback_models=["claude-3-opus-20240229", "gemini-pro"],
)
```

### 4. Monitor Costs

```python
# Track token usage
print(f"Tokens used: {agent._total_tokens}")

# Set limits
agent.config.llm_max_tokens = 500  # Prevent runaway costs
```

### 5. Test with Cheaper Models First

```python
# Development: Use cheaper models
if os.getenv("ENV") == "development":
    llm_model = "gpt-3.5-turbo"
else:
    llm_model = "gpt-4"
```

---

**Status:** ✅ **PRODUCTION READY**

GenXAI now supports **5 major LLM providers** with **15+ models**! 🚀

**Multi-Provider Support:**
- ✅ OpenAI (GPT-4, GPT-3.5-turbo)
- ✅ Anthropic (Claude 3 Opus, Sonnet, Haiku)
- ✅ Google (Gemini Pro, Ultra, Vision)
- ✅ Cohere (Command, Command-R, Command-R-Plus)
- ✅ **Ollama** - Local models (llama3, mistral, phi3)
