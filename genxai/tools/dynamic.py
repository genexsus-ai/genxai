"""Dynamic tool creation from Python code."""

from typing import Any, Dict
import logging
from genxai.tools.base import Tool, ToolMetadata, ToolParameter
from genxai.tools.security import SafeExecutor, ExecutionTimeout

logger = logging.getLogger(__name__)


class DynamicTool(Tool):
    """Tool created dynamically from Python code with security sandboxing."""

    def __init__(
        self, 
        metadata: ToolMetadata, 
        parameters: list[ToolParameter],
        code: str,
        timeout: int = 30
    ):
        """Initialize dynamic tool.

        Args:
            metadata: Tool metadata
            parameters: Tool parameters
            code: Python code to execute
            timeout: Maximum execution time in seconds (default: 30)
        """
        super().__init__(metadata, parameters)
        self.code = code
        self.timeout = timeout
        self._compiled_code = None
        self._safe_executor = SafeExecutor(timeout=timeout)
        self._compile_code()

    def _compile_code(self) -> None:
        """Compile the Python code for execution with security checks."""
        try:
            # Use SafeExecutor for secure compilation
            self._compiled_code = self._safe_executor.compile_code(
                self.code, 
                f'<dynamic:{self.metadata.name}>'
            )
            logger.info(f"Securely compiled code for tool: {self.metadata.name}")
        except (SyntaxError, ValueError) as e:
            logger.error(f"Failed to compile code for {self.metadata.name}: {e}")
            raise ValueError(f"Invalid Python code: {e}")

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute the dynamic tool code in a sandboxed environment.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            # Execute with SafeExecutor (includes timeout and sandboxing)
            result = self._safe_executor.execute(
                self._compiled_code,
                kwargs,
                enable_timeout=True
            )
            
            logger.info(f"Dynamic tool {self.metadata.name} executed successfully")
            return result

        except ExecutionTimeout as e:
            logger.error(f"Dynamic tool {self.metadata.name} timed out: {e}")
            raise RuntimeError(f"Tool execution timed out after {self.timeout} seconds")
        except ValueError as e:
            logger.error(f"Dynamic tool {self.metadata.name} validation failed: {e}")
            raise RuntimeError(f"Tool execution failed: {e}")
        except Exception as e:
            logger.error(f"Dynamic tool {self.metadata.name} execution failed: {e}")
            raise RuntimeError(f"Tool execution failed: {e}")

    def get_code(self) -> str:
        """Get the tool's source code.

        Returns:
            Python source code
        """
        return self.code

    def update_code(self, new_code: str) -> None:
        """Update the tool's code.

        Args:
            new_code: New Python code
        """
        self.code = new_code
        self._compile_code()
        logger.info(f"Updated code for tool: {self.metadata.name}")
    
    def set_timeout(self, timeout: int) -> None:
        """Update the execution timeout.

        Args:
            timeout: New timeout in seconds
        """
        self.timeout = timeout
        self._safe_executor = SafeExecutor(timeout=timeout)
        logger.info(f"Updated timeout for tool {self.metadata.name}: {timeout}s")
