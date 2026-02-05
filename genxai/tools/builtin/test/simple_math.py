"""Simple math tool for testing basic operations."""

from typing import Any
from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory


class SimpleMathTool(Tool):
    """Tool for basic arithmetic operations."""

    def __init__(self):
        """Initialize simple math tool."""
        metadata = ToolMetadata(
            name="simple_math",
            description="Perform basic arithmetic operations (add, subtract, multiply, divide)",
            category=ToolCategory.COMPUTATION,
            tags=["math", "arithmetic", "test"],
            version="1.0.0",
            author="GenXAI",
        )

        parameters = [
            ToolParameter(
                name="operation",
                type="string",
                description="The operation to perform",
                required=True,
                enum=["add", "subtract", "multiply", "divide"],
            ),
            ToolParameter(
                name="a",
                type="number",
                description="First number",
                required=True,
            ),
            ToolParameter(
                name="b",
                type="number",
                description="Second number",
                required=True,
            ),
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the math operation.

        Args:
            **kwargs: Tool parameters (operation, a, b)

        Returns:
            Result of the operation
        """
        operation = kwargs.get("operation")
        a = kwargs.get("a")
        b = kwargs.get("b")

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Cannot divide by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result,
            "formula": f"{a} {self._get_operator(operation)} {b} = {result}",
        }

    def _get_operator(self, operation: str) -> str:
        """Get the operator symbol for an operation.

        Args:
            operation: Operation name

        Returns:
            Operator symbol
        """
        operators = {
            "add": "+",
            "subtract": "-",
            "multiply": "×",
            "divide": "÷",
        }
        return operators.get(operation, "?")
