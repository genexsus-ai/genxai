"""Structured logging for GenXAI."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, UTC
from typing import Any, Dict, Optional


_request_id_ctx: ContextVar[Optional[str]] = ContextVar("genxai_request_id", default=None)
_workflow_id_ctx: ContextVar[Optional[str]] = ContextVar("genxai_workflow_id", default=None)
_agent_id_ctx: ContextVar[Optional[str]] = ContextVar("genxai_agent_id", default=None)


def set_log_context(
    *,
    request_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    """Set context values for structured logging.

    Args:
        request_id: Request identifier
        workflow_id: Workflow identifier
        agent_id: Agent identifier
    """
    if request_id is not None:
        _request_id_ctx.set(request_id)
    if workflow_id is not None:
        _workflow_id_ctx.set(workflow_id)
    if agent_id is not None:
        _agent_id_ctx.set(agent_id)


def clear_log_context() -> None:
    """Clear logging context values."""
    _request_id_ctx.set(None)
    _workflow_id_ctx.set(None)
    _agent_id_ctx.set(None)


def get_log_context() -> Dict[str, Optional[str]]:
    """Get current logging context values."""
    return {
        "request_id": _request_id_ctx.get(),
        "workflow_id": _workflow_id_ctx.get(),
        "agent_id": _agent_id_ctx.get(),
    }


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add contextual identifiers
        log_data.update(get_log_context())

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: Optional[str] = None,
    redact_sensitive: bool = True,
) -> None:
    """Set up logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use structured JSON logging
        log_file: Optional log file path
    """
    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    if redact_sensitive:
        console_handler.addFilter(SensitiveDataFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        if redact_sensitive:
            file_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(file_handler)

    logging.info(f"Logging configured: level={level}, structured={structured}")


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """Get a logger with optional extra context.

    Args:
        name: Logger name
        extra: Extra context to include in logs

    Returns:
        Configured logger
    """
    base_logger = logging.getLogger(name)

    if extra:
        # Create adapter with extra context
        return logging.LoggerAdapter(base_logger, extra)

    return base_logger


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        """Initialize log context.

        Args:
            logger: Logger instance
            **context: Context key-value pairs
        """
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self) -> logging.Logger:
        """Enter context."""
        self.old_factory = logging.getLogRecordFactory()

        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = self.old_factory(*args, **kwargs)
            record.extra = self.context
            return record

        logging.setLogRecordFactory(record_factory)
        return self.logger

    def __exit__(self, *args: Any) -> None:
        """Exit context."""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""
    
    SENSITIVE_PATTERNS = [
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', 'api_key=***REDACTED***'),
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', 'password=***REDACTED***'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', 'token=***REDACTED***'),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', 'secret=***REDACTED***'),
        (r'authorization["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', 'authorization=***REDACTED***'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive data.
        
        Args:
            record: Log record
            
        Returns:
            True to keep the record
        """
        import re
        
        message = record.getMessage()
        
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        record.msg = message
        record.args = ()
        
        return True


class StructuredLogger:
    """Structured JSON logger with context."""
    
    def __init__(self, name: str):
        """Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def add_context(self, **kwargs: Any) -> None:
        """Add context to all log messages.
        
        Args:
            **kwargs: Context key-value pairs
        """
        self.context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context."""
        self.context.clear()
    
    def _format_message(self, level: str, message: str, **kwargs: Any) -> str:
        """Format log message as JSON.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields
            
        Returns:
            JSON formatted log string
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "message": message,
            "context": {**get_log_context(), **self.context},
            **kwargs
        }
        return json.dumps(log_entry)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.error(self._format_message("ERROR", message, **kwargs))
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        self.logger.critical(self._format_message("CRITICAL", message, **kwargs))
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback.
        
        Args:
            message: Log message
            **kwargs: Additional fields
        """
        import traceback
        kwargs["traceback"] = traceback.format_exc()
        self.logger.error(self._format_message("ERROR", message, **kwargs))


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
