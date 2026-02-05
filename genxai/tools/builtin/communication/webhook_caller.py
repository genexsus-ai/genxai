"""Webhook caller tool for triggering webhooks."""

from typing import Any, Dict, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class WebhookCallerTool(Tool):
    """Call webhooks with custom payloads and headers."""

    def __init__(self) -> None:
        """Initialize webhook caller tool."""
        metadata = ToolMetadata(
            name="webhook_caller",
            description="Trigger webhooks with custom payloads and authentication",
            category=ToolCategory.COMMUNICATION,
            tags=["webhook", "http", "callback", "integration", "api"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="Webhook URL",
                pattern=r"^https?://",
                required=True,
            ),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                required=False,
                default="POST",
                enum=["GET", "POST", "PUT", "PATCH", "DELETE"],
            ),
            ToolParameter(
                name="payload",
                type="object",
                description="Webhook payload data",
                required=False,
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="Custom HTTP headers",
                required=False,
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="Request timeout in seconds",
                required=False,
                default=30,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        url: str,
        method: str = "POST",
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Execute webhook call.

        Args:
            url: Webhook URL
            method: HTTP method
            payload: Payload data
            headers: Custom headers
            timeout: Request timeout

        Returns:
            Dictionary containing webhook response
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx"
            )

        result: Dict[str, Any] = {
            "url": url,
            "method": method,
            "success": False,
        }

        try:
            # Prepare request
            request_kwargs: Dict[str, Any] = {
                "method": method,
                "url": url,
                "timeout": timeout,
            }

            if headers:
                request_kwargs["headers"] = headers

            if payload and method in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = payload

            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.request(**request_kwargs)

            # Parse response
            result.update({
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "response_headers": dict(response.headers),
            })

            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_text"] = response.text

        except httpx.HTTPStatusError as e:
            result["error"] = f"HTTP error: {e.response.status_code}"
            result["status_code"] = e.response.status_code
        except httpx.RequestError as e:
            result["error"] = f"Request error: {str(e)}"
        except Exception as e:
            result["error"] = str(e)

        logger.info(f"Webhook call completed: success={result['success']}")
        return result
