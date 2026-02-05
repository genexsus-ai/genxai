"""Web scraper tool for extracting content from web pages."""

from typing import Any, Dict, List, Optional
import logging
import asyncio
from urllib.parse import urljoin, urlparse

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class WebScraperTool(Tool):
    """Extract content from web pages using BeautifulSoup."""

    def __init__(self) -> None:
        """Initialize web scraper tool."""
        metadata = ToolMetadata(
            name="web_scraper",
            description="Extract content, text, and links from web pages",
            category=ToolCategory.WEB,
            tags=["scraping", "web", "extraction", "html", "parsing"],
            version="1.0.0",
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="URL of the web page to scrape",
                required=True,
                pattern=r"^https?://",
            ),
            ToolParameter(
                name="selector",
                type="string",
                description="CSS selector to extract specific content (optional)",
                required=False,
            ),
            ToolParameter(
                name="extract_links",
                type="boolean",
                description="Whether to extract all links from the page",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="extract_images",
                type="boolean",
                description="Whether to extract all image URLs",
                required=False,
                default=False,
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="Request timeout in seconds",
                required=False,
                default=30,
                min_value=1,
                max_value=120,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(
        self,
        url: str,
        selector: Optional[str] = None,
        extract_links: bool = False,
        extract_images: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Execute web scraping.

        Args:
            url: URL to scrape
            selector: CSS selector for specific content
            extract_links: Whether to extract links
            extract_images: Whether to extract images
            timeout: Request timeout

        Returns:
            Dictionary containing scraped content
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError as e:
            raise ImportError(
                f"Required package not installed: {e}. "
                "Install with: pip install httpx beautifulsoup4"
            )

        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        # Fetch page content
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text

        # Parse HTML
        soup = BeautifulSoup(html_content, "html.parser")

        result: Dict[str, Any] = {
            "url": url,
            "title": soup.title.string if soup.title else None,
            "status_code": response.status_code,
        }

        # Extract specific content with selector
        if selector:
            elements = soup.select(selector)
            result["selected_content"] = [
                {"text": elem.get_text(strip=True), "html": str(elem)} for elem in elements
            ]
            result["selected_count"] = len(elements)
        else:
            # Extract all text content
            result["text"] = soup.get_text(separator="\n", strip=True)

        # Extract links
        if extract_links:
            links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                links.append(
                    {
                        "text": link.get_text(strip=True),
                        "href": absolute_url,
                        "title": link.get("title"),
                    }
                )
            result["links"] = links
            result["links_count"] = len(links)

        # Extract images
        if extract_images:
            images = []
            for img in soup.find_all("img"):
                src = img.get("src")
                if src:
                    absolute_url = urljoin(url, src)
                    images.append(
                        {
                            "src": absolute_url,
                            "alt": img.get("alt"),
                            "title": img.get("title"),
                        }
                    )
            result["images"] = images
            result["images_count"] = len(images)

        # Extract metadata
        meta_tags = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                meta_tags[name] = content
        result["metadata"] = meta_tags

        logger.info(f"Successfully scraped {url}")
        return result
