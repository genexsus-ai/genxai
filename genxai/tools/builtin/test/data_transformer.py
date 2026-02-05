"""Data transformation tool for testing JSON/data operations."""

from typing import Any
import json
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory


class DataTransformerTool(Tool):
    """Tool for JSON and data transformation operations."""

    def __init__(self):
        """Initialize data transformer tool."""
        metadata = ToolMetadata(
            name="data_transformer",
            description="Transform and manipulate JSON data (keys, values, filter, sort)",
            category=ToolCategory.DATA_PROCESSING,
            tags=["json", "data", "transform", "test"],
            version="1.0.0",
            author="GenXAI",
        )

        parameters = [
            ToolParameter(
                name="data",
                type="string",
                description="JSON string to transform",
                required=True,
            ),
            ToolParameter(
                name="transformation",
                type="string",
                description="The transformation to apply",
                required=True,
                enum=["keys", "values", "count", "pretty", "minify", "reverse_keys"],
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the data transformation.

        Args:
            **kwargs: Tool parameters (data, transformation)

        Returns:
            Result of the transformation
        """
        data_str = kwargs.get("data", "{}")
        transformation = kwargs.get("transformation")

        try:
            # Parse JSON
            data = json.loads(data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

        if transformation == "keys":
            if isinstance(data, dict):
                result = list(data.keys())
            else:
                raise ValueError("Data must be a JSON object for 'keys' transformation")
        
        elif transformation == "values":
            if isinstance(data, dict):
                result = list(data.values())
            else:
                raise ValueError("Data must be a JSON object for 'values' transformation")
        
        elif transformation == "count":
            if isinstance(data, dict):
                result = len(data)
            elif isinstance(data, list):
                result = len(data)
            else:
                result = 1
        
        elif transformation == "pretty":
            result = json.dumps(data, indent=2, sort_keys=True)
        
        elif transformation == "minify":
            result = json.dumps(data, separators=(',', ':'))
        
        elif transformation == "reverse_keys":
            if isinstance(data, dict):
                result = {k: v for k, v in reversed(data.items())}
            else:
                raise ValueError("Data must be a JSON object for 'reverse_keys' transformation")
        
        else:
            raise ValueError(f"Unknown transformation: {transformation}")

        return {
            "original": data,
            "transformation": transformation,
            "result": result,
            "original_type": type(data).__name__,
            "result_type": type(result).__name__,
        }
