"""Error generator tool for testing error handling."""

from typing import Any
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory


class ErrorGeneratorTool(Tool):
    """Tool to intentionally generate errors for testing error handling."""

    def __init__(self):
        """Initialize error generator tool."""
        metadata = ToolMetadata(
            name="error_generator",
            description="Generate different types of errors to test error handling",
            category=ToolCategory.SYSTEM,
            tags=["error", "test", "validation"],
            version="1.0.0",
            author="GenXAI",
        )

        parameters = [
            ToolParameter(
                name="error_type",
                type="string",
                description="Type of error to generate",
                required=True,
                enum=["value_error", "type_error", "zero_division", "key_error", "index_error", "none"],
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Custom error message",
                required=False,
                default="Test error",
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the error generation.

        Args:
            **kwargs: Tool parameters (error_type, message)

        Returns:
            Result or raises an error based on error_type
        """
        error_type = kwargs.get("error_type")
        message = kwargs.get("message", "Test error")

        if error_type == "value_error":
            raise ValueError(f"ValueError: {message}")
        
        elif error_type == "type_error":
            raise TypeError(f"TypeError: {message}")
        
        elif error_type == "zero_division":
            # Intentionally divide by zero
            result = 1 / 0
            return result
        
        elif error_type == "key_error":
            # Access non-existent key
            data = {"key1": "value1"}
            return data["non_existent_key"]
        
        elif error_type == "index_error":
            # Access out of bounds index
            data = [1, 2, 3]
            return data[10]
        
        elif error_type == "none":
            # No error, return success
            return {
                "status": "success",
                "message": "No error generated",
                "error_type": error_type,
            }
        
        else:
            raise ValueError(f"Unknown error type: {error_type}")
