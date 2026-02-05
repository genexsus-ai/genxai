"""Enterprise-only SQS connector tests are excluded from OSS builds."""

import pytest


pytest.skip("Enterprise SQS connector not available in OSS build.", allow_module_level=True)