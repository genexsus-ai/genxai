"""GenXAI API package.

This package contains lightweight API entrypoints intended to be usable from the
OSS distribution. Enterprise deployments may provide additional endpoints and/or
implementations.
"""

from genxai.api.app import create_app

__all__ = ["create_app"]
