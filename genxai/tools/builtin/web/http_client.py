"""HTTP client tool for advanced HTTP operations."""

from typing import Any, Dict, List, Optional
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class HTTPClientTool(Tool):
    """Advanced HTTP client with session management and cookie support."""

    def __init__(self) -> None:
        """Initialize HTTP client tool."""
        metadata = ToolMetadata(
            name="http_client",
            description="Advanced HTTP client with session management, cookies, and custom configurations",
            category=ToolCategory.WEB,
            tags=["http", "client", "session", "cookies", "request"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="Target URL",
                required=True,
                pattern=r"^https?://",
            ),
            ToolParameter(
                name="method",
                type="string",
                description="HTTP method",
                required=False,
                default="GET",
                enum=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
            ),
            ToolParameter(
                name="headers",
                type="object",
                description="Custom HTTP headers",
                required=False,
            ),
            ToolParameter(
                name="cookies",
                type="object",
                description="Cookies to send with request",
                required=False,
            ),
            ToolParameter(
                name="auth",
                type="object",
                description="Authentication credentials (username, password)",
                required=False,
            ),
            ToolParameter(
                name="verify_ssl",
                type="boolean",
                description="Whether to verify SSL certificates",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="max_redirects",
                type="number",
                description="Maximum number of redirects to follow",
                required=False,
                default=10,
                min_value=0,
                max_value=50,
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
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        auth: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True,
        max_redirects: int = 10,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Execute HTTP request with advanced options.

        Args:
            url: Target URL
            method: HTTP method
            headers: Custom headers
            cookies: Cookies
            auth: Authentication credentials
            verify_ssl: SSL verification flag
            max_redirects: Maximum redirects
            timeout: Request timeout

        Returns:
            Dictionary containing response data
        """
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx package not installed. Install with: pip install httpx"
            )

        # Prepare client configuration
        client_kwargs: Dict[str, Any] = {
            "timeout": timeout,
            "verify": verify_ssl,
            "follow_redirects": max_redirects > 0,
            "max_redirects": max_redirects,
        }

        # Add authentication if provided
        if auth and "username" in auth and "password" in auth:
            client_kwargs["auth"] = (auth["username"], auth["password"])

        # Make request
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                cookies=cookies,
            )

        # Build result
        result: Dict[str, Any] = {
            "status_code": response.status_code,
            "reason_phrase": response.reason_phrase,
            "http_version": response.http_version,
            "url": str(response.url),
            "method": method.upper(),
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "elapsed_ms": response.elapsed.total_seconds() * 1000,
        }

        # Parse response content
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                result["data"] = response.json()
                result["content_type"] = "json"
            except Exception:
                result["data"] = response.text
                result["content_type"] = "text"
        elif "text/" in content_type:
            result["data"] = response.text
            result["content_type"] = "text"
        else:
            result["data"] = f"<binary data: {len(response.content)} bytes>"
            result["content_type"] = "binary"
            result["content_length"] = len(response.content)

        # Add redirect history
        if response.history:
            result["redirects"] = [
                {
                    "url": str(r.url),
                    "status_code": r.status_code,
                }
                for r in response.history
            ]
            result["redirect_count"] = len(response.history)

        # Success flag
        result["success"] = 200 <= response.status_code < 300

        logger.info(
            f"HTTP {method} request to {url} completed with status {response.status_code}"
        )
        return result
