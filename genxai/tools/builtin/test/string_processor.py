"""String processing tool for testing string operations."""

from typing import Any
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory


class StringProcessorTool(Tool):
    """Tool for string manipulation operations."""

    def __init__(self):
        """Initialize string processor tool."""
        metadata = ToolMetadata(
            name="string_processor",
            description="Perform string manipulation operations (uppercase, lowercase, reverse, length, capitalize)",
            category=ToolCategory.DATA_PROCESSING,
            tags=["string", "text", "manipulation", "test"],
            version="1.0.0",
            author="GenXAI",
        )

        parameters = [
            ToolParameter(
                name="text",
                type="string",
                description="The text to process",
                required=True,
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="The operation to perform",
                required=True,
                enum=["uppercase", "lowercase", "reverse", "length", "capitalize", "title"],
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the string operation.

        Args:
            **kwargs: Tool parameters (text, operation)

        Returns:
            Result of the operation
        """
        text = kwargs.get("text", "")
        operation = kwargs.get("operation")

        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "length":
            result = len(text)
        elif operation == "capitalize":
            result = text.capitalize()
        elif operation == "title":
            result = text.title()
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return {
            "original": text,
            "operation": operation,
            "result": result,
            "original_length": len(text),
            "result_length": len(str(result)),
        }
