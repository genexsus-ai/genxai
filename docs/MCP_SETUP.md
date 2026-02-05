# GenXAI MCP Server Setup Guide

This guide explains how to set up and use the GenXAI MCP (Model Context Protocol) server to expose your custom tools to external applications like Claude Desktop, IDEs, and other AI systems.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to LLMs. It allows AI assistants to access tools, data sources, and other resources in a secure and standardized way.

## Features

- **Tool Discovery**: External applications can discover all GenXAI tools
- **Tool Execution**: Execute GenXAI tools from external applications
- **Schema Mapping**: Automatic conversion between GenXAI and MCP formats
- **Real-time Updates**: Tools created in GenXAI are immediately available via MCP

## Prerequisites

1. Python 3.8 or higher
2. GenXAI installed
3. MCP Python SDK installed:
   ```bash
   pip install mcp
   ```

## Installation

### 1. Install Dependencies

```bash
# Install MCP SDK and required packages
pip install mcp httpx aiofiles
```

### 2. Verify Installation

```bash
# Test the MCP server
python -m genxai.tools.mcp_server
```

## Configuration

### For Claude Desktop

1. **Locate Claude Desktop Config**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add GenXAI MCP Server**:
   ```json
   {
     "mcpServers": {
       "genxai-tools": {
         "command": "python",
         "args": ["-m", "genxai.tools.mcp_server"],
         "env": {
           "PYTHONPATH": "/path/to/GenXAI"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

### For Other Applications

Use the provided `mcp_config.json` as a template:

```json
{
  "mcpServers": {
    "genxai-tools": {
      "command": "python",
      "args": ["-m", "genxai.tools.mcp_server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Usage

### Creating Tools in GenXAI

1. **Via Web UI**:
   - Navigate to Tools page
   - Click "Create Tool"
   - Choose "Code Editor" or "From Template"
   - Fill in tool details and code
   - Click "Create Tool"

2. **Via Python Code**:
   ```python
   from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory
   from genxai.tools.registry import ToolRegistry
   
   # Create custom tool
   class MyCustomTool(Tool):
       def __init__(self):
           metadata = ToolMetadata(
               name="my_custom_tool",
               description="My custom tool",
               category=ToolCategory.CUSTOM,
               tags=["custom"]
           )
           parameters = [
               ToolParameter(
                   name="input",
                   type="string",
                   description="Input parameter",
                   required=True
               )
           ]
           super().__init__(metadata, parameters)
       
       async def _execute(self, input: str):
           return {"result": f"Processed: {input}"}
   
   # Register tool
   ToolRegistry.register(MyCustomTool())
   ```

### Using Tools via MCP

Once configured, tools are automatically available in Claude Desktop or other MCP-compatible applications:

1. **Tool Discovery**: Tools appear in the application's tool list
2. **Tool Execution**: Use natural language to invoke tools
3. **Results**: Tool results are returned and displayed

### Example Usage in Claude Desktop

```
User: "Use the calculator tool to compute 25 * 4 + 10"

Claude: [Uses calculator tool]
Result: 110

User: "Create a custom tool that reverses text"

[Navigate to GenXAI UI, create tool]

User: "Use the text_reverser tool to reverse 'Hello World'"

Claude: [Uses text_reverser tool]
Result: "dlroW olleH"
```

## Available Tool Templates

GenXAI provides several built-in templates:

1. **API Call Tool**: Make HTTP requests to external APIs
2. **Text Processor Tool**: Process and transform text
3. **Data Transformer Tool**: Convert between data formats (JSON, CSV, XML)
4. **File Processor Tool**: Read and write files

## Troubleshooting

### MCP Server Not Starting

**Issue**: Server fails to start
**Solution**: 
- Check Python path in config
- Verify MCP SDK is installed: `pip list | grep mcp`
- Check logs for errors

### Tools Not Appearing

**Issue**: Tools don't show up in Claude Desktop
**Solution**:
- Restart Claude Desktop
- Verify MCP server is running
- Check tool registration: `python -c "from genxai.tools.registry import ToolRegistry; print(ToolRegistry.list_all())"`

### Tool Execution Fails

**Issue**: Tool execution returns errors
**Solution**:
- Check tool code for syntax errors
- Verify all required parameters are provided
- Review tool logs for detailed error messages

## Security Considerations

1. **Code Execution**: Dynamic tools execute Python code - review code before creation
2. **API Access**: Tools can make external API calls - use appropriate authentication
3. **File Access**: File tools can read/write files - restrict paths as needed
4. **Network Access**: Some templates require network access - configure firewalls accordingly

## Advanced Configuration

### Custom Tool Registration

Register tools programmatically on server startup:

```python
# genxai/tools/mcp_server.py

async def main():
    # Register custom tools
    from my_tools import CustomTool1, CustomTool2
    
    ToolRegistry.register(CustomTool1())
    ToolRegistry.register(CustomTool2())
    
    # Start server
    server = GenXAIMCPServer()
    await server.run()
```

### Environment Variables

Configure server behavior via environment variables:

```bash
export GENXAI_LOG_LEVEL=DEBUG
export GENXAI_TOOL_TIMEOUT=60
python -m genxai.tools.mcp_server
```

### Multiple MCP Servers

Run multiple instances for different tool sets:

```json
{
  "mcpServers": {
    "genxai-production": {
      "command": "python",
      "args": ["-m", "genxai.tools.mcp_server"],
      "env": {
        "GENXAI_ENV": "production"
      }
    },
    "genxai-development": {
      "command": "python",
      "args": ["-m", "genxai.tools.mcp_server"],
      "env": {
        "GENXAI_ENV": "development"
      }
    }
  }
}
```

## API Reference

### GenXAIMCPServer

Main MCP server class.

**Methods**:
- `__init__(name: str)`: Initialize server
- `run()`: Start server
- `_convert_to_mcp_tool(tool: Tool)`: Convert GenXAI tool to MCP format
- `_format_tool_result(data: Any)`: Format tool results

### Tool Registry

Manage tool registration and discovery.

**Methods**:
- `register(tool: Tool)`: Register a tool
- `unregister(name: str)`: Unregister a tool
- `get(name: str)`: Get tool by name
- `list_all()`: List all tools
- `search(query: str, category: ToolCategory)`: Search tools

## Examples

### Example 1: Weather API Tool

```python
# Create via UI or code
name: "weather_api"
description: "Get weather information"
template: "api_call"
config:
  url: "https://api.weather.com/v1/current"
  method: "GET"
  headers: {"Authorization": "Bearer YOUR_API_KEY"}
```

### Example 2: Text Analysis Tool

```python
# Code-based tool
name: "text_analyzer"
description: "Analyze text statistics"
code: |
  text = params.get('text', '')
  
  result = {
      'word_count': len(text.split()),
      'char_count': len(text),
      'sentence_count': text.count('.') + text.count('!') + text.count('?'),
      'avg_word_length': sum(len(word) for word in text.split()) / len(text.split()) if text else 0
  }
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/irsal2012/GenXAI/issues
- Documentation: https://github.com/irsal2012/GenXAI
- MCP Specification: https://modelcontextprotocol.io

## License

GenXAI MCP Server is part of GenXAI and is licensed under the MIT License.
