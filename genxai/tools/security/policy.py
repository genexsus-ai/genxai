"""Tool execution policy enforcement."""

from __future__ import annotations

from genxai.config import get_settings


def is_tool_allowed(tool_name: str) -> tuple[bool, str | None]:
    """Determine whether a tool can execute based on allow/deny lists."""
    settings = get_settings()
    allowlist = settings.allowlist_set()
    denylist = settings.denylist_set()

    if tool_name in denylist:
        return False, f"Tool '{tool_name}' is denied by policy"

    if allowlist and tool_name not in allowlist:
        return False, f"Tool '{tool_name}' is not in allowlist"

    return True, None