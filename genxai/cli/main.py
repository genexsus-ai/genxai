"""GenXAI CLI (OSS).

This is the OSS CLI entry point.

Enterprise distributions can inject additional commands by exposing entry points
in the `genxai.cli_plugins` group.
"""

from __future__ import annotations

import click

from genxai.cli.commands import tool, workflow


PLUGIN_ENTRYPOINT_GROUP = "genxai.cli_plugins"


@click.group()
@click.version_option(prog_name="genxai")
def cli() -> None:
    """GenXAI command line interface (OSS).

    Manage tools and run workflows from the command line.
    """


def _add_plugin_command(root: click.Group, plugin_obj) -> None:
    """Register commands from a plugin object.

    Supported plugin shapes:
    - click.Command / click.Group: registered directly.
    - callable returning a click.Command or iterable of click.Commands.
    """

    if isinstance(plugin_obj, click.core.BaseCommand):
        root.add_command(plugin_obj)
        return

    if callable(plugin_obj):
        resolved = plugin_obj()
        if isinstance(resolved, click.core.BaseCommand):
            root.add_command(resolved)
            return
        if resolved is None:
            return
        try:
            for cmd in resolved:
                if isinstance(cmd, click.core.BaseCommand):
                    root.add_command(cmd)
        except TypeError:
            # Not iterable; ignore.
            return


def load_plugins(root: click.Group) -> None:
    """Load CLI plugins registered via Python entry points."""

    try:
        from importlib import metadata
    except Exception:  # pragma: no cover
        return

    try:
        eps = metadata.entry_points()
        # Python 3.10+ supports .select
        candidates = eps.select(group=PLUGIN_ENTRYPOINT_GROUP)  # type: ignore[attr-defined]
    except Exception:
        try:
            candidates = metadata.entry_points().get(PLUGIN_ENTRYPOINT_GROUP, [])  # type: ignore[assignment]
        except Exception:
            candidates = []

    for ep in candidates:
        try:
            plugin_obj = ep.load()
        except Exception:
            # Plugin failed to load; do not hard-fail the core CLI.
            continue
        _add_plugin_command(root, plugin_obj)


# Register OSS command groups.
cli.add_command(tool)
cli.add_command(workflow)

# Load optional plugins.
load_plugins(cli)


def main() -> None:
    """Console script entry point."""

    cli()


if __name__ == "__main__":
    main()
