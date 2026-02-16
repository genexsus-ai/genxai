"""Enterprise CLI plugin for the OSS `genxai` CLI.

The OSS CLI (`genxai.cli.main`) loads optional command groups from the
`genxai.cli_plugins` entry-point group.

In the enterprise distribution (private repo), register this as:

```toml
[project.entry-points."genxai.cli_plugins"]
enterprise = "enterprise.cli.plugin:plugin_commands"
```
"""

from __future__ import annotations

from cli.commands.approval import approval
from cli.commands.audit import audit
from cli.commands.connector import connector
from cli.commands.metrics import metrics


def plugin_commands():
    """Return enterprise click command groups to attach to the OSS CLI."""

    return [metrics, connector, approval, audit]
