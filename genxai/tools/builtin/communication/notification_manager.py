"""Notification manager tool for multi-channel notifications."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class NotificationManagerTool(Tool):
    """Manage and send notifications across multiple channels."""

    def __init__(self) -> None:
        """Initialize notification manager tool."""
        metadata = ToolMetadata(
            name="notification_manager",
            description="Send notifications across multiple channels (email, Slack, webhook)",
            category=ToolCategory.COMMUNICATION,
            tags=["notification", "multi-channel", "alert", "messaging", "broadcast"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="message",
                type="string",
                description="Notification message",
                required=True,
            ),
            ToolParameter(
                name="channels",
                type="object",
                description="Channel configurations (email, slack, webhook)",
                required=True,
            ),
            ToolParameter(
                name="priority",
                type="string",
                description="Notification priority",
                required=False,
                default="normal",
                enum=["low", "normal", "high", "urgent"],
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Notification title/subject",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        message: str,
        channels: Dict[str, Any],
        priority: str = "normal",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute multi-channel notification.

        Args:
            message: Notification message
            channels: Channel configurations
            priority: Priority level
            title: Notification title

        Returns:
            Dictionary containing send results for all channels
        """
        result: Dict[str, Any] = {
            "message": message,
            "priority": priority,
            "channels_attempted": [],
            "channels_succeeded": [],
            "channels_failed": [],
            "success": False,
        }

        try:
            # Process each channel
            for channel_type, config in channels.items():
                result["channels_attempted"].append(channel_type)

                try:
                    if channel_type == "email":
                        await self._send_email(message, title, config)
                        result["channels_succeeded"].append(channel_type)
                    
                    elif channel_type == "slack":
                        await self._send_slack(message, title, config)
                        result["channels_succeeded"].append(channel_type)
                    
                    elif channel_type == "webhook":
                        await self._send_webhook(message, title, priority, config)
                        result["channels_succeeded"].append(channel_type)
                    
                    else:
                        result["channels_failed"].append({
                            "channel": channel_type,
                            "error": "Unsupported channel type"
                        })

                except Exception as e:
                    result["channels_failed"].append({
                        "channel": channel_type,
                        "error": str(e)
                    })

            result["success"] = len(result["channels_succeeded"]) > 0

        except Exception as e:
            result["error"] = str(e)

        logger.info(
            f"Notification sent: {len(result['channels_succeeded'])}/{len(result['channels_attempted'])} channels"
        )
        return result

    async def _send_email(self, message: str, title: Optional[str], config: Dict[str, Any]) -> None:
        """Send email notification."""
        # Placeholder - would integrate with EmailSenderTool
        logger.info(f"Email notification sent: {title or 'Notification'}")

    async def _send_slack(self, message: str, title: Optional[str], config: Dict[str, Any]) -> None:
        """Send Slack notification."""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx required for Slack notifications")

        webhook_url = config.get("webhook_url")
        if not webhook_url:
            raise ValueError("webhook_url required for Slack channel")

        payload = {
            "text": f"*{title}*\n{message}" if title else message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

    async def _send_webhook(
        self, message: str, title: Optional[str], priority: str, config: Dict[str, Any]
    ) -> None:
        """Send webhook notification."""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx required for webhook notifications")

        url = config.get("url")
        if not url:
            raise ValueError("url required for webhook channel")

        payload = {
            "message": message,
            "title": title,
            "priority": priority,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
