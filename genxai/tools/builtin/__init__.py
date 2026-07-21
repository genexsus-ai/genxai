"""Built-in tools for GenXAI."""

# Communication tools
from genxai.tools.builtin.communication.email_sender import EmailSenderTool
from genxai.tools.builtin.communication.human_input import HumanInputTool
from genxai.tools.builtin.communication.notification_manager import NotificationManagerTool
from genxai.tools.builtin.communication.slack_notifier import SlackNotifierTool
from genxai.tools.builtin.communication.sms_sender import SMSSenderTool
from genxai.tools.builtin.communication.webhook_caller import WebhookCallerTool

# Import all tools to trigger registration
# Computation tools
from genxai.tools.builtin.computation.calculator import CalculatorTool
from genxai.tools.builtin.computation.code_executor import CodeExecutorTool
from genxai.tools.builtin.computation.data_validator import DataValidatorTool
from genxai.tools.builtin.computation.hash_generator import HashGeneratorTool
from genxai.tools.builtin.computation.regex_matcher import RegexMatcherTool
from genxai.tools.builtin.data.csv_processor import CSVProcessorTool
from genxai.tools.builtin.data.data_filter import DataFilterTool
from genxai.tools.builtin.data.data_set_fields import SetFieldsTool
from genxai.tools.builtin.data.date_time import DateTimeTool
from genxai.tools.builtin.data.data_transformer import DataTransformerTool

# Data tools
from genxai.tools.builtin.data.json_processor import JSONProcessorTool
from genxai.tools.builtin.data.text_analyzer import TextAnalyzerTool
from genxai.tools.builtin.data.xml_processor import XMLProcessorTool
from genxai.tools.builtin.database.database_inspector import DatabaseInspectorTool
from genxai.tools.builtin.database.mongodb_query import MongoDBQueryTool
from genxai.tools.builtin.database.redis_cache import RedisCacheTool

# Database tools
from genxai.tools.builtin.database.sql_query import SQLQueryTool
from genxai.tools.builtin.database.vector_search import VectorSearchTool
from genxai.tools.builtin.file.directory_scanner import DirectoryScannerTool
from genxai.tools.builtin.file.file_compressor import FileCompressorTool

# File tools
from genxai.tools.builtin.file.file_reader import FileReaderTool
from genxai.tools.builtin.file.file_writer import FileWriterTool
from genxai.tools.builtin.file.image_processor import ImageProcessorTool
from genxai.tools.builtin.file.pdf_parser import PDFParserTool
from genxai.tools.builtin.web.api_caller import APICallerTool
from genxai.tools.builtin.web.html_parser import HTMLParserTool
from genxai.tools.builtin.web.http_client import HTTPClientTool
from genxai.tools.builtin.web.url_validator import URLValidatorTool

# Web tools
from genxai.tools.builtin.web.web_scraper import WebScraperTool
from genxai.tools.registry import ToolRegistry

# Auto-register all tools
_tools_to_register = [
    # Computation
    CalculatorTool(),
    CodeExecutorTool(),
    DataValidatorTool(),
    HashGeneratorTool(),
    RegexMatcherTool(),
    # File
    FileReaderTool(),
    FileWriterTool(),
    DirectoryScannerTool(),
    FileCompressorTool(),
    ImageProcessorTool(),
    PDFParserTool(),
    # Web
    WebScraperTool(),
    APICallerTool(),
    HTTPClientTool(),
    HTMLParserTool(),
    URLValidatorTool(),
    # Database
    SQLQueryTool(),
    MongoDBQueryTool(),
    RedisCacheTool(),
    VectorSearchTool(),
    DatabaseInspectorTool(),
    # Communication
    EmailSenderTool(),
    HumanInputTool(),
    SlackNotifierTool(),
    SMSSenderTool(),
    WebhookCallerTool(),
    NotificationManagerTool(),
    # Data
    JSONProcessorTool(),
    CSVProcessorTool(),
    DataFilterTool(),
    SetFieldsTool(),
    DateTimeTool(),
    XMLProcessorTool(),
    TextAnalyzerTool(),
    DataTransformerTool(),
]

# Register all tools
for tool in _tools_to_register:
    try:
        ToolRegistry.register(tool)
    except Exception as e:
        # Log but don't fail if a tool can't be registered
        import logging
        logging.warning(f"Failed to register tool {tool.metadata.name}: {e}")

__all__ = [
    "CalculatorTool",
    "CodeExecutorTool",
    "DataValidatorTool",
    "HashGeneratorTool",
    "RegexMatcherTool",
    "FileReaderTool",
    "FileWriterTool",
    "DirectoryScannerTool",
    "FileCompressorTool",
    "ImageProcessorTool",
    "PDFParserTool",
    "WebScraperTool",
    "APICallerTool",
    "HTTPClientTool",
    "HTMLParserTool",
    "URLValidatorTool",
    "SQLQueryTool",
    "MongoDBQueryTool",
    "RedisCacheTool",
    "VectorSearchTool",
    "DatabaseInspectorTool",
    "EmailSenderTool",
    "HumanInputTool",
    "SlackNotifierTool",
    "SMSSenderTool",
    "WebhookCallerTool",
    "NotificationManagerTool",
    "JSONProcessorTool",
    "CSVProcessorTool",
    "DataFilterTool",
    "SetFieldsTool",
    "DateTimeTool",
    "XMLProcessorTool",
    "TextAnalyzerTool",
    "DataTransformerTool",
]
