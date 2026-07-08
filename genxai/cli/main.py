"""GenXAI CLI entry point.

Console script: `genxai` -> `genxai.cli.main:main`

Provides the `tool`, `workflow`, `connector`, `metrics`, `approval`, and
`audit` command groups. Additional command groups can be attached via the
`genxai.cli_plugins` entry-point group.
"""

import click

from genxai import __version__
from genxai.cli.commands import connector, metrics, tool, workflow
from genxai.cli.commands.approval import approval
from genxai.cli.commands.audit import audit


@click.group()
@click.version_option(version=__version__, prog_name='genxai')
def cli():
    """GenXAI - Multi-Agent AI Framework CLI.
    
    Manage tools, agents, workflows, and more from the command line.
    """
    pass


# Register command groups
cli.add_command(tool)
cli.add_command(metrics)
cli.add_command(connector)
cli.add_command(workflow)
cli.add_command(approval)
cli.add_command(audit)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()
