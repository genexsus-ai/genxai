"""Slack notifier tool for sending messages to Slack."""

from typing import Any, Dict, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class SlackNotifierTool(Tool):
    """Send notifications to Slack channels via webhook."""

    def __init__(self) -> None:
        """Initialize Slack notifier tool."""
        metadata = ToolMetadata(
            name="slack_notifier",
            description="Send messages and notifications to Slack channels",
            category=ToolCategory.COMMUNICATION,
            tags=["slack", "notification", "webhook", "messaging", "communication"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="webhook_url",
                type="string",
                description="Slack webhook URL",
                required=True,
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Message text to send",
                required=True,
            ),
            ToolParameter(
                name="username",
                type="string",
                description="Bot username to display",
                required=False,
            ),
            ToolParameter(
                name="icon_emoji",
                type="string",
                description="Emoji icon (e.g., ':robot_face:')",
                required=False,
            ),
            ToolParameter(
                name="channel",
                type="string",
                description="Channel to post to (overrides webhook default)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        webhook_url: str,
        message: str,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute Slack notification.

        Args:
            webhook_url: Slack webhook URL
            message: Message text
            username: Bot username
            icon_emoji: Icon emoji
            channel: Target channel

        Returns:
            Dictionary containing send results
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx"
            )

        result: Dict[str, Any] = {
            "message": message,
            "success": False,
        }

        try:
            # Build payload
            payload: Dict[str, Any] = {"text": message}
            
            if username:
                payload["username"] = username
            if icon_emoji:
                payload["icon_emoji"] = icon_emoji
            if channel:
                payload["channel"] = channel

            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()

            result.update({
                "success": True,
                "status_code": response.status_code,
            })

        except httpx.HTTPStatusError as e:
            result["error"] = f"HTTP error: {e.response.status_code}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Slack notification completed: success={result['success']}")
        return result
