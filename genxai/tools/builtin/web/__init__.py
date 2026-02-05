"""Web tools for GenXAI."""

from genxai.tools.builtin.web.web_scraper import WebScraperTool
from genxai.tools.builtin.web.api_caller import APICallerTool
from genxai.tools.builtin.web.url_validator import URLValidatorTool
from genxai.tools.builtin.web.http_client import HTTPClientTool
from genxai.tools.builtin.web.html_parser import HTMLParserTool

__all__ = [
    "WebScraperTool",
    "APICallerTool",
    "URLValidatorTool",
    "HTTPClientTool",
    "HTMLParserTool",
]
