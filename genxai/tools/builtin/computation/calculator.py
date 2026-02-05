"""Calculator tool for mathematical computations."""

from typing import Any
import ast
import operator
import logging

from genxai.tools.base import Tool, ToolMetadata, ToolParameter, ToolCategory

logger = logging.getLogger(__name__)


class CalculatorTool(Tool):
    """Tool for evaluating mathematical expressions safely."""

    # Allowed operators for safe evaluation
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self) -> None:
        """Initialize calculator tool."""
        metadata = ToolMetadata(
            name="calculator",
            description="Calculate and evaluate mathematical expressions safely",
            category=ToolCategory.COMPUTATION,
            tags=["math", "calculation", "computation", "arithmetic"],
        )

        parameters = [
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5 + 3')",
                pattern=r"^[0-9+\-*/().\s]+$",
            )
        ]

        super().__init__(metadata, parameters)

    async def _execute(self, expression: str) -> Any:
        """Execute mathematical expression.

        Args:
            expression: Mathematical expression string

        Returns:
            Result of the calculation

        Raises:
            ValueError: If expression is invalid or unsafe
        """
        try:
            # Parse the expression
            node = ast.parse(expression, mode="eval")
            
            # Evaluate safely
            result = self._eval_node(node.body)
            
            logger.info(f"Calculated: {expression} = {result}")
            return {"expression": expression, "result": result}

        except Exception as e:
            logger.error(f"Calculator error: {e}")
            raise ValueError(f"Invalid expression: {e}")

    def _eval_node(self, node: ast.AST) -> float:
        """Evaluate AST node safely.

        Args:
            node: AST node to evaluate

        Returns:
            Evaluation result

        Raises:
            ValueError: If node type is not allowed
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return float(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in self._operators:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            return self._operators[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in self._operators:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            return self._operators[op_type](operand)
        else:
            raise ValueError(f"Node type {type(node).__name__} not allowed")
