# GenXAI CLI - Tool Management (Enterprise)

The GenXAI CLI is part of the enterprise edition and lives under `enterprise/`.

## Installation

```bash
# Install GenXAI (core only)
pip install -e .

# Or install from PyPI (when published)
pip install genxai

# Full install with providers/tools/API (core)
pip install "genxai[llm,tools,api]"

# Everything included
pip install "genxai[all]"
```

## Tool Management Commands

### List Tools

List all available tools:

```bash
genxai tool list
```

### Run a Workflow (YAML)

```bash
genxai workflow run examples/nocode/content_generation.yaml \
  --input '{"topic": "AI workflow design"}'
```

Filter by category:

```bash
genxai tool list --category web
```

Output as JSON:

```bash
genxai tool list --format json
```

### Get Tool Information

Show detailed information about a specific tool:

```bash
genxai tool info <tool_name>
```

Example:

```bash
genxai tool info weather_api
```

### Search Tools

Search tools by name, description, or tags:

```bash
genxai tool search <query>
```

Examples:

```bash
genxai tool search weather
genxai tool search api --category web
```

### Create Tool

Create a new tool from a template:

```bash
genxai tool create \
  --name my_tool \
  --description "My custom tool" \
  --category custom \
  --template api_call \
  --config '{"url": "https://api.example.com", "method": "GET"}' \
  --tags api,custom
```

Create a tool from a Python file:

```bash
genxai tool create \
  --name my_code_tool \
  --description "Tool from code" \
  --category custom \
  --code-file ./my_tool.py \
  --tags custom
```

### Delete Tool

Delete a tool (with confirmation):

```bash
genxai tool delete <tool_name>
```

Skip confirmation:

```bash
genxai tool delete <tool_name> --force
```

### Export Tool

Export a tool to a file:

```bash
# Export as JSON (default)
genxai tool export <tool_name>

# Export to specific file
genxai tool export <tool_name> --output ./backup/tool.json

# Export as Python file (code-based tools only)
genxai tool export <tool_name> --format py --output ./tool.py
```

### Export Tool Schema Bundle

```bash
# Export all schemas to a file (JSON)
genxai tool export-schema --output tool_schemas.json
# Output includes schema bundle version

# Export all schemas to YAML
genxai tool export-schema --format yaml --output tool_schemas.yaml

# Export only web tool schemas
genxai tool export-schema --category web --output web_tool_schemas.json

# Print schemas to stdout (JSON default)
genxai tool export-schema --stdout

# Print schemas to stdout as YAML
genxai tool export-schema --stdout --format yaml
```

### Import Tool

Import a tool from a JSON file:

```bash
genxai tool import-tool ./tool.json
```

## Metrics API Commands

Start the metrics API server (non-Studio) to expose Prometheus metrics:

```bash
Enterprise metrics command (enterprise repo):
genxai metrics serve --host 0.0.0.0 --port 8001
```

Enable auto-reload during development:

```bash
genxai metrics serve --reload
```

## Connector Commands

List available connector types:

```bash
genxai connector list
```

Output connector catalog as JSON:

```bash
genxai connector list --format json
```

Validate connector configuration:

```bash
genxai connector validate \
  --type slack \
  --connector-id slack_alerts \
  --config '{"bot_token": "xoxb-token"}'
```

Example validations for other connectors:

```bash
genxai connector validate --type github --config '{"token": "ghp_xxx"}'
genxai connector validate --type jira --config '{"email": "you@company.com", "api_token": "token", "base_url": "https://your-domain.atlassian.net"}'
genxai connector validate --type google_workspace --config '{"access_token": "ya29.x"}'
```

Save and reuse connector configs:

```bash
genxai connector save --name slack_alerts --type slack --config '{"bot_token": "xoxb-token"}'
genxai connector saved
genxai connector validate --type slack --config-name slack_alerts
genxai connector start --type slack --config-name slack_alerts
genxai connector health --type slack --config-name slack_alerts
genxai connector remove --name slack_alerts
```

Enable encrypted connector configs (optional):

```bash
# Generate a Fernet key (requires cryptography)
genxai connector keygen

# Export the key before saving connector configs
export GENXAI_CONNECTOR_CONFIG_KEY="your-generated-key"

# Saved configs will now be encrypted at rest
genxai connector save --name slack_alerts --type slack --config '{"bot_token": "xoxb-token"}'
```

Start/stop a connector instance (for quick validation):

```bash
genxai connector start --type slack --config '{"bot_token": "xoxb-token"}'
genxai connector stop --type slack --config '{"bot_token": "xoxb-token"}'
```

Run a connector health check:

```bash
genxai connector health --type slack --config '{"bot_token": "xoxb-token"}'
genxai connector health --type slack --format table --config '{"bot_token": "xoxb-token"}'
```

## Approval Commands

Manage pending approvals for policy-gated operations:

```bash
# List all pending approvals
genxai approval list

# Approve a specific request
genxai approval approve <request_id>

# Reject a specific request
genxai approval reject <request_id> --reason "Security concern"
```

## Audit Commands

Query and export audit logs:

```bash
# List recent audit events
genxai audit list --limit 50

# Filter by user
genxai audit list --user alice

# Filter by resource type
genxai audit list --resource-type tool

# Export audit logs to JSON
genxai audit export --output audit_logs.json --start-date 2026-01-01
```

## Tool Categories

Valid tool categories:

- `web` - Web scraping, API calls, HTTP requests
- `file` - File operations, reading, writing
- `computation` - Mathematical calculations, data processing
- `database` - Database queries and operations
- `communication` - Email, messaging, notifications
- `custom` - User-defined custom tools

## Examples

### Workflow: Backup All Tools

```bash
# Create backup directory
mkdir -p ./tool_backups/$(date +%Y%m%d)

# Export all tools
for tool in $(genxai tool list --format json | jq -r '.[].name'); do
  genxai tool export "$tool" --output "./tool_backups/$(date +%Y%m%d)/$tool.json"
done
```

### Workflow: Bulk Import Tools

```bash
# Import all tools from a directory
for file in ./tools/*.json; do
  genxai tool import-tool "$file"
done
```

### Workflow: List Tools by Category

```bash
# List all web tools
genxai tool list --category web

# Count tools by category
for cat in web file computation database communication custom; do
  count=$(genxai tool list --category $cat --format json | jq length)
  echo "$cat: $count tools"
done
```

## Integration with Scripts

### Shell Script Example

```bash
#!/bin/bash

# Check if tool exists before using it
if genxai tool info weather_api &>/dev/null; then
  echo "Weather API tool is available"
else
  echo "Creating weather API tool..."
  genxai tool create \
    --name weather_api \
    --description "Weather API integration" \
    --category web \
    --template api_call \
    --config '{"url": "https://api.weather.com", "method": "GET"}'
fi
```

### Python Script Example

```python
import subprocess
import json

# List all tools programmatically
result = subprocess.run(
    ['genxai', 'tool', 'list', '--format', 'json'],
    capture_output=True,
    text=True
)

tools = json.loads(result.stdout)
print(f"Total tools: {len(tools)}")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Tools

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install GenXAI
        run: pip install genxai
      
      - name: Configure encrypted connector configs (optional)
        env:
          GENXAI_CONNECTOR_CONFIG_KEY: ${{ secrets.GENXAI_CONNECTOR_CONFIG_KEY }}
        run: |
          echo "Connector configs will be encrypted at rest"

      - name: Deploy Tools
        run: |
          for file in tools/*.json; do
            genxai tool import-tool "$file"
          done
```

## Troubleshooting

### Tool Not Found

If you get "Tool not found" errors, make sure:

1. The tool exists: `genxai tool list`
2. The tool name is correct (case-sensitive)
3. The database is accessible at `genxai/data/tools.db`

### Import Errors

If tool import fails:

1. Validate the JSON file format
2. Check that the tool doesn't already exist
3. Ensure all required fields are present

### Schema Export Errors

- **Invalid category**: run `genxai tool export-schema --category <category>` using a valid category value.
- **YAML export requires PyYAML**: install with `pip install PyYAML` when using `--format yaml`.

### Permission Errors

If you get permission errors:

1. Check file permissions on `genxai/data/tools.db`
2. Ensure you have write access to the GenXAI directory
3. Try running with appropriate permissions

## Getting Help

Get help for any command:

```bash
genxai --help
genxai tool --help
genxai tool create --help
```

## See Also

- [Tool Creation Guide](./TOOL_CREATION.md)
- [GenXAI Studio](../studio/README.md)
- [API Documentation](./API.md)
