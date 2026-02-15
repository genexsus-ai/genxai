"""Base tool classes for GenXAI."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from abc import ABC, abstractmethod
import time
import logging

from genxai.tools.security.policy import is_tool_allowed
from genxai.utils.enterprise_compat import (
    get_audit_log,
    get_current_user,
    get_policy_engine,
    record_exception,
    record_tool_execution,
    span,
    AuditEvent,
    Permission,
)

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool categories for organization."""

    WEB = "web"
    DATABASE = "database"
    FILE = "file"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"
    AI = "ai"
    # Backwards-compatible alias for unit tests that expect category == "data"
    DATA = "data"
    DATA_PROCESSING = "data_processing"
    SYSTEM = "system"
    CUSTOM = "custom"


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for strings



class ToolMetadata(BaseModel):
    """Tool metadata."""

    name: str
    description: str
    category: ToolCategory
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    author: str = "GenXAI"
    license: str = "MIT"
    documentation_url: Optional[str] = None


class ToolResult(BaseModel):
    """Tool execution result."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0



class Tool(ABC):
    """Base class for all tools."""

    def __init__(self, metadata: ToolMetadata, parameters: List[ToolParameter]):
        """Initialize tool.

        Args:
            metadata: Tool metadata
            parameters: Tool parameters
        """
        self.metadata = metadata
        self.parameters = parameters
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._success_count = 0
        self._failure_count = 0

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute tool with validation, consistent success semantics, and error handling.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        start_time = time.time()

        status = "success"
        error_type: Optional[str] = None
        try:
            with span("genxai.tool.execute", {"tool_name": self.metadata.name}):
                user = get_current_user()
                if user is not None:
                    get_policy_engine().check(user, f"tool:{self.metadata.name}", Permission.TOOL_EXECUTE)
                    get_audit_log().record(
                        AuditEvent(
                            action="tool.execute",
                            actor_id=user.user_id,
                            resource_id=f"tool:{self.metadata.name}",
                            status="allowed",
                        )
                    )
                allowed, reason = is_tool_allowed(self.metadata.name)
                if not allowed:
                    status = "error"
                    error_type = "PolicyDenied"
                    return ToolResult(
                        success=False,
                        data=None,
                        error=reason or "Tool execution denied by policy",
                        execution_time=time.time() - start_time,
                    )
                # Validate input
                if not self.validate_input(**kwargs):
                    status = "error"
                    error_type = "ValidationError"
                    return ToolResult(
                        success=False,
                        data=None,
                        error="Invalid input parameters",
                        execution_time=time.time() - start_time,
                    )

                # Execute tool logic
                raw_result = await self._execute(**kwargs)

            # Normalize results:
            # - If tool returns ToolResult, respect it.
            # - If tool returns a dict containing a boolean "success" field, map that
            #   to ToolResult.success and propagate "error" if present.
            # - Otherwise treat return value as successful data.
            tool_success: Optional[bool] = None
            tool_error: Optional[str] = None
            result_data: Any = raw_result

            if isinstance(raw_result, ToolResult):
                # Update metrics based on the returned ToolResult.
                execution_time = time.time() - start_time
                self._execution_count += 1
                self._total_execution_time += execution_time
                if raw_result.success:
                    self._success_count += 1
                else:
                    self._failure_count += 1
                    status = "error"
                    error_type = raw_result.error or "ToolError"
                # Ensure metadata/execution_time are populated.
                if not raw_result.metadata:
                    raw_result.metadata = {"tool": self.metadata.name, "version": self.metadata.version}
                raw_result.execution_time = execution_time
                record_tool_execution(
                    tool_name=self.metadata.name,
                    duration=execution_time,
                    status="success" if raw_result.success else "error",
                    error_type=error_type,
                )
                return raw_result

            if isinstance(raw_result, dict) and "success" in raw_result and isinstance(raw_result["success"], bool):
                tool_success = raw_result["success"]
                tool_error = raw_result.get("error")
                # Keep the full raw payload as data to aid debugging.
                result_data = raw_result

            # Update metrics
            execution_time = time.time() - start_time
            self._execution_count += 1
            self._total_execution_time += execution_time

            # If tool explicitly signaled success/failure, respect it.
            if tool_success is False:
                self._failure_count += 1
                status = "error"
                error_type = tool_error or "ToolError"
                logger.warning(
                    f"Tool {self.metadata.name} reported failure in {execution_time:.2f}s: {tool_error}"
                )
                record_tool_execution(
                    tool_name=self.metadata.name,
                    duration=execution_time,
                    status="error",
                    error_type=error_type,
                )
                return ToolResult(
                    success=False,
                    data=result_data,
                    error=tool_error or "Tool reported failure",
                    execution_time=execution_time,
                    metadata={"tool": self.metadata.name, "version": self.metadata.version},
                )

            self._success_count += 1
            logger.info(
                f"Tool {self.metadata.name} executed successfully in {execution_time:.2f}s"
            )
            record_tool_execution(
                tool_name=self.metadata.name,
                duration=execution_time,
                status="success",
            )
            return ToolResult(
                success=True,
                data=result_data,
                execution_time=execution_time,
                metadata={"tool": self.metadata.name, "version": self.metadata.version},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._execution_count += 1
            self._total_execution_time += execution_time
            self._failure_count += 1
            status = "error"
            error_type = type(e).__name__

            logger.error(f"Tool {self.metadata.name} failed: {str(e)}")
            record_exception(e)
            record_tool_execution(
                tool_name=self.metadata.name,
                duration=execution_time,
                status=status,
                error_type=error_type,
            )

            return ToolResult(
                success=False, data=None, error=str(e), execution_time=execution_time
            )

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Implement tool-specific logic.

        Args:
            **kwargs: Tool parameters

        Returns:
            Tool result data
        """
        pass

    def validate_input(self, **kwargs: Any) -> bool:
        """Validate input parameters against schema.

        Args:
            **kwargs: Input parameters

        Returns:
            True if valid, False otherwise
        """
        for param in self.parameters:
            # Check required parameters
            if param.required and param.name not in kwargs:
                logger.error(f"Missing required parameter: {param.name}")
                return False

            if param.name in kwargs:
                value = kwargs[param.name]

                # Type validation
                if param.type == "string" and not isinstance(value, str):
                    logger.error(f"Parameter {param.name} must be string")
                    return False
                elif param.type == "number" and not isinstance(value, (int, float)):
                    logger.error(f"Parameter {param.name} must be number")
                    return False
                elif param.type == "boolean" and not isinstance(value, bool):
                    logger.error(f"Parameter {param.name} must be boolean")
                    return False

                # Range validation
                if param.min_value is not None and value < param.min_value:
                    logger.error(
                        f"Parameter {param.name} must be >= {param.min_value}"
                    )
                    return False
                if param.max_value is not None and value > param.max_value:
                    logger.error(
                        f"Parameter {param.name} must be <= {param.max_value}"
                    )
                    return False

                # Enum validation
                if param.enum and value not in param.enum:
                    logger.error(
                        f"Parameter {param.name} must be one of {param.enum}"
                    )
                    return False

        return True

    def get_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI-style schema.

        Returns:
            Tool schema dictionary
        """
        def _build_param_schema(param: ToolParameter) -> Dict[str, Any]:
            schema: Dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                schema["enum"] = param.enum
            if param.default is not None:
                schema["default"] = param.default
            if param.pattern:
                schema["pattern"] = param.pattern

            if param.type == "number":
                if param.min_value is not None:
                    schema["minimum"] = param.min_value
                if param.max_value is not None:
                    schema["maximum"] = param.max_value

            return schema

        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: _build_param_schema(param)
                    for param in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required],
            },
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": (
                self._success_count / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
            "total_execution_time": self._total_execution_time,
            "average_execution_time": (
                self._total_execution_time / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
        }

    def reset_metrics(self) -> None:
        """Reset tool metrics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._success_count = 0
        self._failure_count = 0

    def __repr__(self) -> str:
        """String representation."""
        return f"Tool(name={self.metadata.name}, category={self.metadata.category})"
