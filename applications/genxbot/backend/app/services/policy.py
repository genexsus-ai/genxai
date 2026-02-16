"""Safety and approval policy helpers."""

from __future__ import annotations

from app.schemas import ProposedAction


class SafetyPolicy:
    """Very small policy engine for prototype approval gates."""

    SAFE_COMMAND_PREFIXES = (
        "pytest",
        "python -m pytest",
        "ruff check",
        "ruff format",
        "npm test",
        "npm run lint",
        "npm run build",
    )

    def is_safe_command(self, command: str) -> bool:
        cleaned = command.strip()
        return any(cleaned.startswith(prefix) for prefix in self.SAFE_COMMAND_PREFIXES)

    def requires_approval(self, action: ProposedAction) -> bool:
        if action.action_type == "edit":
            return True
        if action.action_type == "command":
            return not (action.command and self.is_safe_command(action.command))
        return True
