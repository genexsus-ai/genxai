"""Async simulator tool for testing long-running operations and timeouts."""

from typing import Any
import asyncio
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory


class AsyncSimulatorTool(Tool):
    """Tool to simulate asynchronous operations and test timeout handling."""

    def __init__(self):
        """Initialize async simulator tool."""
        metadata = ToolMetadata(
            name="async_simulator",
            description="Simulate long-running async operations to test timeout and async handling",
            category=ToolCategory.SYSTEM,
            tags=["async", "timeout", "test", "simulator"],
            version="1.0.0",
            author="GenXAI",
        )

        parameters = [
            ToolParameter(
                name="duration",
                type="number",
                description="Duration to simulate in seconds",
                required=True,
                min_value=0,
                max_value=60,
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Message to return after completion",
                required=False,
                default="Operation completed",
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the async simulation.

        Args:
            **kwargs: Tool parameters (duration, message)

        Returns:
            Result after simulated delay
        """
        duration = kwargs.get("duration", 1)
        message = kwargs.get("message", "Operation completed")

        # Simulate async work
        await asyncio.sleep(duration)

        return {
            "duration": duration,
            "message": message,
            "status": "completed",
            "simulated": True,
        }
