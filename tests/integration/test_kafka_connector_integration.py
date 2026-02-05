"""Enterprise-only Kafka connector tests are excluded from OSS builds."""

import pytest


pytest.skip("Enterprise Kafka connector not available in OSS build.", allow_module_level=True)