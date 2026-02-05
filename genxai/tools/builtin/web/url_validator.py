"""URL validator tool for checking URL validity and accessibility."""

from typing import Any, Dict
import logging
from urllib.parse import urlparse
import re

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class URLValidatorTool(Tool):
    """Validate URLs and check their accessibility."""

    def __init__(self) -> None:
        """Initialize URL validator tool."""
        metadata = ToolMetadata(
            name="url_validator",
            description="Validate URL format and check if URLs are accessible",
            category=ToolCategory.WEB,
            tags=["url", "validation", "web", "check", "accessibility"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="URL to validate",
                required=True,
                pattern=r"^https?://",
            ),
            ToolParameter(
                name="check_accessibility",
                type="boolean",
                description="Whether to check if URL is accessible via HTTP",
                required=False,
                default=True,
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="Request timeout in seconds for accessibility check",
                required=False,
                default=10,
                min_value=1,
                max_value=60,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        url: str,
        check_accessibility: bool = True,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        """Execute URL validation.

        Args:
            url: URL to validate
            check_accessibility: Whether to check accessibility
            timeout: Request timeout

        Returns:
            Dictionary containing validation results
        """
        result: Dict[str, Any] = {
            "url": url,
            "is_valid": False,
            "format_valid": False,
            "accessible": None,
        }

        # Validate URL format
        try:
            parsed = urlparse(url)
            
            # Check basic structure
            has_scheme = bool(parsed.scheme)
            has_netloc = bool(parsed.netloc)
            
            # Validate scheme
            valid_schemes = ["http", "https", "ftp", "ftps"]
            scheme_valid = parsed.scheme.lower() in valid_schemes
            
            # Validate domain format
            domain_pattern = re.compile(
                r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
                r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
            )
            domain_valid = bool(domain_pattern.match(parsed.netloc.split(":")[0]))
            
            format_valid = has_scheme and has_netloc and scheme_valid and domain_valid
            
            result.update({
                "format_valid": format_valid,
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment,
            })
            
        except Exception as e:
            result["format_error"] = str(e)
            logger.warning(f"URL format validation failed for {url}: {e}")
            return result

        # Check accessibility if requested and format is valid
        if check_accessibility and format_valid and parsed.scheme in ["http", "https"]:
            try:
                import httpx
            except ImportError:
                result["accessibility_error"] = (
                    "httpx package not installed. Install with: pip install httpx"
                )
                return result

            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.head(url)
                    
                    result.update({
                        "accessible": True,
                        "status_code": response.status_code,
                        "final_url": str(response.url),
                        "redirected": str(response.url) != url,
                        "content_type": response.headers.get("content-type"),
                        "server": response.headers.get("server"),
                    })
                    
            except httpx.HTTPStatusError as e:
                result.update({
                    "accessible": False,
                    "status_code": e.response.status_code,
                    "error": f"HTTP error: {e.response.status_code}",
                })
            except httpx.RequestError as e:
                result.update({
                    "accessible": None,
                    "error": f"Request error: {str(e)}",
                })
            except Exception as e:
                result.update({
                    "accessible": None,
                    "error": f"Unexpected error: {str(e)}",
                })

        # Overall validity
        result["is_valid"] = result["format_valid"] and (
            result["accessible"] is not False if check_accessibility else True
        )

        # Backwards-compatible alias used by unit tests
        result["valid"] = result["is_valid"]

        logger.info(f"URL validation completed for {url}: valid={result['is_valid']}")
        return result
