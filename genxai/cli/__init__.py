"""GenXAI OSS CLI.

This package provides the open-source command line interface.

Enterprise editions can extend the CLI by registering additional click command
groups via the `genxai.cli_plugins` entry-point group.
"""

from __future__ import annotations

__all__ = ["__version__"]

# CLI version is intentionally decoupled from the library version.
__version__ = "0.1.0"
