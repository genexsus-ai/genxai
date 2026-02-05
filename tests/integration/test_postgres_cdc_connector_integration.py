"""Enterprise-only Postgres CDC connector tests are excluded from OSS builds."""

import pytest


pytest.skip("Enterprise Postgres CDC connector not available in OSS build.", allow_module_level=True)