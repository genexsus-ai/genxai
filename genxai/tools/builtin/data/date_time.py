"""Date & Time tool: parse, format, and shift datetimes (n8n-style)."""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)

OPERATIONS = ["format", "now", "add", "subtract", "diff"]
UNITS = {
    "seconds": 1,
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
    "weeks": 604800,
}
# Friendly output presets -> strftime; anything else is treated as a strftime string.
PRESETS = {
    "iso": None,  # ISO-8601
    "date": "%Y-%m-%d",
    "time": "%H:%M",
    "datetime": "%Y-%m-%d %H:%M",
    "us": "%m/%d/%Y",
    "human": "%B %-d, %Y",  # July 21, 2026
}


class DateTimeTool(Tool):
    """Parse a date/time and format it, shift it, or diff two of them."""

    def __init__(self) -> None:
        metadata = ToolMetadata(
            name="date_time",
            description="Format, add/subtract, or diff dates and times",
            category=ToolCategory.DATA,
            tags=["date", "time", "format", "datetime"],
            version="1.0.0",
        )
        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="What to do",
                required=False,
                enum=OPERATIONS,
            ),
            ToolParameter(
                name="value",
                type="string",
                description="Input date/time (ISO-8601 or common formats). Omit for 'now'.",
                required=False,
            ),
            ToolParameter(
                name="format",
                type="string",
                description="Output format: a preset (iso, date, time, datetime, us, human) or a strftime string",
                required=False,
            ),
            ToolParameter(
                name="amount",
                type="number",
                description="How much to add/subtract (for add/subtract)",
                required=False,
            ),
            ToolParameter(
                name="unit",
                type="string",
                description="Unit for add/subtract",
                required=False,
                enum=list(UNITS),
            ),
            ToolParameter(
                name="to",
                type="string",
                description="Second date/time (for diff)",
                required=False,
            ),
        ]
        super().__init__(metadata, parameters)

    async def _execute(
        self,
        operation: str = "format",
        value: Optional[str] = None,
        format: Optional[str] = None,  # noqa: A002 - matches n8n's param name
        amount: Optional[float] = None,
        unit: str = "days",
        to: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            if operation == "now":
                dt = datetime.now(timezone.utc).astimezone()
            else:
                dt = _parse(value)

            if operation == "diff":
                other = _parse(to)
                seconds = abs((dt - other).total_seconds())
                return {
                    "success": True,
                    "seconds": seconds,
                    "minutes": round(seconds / 60, 2),
                    "hours": round(seconds / 3600, 2),
                    "days": round(seconds / 86400, 2),
                }

            if operation in ("add", "subtract"):
                if amount is None:
                    return {"success": False, "error": "amount is required for add/subtract"}
                delta = timedelta(seconds=float(amount) * UNITS.get(unit, 86400))
                dt = dt + delta if operation == "add" else dt - delta

            return {
                "success": True,
                "result": _format(dt, format),
                "iso": dt.isoformat(),
            }
        except (ValueError, TypeError) as exc:
            return {"success": False, "error": str(exc)}


def _parse(value: Optional[str]) -> datetime:
    if value is None or str(value).strip() == "":
        raise ValueError("a date/time value is required")
    text = str(value).strip()
    # ISO-8601 first (handles "2026-07-21T02:43:53+00:00", trailing Z)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Could not parse date/time: {value!r}")


def _format(dt: datetime, fmt: Optional[str]) -> str:
    if not fmt or fmt == "iso":
        return dt.isoformat()
    pattern = PRESETS.get(fmt, fmt)
    if pattern is None:
        return dt.isoformat()
    try:
        return dt.strftime(pattern)
    except ValueError:
        # %-d isn't portable on every platform; fall back without the dash flag
        return dt.strftime(pattern.replace("%-", "%"))
