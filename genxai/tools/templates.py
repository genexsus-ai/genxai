"""Tool templates for quick tool creation."""

from typing import Any, Dict, List
import logging
import httpx
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


# Template definitions
TEMPLATES = {
    "api_call": {
        "name": "API Call Tool",
        "description": "Make HTTP requests to external APIs",
        "parameters": ["url", "method", "headers", "body"],
        "config_schema": {
            "url": {"type": "string", "required": True, "description": "API endpoint URL"},
            "method": {"type": "string", "required": True, "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
            "headers": {"type": "object", "required": False, "description": "HTTP headers"},
            "timeout": {"type": "number", "required": False, "default": 30},
        }
    },
    "text_processor": {
        "name": "Text Processing Tool",
        "description": "Process and transform text data",
        "parameters": ["text", "operation"],
        "config_schema": {
            "operation": {
                "type": "string", 
                "required": True, 
                "enum": ["uppercase", "lowercase", "reverse", "word_count", "char_count"]
            }
        }
    },
    "data_transformer": {
        "name": "Data Transformation Tool",
        "description": "Transform data between formats",
        "parameters": ["data", "from_format", "to_format"],
        "config_schema": {
            "from_format": {"type": "string", "required": True, "enum": ["json", "csv", "xml"]},
            "to_format": {"type": "string", "required": True, "enum": ["json", "csv", "xml"]},
        }
    },
    "file_processor": {
        "name": "File Processing Tool",
        "description": "Read and process files",
        "parameters": ["file_path", "operation"],
        "config_schema": {
            "operation": {"type": "string", "required": True, "enum": ["read", "write", "append", "delete"]},
            "encoding": {"type": "string", "required": False, "default": "utf-8"},
        }
    },
}


class APICallTool(Tool):
    """Template tool for making API calls."""

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        tags: List[str],
        config: Dict[str, Any]
    ):
        """Initialize API call tool."""
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags + ["api", "http", "template"],
        )

        parameters = [
            ToolParameter(
                name="url",
                type="string",
                description="API endpoint URL (overrides default)",
                required=False,
            ),
            ToolParameter(
                name="params",
                type="object",
                description="Query parameters",
                required=False,
            ),
            ToolParameter(
                name="body",
                type="object",
                description="Request body (for POST/PUT/PATCH)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)
        self.config = config
        self.default_url = config.get("url", "")
        self.method = config.get("method", "GET").upper()
        self.default_headers = config.get("headers", {})
        self.timeout = config.get("timeout", 30)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute API call."""
        url = kwargs.get("url", self.default_url)
        params = kwargs.get("params", {})
        body = kwargs.get("body", None)

        if not url:
            raise ValueError("URL is required")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=self.method,
                    url=url,
                    params=params,
                    json=body if body else None,
                    headers=self.default_headers,
                )
                response.raise_for_status()

                # Try to parse as JSON, fallback to text
                try:
                    data = response.json()
                except Exception:
                    data = response.text

                return {
                    "status_code": response.status_code,
                    "data": data,
                    "headers": dict(response.headers),
                }

        except httpx.HTTPError as e:
            logger.error(f"API call failed: {e}")
            raise RuntimeError(f"API call failed: {e}")


class TextProcessorTool(Tool):
    """Template tool for text processing."""

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        tags: List[str],
        config: Dict[str, Any]
    ):
        """Initialize text processor tool."""
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags + ["text", "processing", "template"],
        )

        parameters = [
            ToolParameter(
                name="text",
                type="string",
                description="Text to process",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=False,
                enum=["uppercase", "lowercase", "reverse", "word_count", "char_count"],
            ),
        ]

        super().__init__(metadata, parameters)
        self.config = config
        self.default_operation = config.get("operation", "uppercase")

    async def _execute(self, text: str, operation: str = None, **kwargs: Any) -> Any:
        """Execute text processing."""
        op = operation or self.default_operation

        operations = {
            "uppercase": lambda t: t.upper(),
            "lowercase": lambda t: t.lower(),
            "reverse": lambda t: t[::-1],
            "word_count": lambda t: len(t.split()),
            "char_count": lambda t: len(t),
        }

        if op not in operations:
            raise ValueError(f"Unknown operation: {op}")

        result = operations[op](text)

        return {
            "operation": op,
            "input": text,
            "result": result,
        }


class DataTransformerTool(Tool):
    """Template tool for data transformation."""

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        tags: List[str],
        config: Dict[str, Any]
    ):
        """Initialize data transformer tool."""
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags + ["data", "transformation", "template"],
        )

        parameters = [
            ToolParameter(
                name="data",
                type="string",
                description="Data to transform",
                required=True,
            ),
            ToolParameter(
                name="from_format",
                type="string",
                description="Source format",
                required=False,
                enum=["json", "csv", "xml"],
            ),
            ToolParameter(
                name="to_format",
                type="string",
                description="Target format",
                required=False,
                enum=["json", "csv", "xml"],
            ),
        ]

        super().__init__(metadata, parameters)
        self.config = config
        self.default_from = config.get("from_format", "json")
        self.default_to = config.get("to_format", "json")

    async def _execute(
        self, 
        data: str, 
        from_format: str = None, 
        to_format: str = None,
        **kwargs: Any
    ) -> Any:
        """Execute data transformation."""
        import json
        import csv
        import io

        from_fmt = from_format or self.default_from
        to_fmt = to_format or self.default_to

        # Parse input
        if from_fmt == "json":
            parsed_data = json.loads(data)
        elif from_fmt == "csv":
            reader = csv.DictReader(io.StringIO(data))
            parsed_data = list(reader)
        else:
            raise ValueError(f"Unsupported format: {from_fmt}")

        # Convert output
        if to_fmt == "json":
            result = json.dumps(parsed_data, indent=2)
        elif to_fmt == "csv":
            if not isinstance(parsed_data, list):
                parsed_data = [parsed_data]
            
            output = io.StringIO()
            if parsed_data:
                writer = csv.DictWriter(output, fieldnames=parsed_data[0].keys())
                writer.writeheader()
                writer.writerows(parsed_data)
            result = output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {to_fmt}")

        return {
            "from_format": from_fmt,
            "to_format": to_fmt,
            "result": result,
        }


class FileProcessorTool(Tool):
    """Template tool for file processing."""

    def __init__(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        tags: List[str],
        config: Dict[str, Any]
    ):
        """Initialize file processor tool."""
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            tags=tags + ["file", "io", "template"],
        )

        parameters = [
            ToolParameter(
                name="file_path",
                type="string",
                description="Path to file",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Operation to perform",
                required=False,
                enum=["read", "write", "append"],
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write (for write/append operations)",
                required=False,
            ),
        ]

        super().__init__(metadata, parameters)
        self.config = config
        self.encoding = config.get("encoding", "utf-8")

    async def _execute(
        self,
        file_path: str,
        operation: str = "read",
        content: str = None,
        **kwargs: Any
    ) -> Any:
        """Execute file operation."""
        import aiofiles
        import os

        try:
            if operation == "read":
                async with aiofiles.open(file_path, 'r', encoding=self.encoding) as f:
                    data = await f.read()
                return {"operation": "read", "file_path": file_path, "content": data}

            elif operation == "write":
                if content is None:
                    raise ValueError("Content is required for write operation")
                async with aiofiles.open(file_path, 'w', encoding=self.encoding) as f:
                    await f.write(content)
                return {"operation": "write", "file_path": file_path, "bytes_written": len(content)}

            elif operation == "append":
                if content is None:
                    raise ValueError("Content is required for append operation")
                async with aiofiles.open(file_path, 'a', encoding=self.encoding) as f:
                    await f.write(content)
                return {"operation": "append", "file_path": file_path, "bytes_written": len(content)}

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"File operation failed: {e}")
            raise RuntimeError(f"File operation failed: {e}")


def create_tool_from_template(
    name: str,
    description: str,
    category: ToolCategory,
    tags: List[str],
    template: str,
    config: Dict[str, Any]
) -> Tool:
    """Create a tool from a template.

    Args:
        name: Tool name
        description: Tool description
        category: Tool category
        tags: Tool tags
        template: Template name
        config: Template configuration

    Returns:
        Tool instance

    Raises:
        ValueError: If template is unknown
    """
    template_classes = {
        "api_call": APICallTool,
        "text_processor": TextProcessorTool,
        "data_transformer": DataTransformerTool,
        "file_processor": FileProcessorTool,
    }

    if template not in template_classes:
        raise ValueError(f"Unknown template: {template}")

    tool_class = template_classes[template]
    return tool_class(name, description, category, tags, config)


def get_available_templates() -> List[Dict[str, Any]]:
    """Get list of available templates.

    Returns:
        List of template definitions
    """
    return [
        {
            "id": template_id,
            "name": template_data["name"],
            "description": template_data["description"],
            "parameters": template_data["parameters"],
            "config_schema": template_data["config_schema"],
        }
        for template_id, template_data in TEMPLATES.items()
    ]
