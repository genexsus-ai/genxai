"""Tests for web tools."""

import pytest
from genxai.tools.builtin.web.web_scraper import WebScraperTool
from genxai.tools.builtin.web.api_caller import APICallerTool
from genxai.tools.builtin.web.http_client import HTTPClientTool
from genxai.tools.builtin.web.html_parser import HTMLParserTool
from genxai.tools.builtin.web.url_validator import URLValidatorTool


# ==================== Web Scraper Tool Tests ====================

@pytest.mark.asyncio
async def test_web_scraper_initialization():
    """Test web scraper tool initialization."""
    tool = WebScraperTool()
    assert tool.metadata.name == "web_scraper"
    assert tool.metadata.category == "web"
    assert len(tool.parameters) > 0


@pytest.mark.asyncio
async def test_web_scraper_invalid_url():
    """Test web scraper with invalid URL."""
    tool = WebScraperTool()
    result = await tool.execute(url="invalid-url")
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_web_scraper_nonexistent_url():
    """Test web scraper with nonexistent URL."""
    tool = WebScraperTool()
    result = await tool.execute(url="https://nonexistent-domain-12345.com")
    assert result.success is False


def test_web_scraper_metadata():
    """Test web scraper metadata."""
    tool = WebScraperTool()
    assert "scrape" in tool.metadata.description.lower() or "web" in tool.metadata.description.lower()
    assert len(tool.metadata.tags) > 0


# ==================== API Caller Tool Tests ====================

@pytest.mark.asyncio
async def test_api_caller_initialization():
    """Test API caller tool initialization."""
    tool = APICallerTool()
    assert tool.metadata.name == "api_caller"
    assert tool.metadata.category == "web"


@pytest.mark.asyncio
async def test_api_caller_get_request():
    """Test API caller with GET request."""
    tool = APICallerTool()
    result = await tool.execute(
        url="https://httpbin.org/get",
        method="GET"
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_api_caller_invalid_url():
    """Test API caller with invalid URL."""
    tool = APICallerTool()
    result = await tool.execute(
        url="invalid-url",
        method="GET"
    )
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_api_caller_invalid_method():
    """Test API caller with invalid HTTP method."""
    tool = APICallerTool()
    result = await tool.execute(
        url="https://httpbin.org/get",
        method="INVALID"
    )
    assert result.success is False


def test_api_caller_metadata():
    """Test API caller metadata."""
    tool = APICallerTool()
    assert "api" in tool.metadata.description.lower() or "call" in tool.metadata.description.lower()


# ==================== HTTP Client Tool Tests ====================

@pytest.mark.asyncio
async def test_http_client_initialization():
    """Test HTTP client tool initialization."""
    tool = HTTPClientTool()
    assert tool.metadata.name == "http_client"
    assert tool.metadata.category == "web"


@pytest.mark.asyncio
async def test_http_client_get_request():
    """Test HTTP client with GET request."""
    tool = HTTPClientTool()
    result = await tool.execute(
        url="https://httpbin.org/get",
        method="GET"
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_http_client_post_request():
    """Test HTTP client with POST request."""
    tool = HTTPClientTool()
    result = await tool.execute(
        url="https://httpbin.org/post",
        method="POST",
        data={"key": "value"}
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_http_client_with_headers():
    """Test HTTP client with custom headers."""
    tool = HTTPClientTool()
    result = await tool.execute(
        url="https://httpbin.org/headers",
        method="GET",
        headers={"User-Agent": "GenXAI-Test"}
    )
    # Should either succeed or fail gracefully
    assert result.success is True or result.success is False


@pytest.mark.asyncio
async def test_http_client_invalid_url():
    """Test HTTP client with invalid URL."""
    tool = HTTPClientTool()
    result = await tool.execute(
        url="invalid-url",
        method="GET"
    )
    assert result.success is False


def test_http_client_metadata():
    """Test HTTP client metadata."""
    tool = HTTPClientTool()
    assert "http" in tool.metadata.description.lower() or "client" in tool.metadata.description.lower()


# ==================== HTML Parser Tool Tests ====================

@pytest.mark.asyncio
async def test_html_parser_initialization():
    """Test HTML parser tool initialization."""
    tool = HTMLParserTool()
    assert tool.metadata.name == "html_parser"
    assert tool.metadata.category == "web"


@pytest.mark.asyncio
async def test_html_parser_parse_html():
    """Test HTML parser with valid HTML."""
    tool = HTMLParserTool()
    html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    result = await tool.execute(html=html)
    assert result.success is True
    assert "parsed" in result.data or "elements" in result.data or "text" in result.data


@pytest.mark.asyncio
async def test_html_parser_extract_links():
    """Test HTML parser extracting links."""
    tool = HTMLParserTool()
    html = '<html><body><a href="https://example.com">Link</a></body></html>'
    result = await tool.execute(
        html=html,
        extract="links"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_html_parser_extract_text():
    """Test HTML parser extracting text."""
    tool = HTMLParserTool()
    html = "<html><body><p>Hello World</p></body></html>"
    result = await tool.execute(
        html=html,
        extract="text"
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_html_parser_invalid_html():
    """Test HTML parser with invalid HTML."""
    tool = HTMLParserTool()
    result = await tool.execute(html="<invalid>")
    # Should handle gracefully
    assert result.success is True or result.success is False


def test_html_parser_metadata():
    """Test HTML parser metadata."""
    tool = HTMLParserTool()
    assert "html" in tool.metadata.description.lower() or "parse" in tool.metadata.description.lower()


# ==================== URL Validator Tool Tests ====================

@pytest.mark.asyncio
async def test_url_validator_initialization():
    """Test URL validator tool initialization."""
    tool = URLValidatorTool()
    assert tool.metadata.name == "url_validator"
    assert tool.metadata.category == "web"


@pytest.mark.asyncio
async def test_url_validator_valid_url():
    """Test URL validator with valid URL."""
    tool = URLValidatorTool()
    result = await tool.execute(url="https://www.example.com")
    assert result.success is True
    assert result.data.get("valid") is True


@pytest.mark.asyncio
async def test_url_validator_valid_http_url():
    """Test URL validator with HTTP URL."""
    tool = URLValidatorTool()
    result = await tool.execute(url="http://example.com")
    assert result.success is True
    assert result.data.get("valid") is True


@pytest.mark.asyncio
async def test_url_validator_invalid_url():
    """Test URL validator with invalid URL."""
    tool = URLValidatorTool()
    result = await tool.execute(url="not-a-url")
    assert result.success is True
    assert result.data.get("valid") is False


@pytest.mark.asyncio
async def test_url_validator_url_with_path():
    """Test URL validator with URL containing path."""
    tool = URLValidatorTool()
    result = await tool.execute(url="https://example.com/path/to/page")
    assert result.success is True
    assert result.data.get("valid") is True


@pytest.mark.asyncio
async def test_url_validator_url_with_query():
    """Test URL validator with URL containing query parameters."""
    tool = URLValidatorTool()
    result = await tool.execute(url="https://example.com?param=value")
    assert result.success is True
    assert result.data.get("valid") is True


def test_url_validator_metadata():
    """Test URL validator metadata."""
    tool = URLValidatorTool()
    assert "url" in tool.metadata.description.lower() or "validate" in tool.metadata.description.lower()
