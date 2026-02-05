"""Resource limits and monitoring for tool execution."""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits for tool execution."""
    
    max_execution_time: float = 30.0  # seconds
    max_memory_mb: Optional[float] = None  # MB (not enforced yet, placeholder)
    max_cpu_percent: Optional[float] = None  # % (not enforced yet, placeholder)
    
    def __post_init__(self):
        """Validate limits."""
        if self.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")
        
        if self.max_memory_mb is not None and self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        
        if self.max_cpu_percent is not None and (
            self.max_cpu_percent <= 0 or self.max_cpu_percent > 100
        ):
            raise ValueError("max_cpu_percent must be between 0 and 100")


class ExecutionLimiter:
    """Rate limiter and resource monitor for tool execution."""
    
    def __init__(
        self,
        max_executions_per_minute: int = 60,
        max_executions_per_hour: int = 1000,
        resource_limits: Optional[ResourceLimits] = None
    ):
        """Initialize execution limiter.
        
        Args:
            max_executions_per_minute: Maximum executions per minute per tool
            max_executions_per_hour: Maximum executions per hour per tool
            resource_limits: Resource limits for execution
        """
        self.max_executions_per_minute = max_executions_per_minute
        self.max_executions_per_hour = max_executions_per_hour
        self.resource_limits = resource_limits or ResourceLimits()
        
        # Track execution history
        self._execution_history: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
        
        logger.info(
            f"ExecutionLimiter initialized: "
            f"{max_executions_per_minute}/min, {max_executions_per_hour}/hour"
        )
    
    def _clean_old_executions(self, tool_name: str, current_time: float) -> None:
        """Remove executions older than 1 hour.
        
        Args:
            tool_name: Name of the tool
            current_time: Current timestamp
        """
        hour_ago = current_time - 3600
        self._execution_history[tool_name] = [
            ts for ts in self._execution_history[tool_name]
            if ts > hour_ago
        ]
    
    def check_rate_limit(self, tool_name: str) -> tuple[bool, Optional[str]]:
        """Check if execution is allowed based on rate limits.
        
        Args:
            tool_name: Name of the tool to execute
            
        Returns:
            Tuple of (allowed, error_message)
        """
        with self._lock:
            current_time = time.time()
            
            # Clean old executions
            self._clean_old_executions(tool_name, current_time)
            
            executions = self._execution_history[tool_name]
            
            # Check per-minute limit
            minute_ago = current_time - 60
            recent_executions = sum(1 for ts in executions if ts > minute_ago)
            
            if recent_executions >= self.max_executions_per_minute:
                error_msg = (
                    f"Rate limit exceeded: {recent_executions} executions in the last minute. "
                    f"Maximum allowed: {self.max_executions_per_minute}/minute"
                )
                logger.warning(f"Rate limit exceeded for tool '{tool_name}': {error_msg}")
                return False, error_msg
            
            # Check per-hour limit
            if len(executions) >= self.max_executions_per_hour:
                error_msg = (
                    f"Rate limit exceeded: {len(executions)} executions in the last hour. "
                    f"Maximum allowed: {self.max_executions_per_hour}/hour"
                )
                logger.warning(f"Rate limit exceeded for tool '{tool_name}': {error_msg}")
                return False, error_msg
            
            return True, None
    
    def record_execution(self, tool_name: str) -> None:
        """Record a tool execution.
        
        Args:
            tool_name: Name of the tool executed
        """
        with self._lock:
            current_time = time.time()
            self._execution_history[tool_name].append(current_time)
            logger.debug(f"Recorded execution for tool '{tool_name}'")
    
    def get_execution_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get execution statistics for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with execution statistics
        """
        with self._lock:
            current_time = time.time()
            self._clean_old_executions(tool_name, current_time)
            
            executions = self._execution_history[tool_name]
            minute_ago = current_time - 60
            
            recent_executions = sum(1 for ts in executions if ts > minute_ago)
            
            return {
                "tool_name": tool_name,
                "executions_last_minute": recent_executions,
                "executions_last_hour": len(executions),
                "max_per_minute": self.max_executions_per_minute,
                "max_per_hour": self.max_executions_per_hour,
                "remaining_minute": max(0, self.max_executions_per_minute - recent_executions),
                "remaining_hour": max(0, self.max_executions_per_hour - len(executions)),
            }
    
    def reset_limits(self, tool_name: Optional[str] = None) -> None:
        """Reset execution limits.
        
        Args:
            tool_name: Name of tool to reset, or None to reset all
        """
        with self._lock:
            if tool_name:
                self._execution_history[tool_name] = []
                logger.info(f"Reset execution limits for tool '{tool_name}'")
            else:
                self._execution_history.clear()
                logger.info("Reset execution limits for all tools")
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get execution statistics for all tools.
        
        Returns:
            Dictionary mapping tool names to their statistics
        """
        with self._lock:
            return {
                tool_name: self.get_execution_stats(tool_name)
                for tool_name in self._execution_history.keys()
            }


# Global execution limiter instance
_global_limiter: Optional[ExecutionLimiter] = None
_limiter_lock = Lock()


def get_global_limiter() -> ExecutionLimiter:
    """Get or create the global execution limiter.
    
    Returns:
        Global ExecutionLimiter instance
    """
    global _global_limiter
    
    with _limiter_lock:
        if _global_limiter is None:
            _global_limiter = ExecutionLimiter()
            logger.info("Created global ExecutionLimiter")
        
        return _global_limiter


def set_global_limiter(limiter: ExecutionLimiter) -> None:
    """Set the global execution limiter.
    
    Args:
        limiter: ExecutionLimiter instance to use globally
    """
    global _global_limiter
    
    with _limiter_lock:
        _global_limiter = limiter
        logger.info("Updated global ExecutionLimiter")
