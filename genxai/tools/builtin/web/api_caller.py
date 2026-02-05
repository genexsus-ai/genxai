"""API caller tool for making HTTP requests."""

from typing import Any, Dict, Optional
import logging
import json

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class APICallerTool(Tool):
    """Make HTTP API calls with authentication support."""

    def __init__(self) -> None:
        """Initialize API caller tool."""
        metadata = ToolMetadata(
            name="api_caller",
            description="Call external REST APIs with various HTTP methods and authentication",
            category=ToolCategory.WEB,
            tags=["api", "http", "rest", "request", "client"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="API endpoint URL",
                required=True,
                pattern=r"^https?://",
            ),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                required=True,
                enum=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="HTTP headers as key-value pairs",
                required=False,
            ),
            ToolParameter(
                name="params",
                type="object",
                description="URL query parameters",
                required=False,
            ),
            ToolParameter(
                name="body",
                type="object",
                description="Request body (for POST, PUT, PATCH)",
                required=False,
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="Request timeout in seconds",
                required=False,
                default=30,
                min_value=1,
                max_value=300,
            ),
            ToolParameter(
                name="follow_redirects",
                type="boolean",
                description="Whether to follow redirects",
                required=False,
                default=True,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        follow_redirects: bool = True,
    ) -> Dict[str, Any]:
        """Execute API call.

        Args:
            url: API endpoint URL
            method: HTTP method
            headers: Request headers
            params: Query parameters
            body: Request body
            timeout: Request timeout
            follow_redirects: Follow redirects flag

        Returns:
            Dictionary containing response data
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx"
            )

        # Prepare headers
        request_headers = headers or {}
        if body and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"

        # Prepare request
        method = method.upper()
        request_kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": request_headers,
            "params": params,
            "timeout": timeout,
            "follow_redirects": follow_redirects,
        }

        # Add body for methods that support it
        if method in ["POST", "PUT", "PATCH"] and body:
            if request_headers.get("Content-Type") == "application/json":
                request_kwargs["json"] = body
            else:
                request_kwargs["data"] = body

        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.request(**request_kwargs)

        # Parse response
        result: Dict[str, Any] = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "url": str(response.url),
            "method": method,
        }

        # Try to parse JSON response
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                result["data"] = response.json()
            except json.JSONDecodeError:
                result["data"] = response.text
        else:
            result["data"] = response.text

        # Add response metadata
        result["elapsed_ms"] = response.elapsed.total_seconds() * 1000
        result["success"] = 200 <= response.status_code < 300

        logger.info(
            f"API call to {url} completed with status {response.status_code}"
        )
        return result
