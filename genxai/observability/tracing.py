"""OpenTelemetry tracing for GenXAI."""

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Optional
import os

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class TracingManager:
    """Manage OpenTelemetry tracing for GenXAI."""
    
    def __init__(
        self,
        service_name: str = "genxai",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        enable_console: bool = False
    ):
        """Initialize tracing manager.
        
        Args:
            service_name: Name of the service
            jaeger_host: Jaeger agent host
            jaeger_port: Jaeger agent port
            enable_console: Enable console exporter for debugging
        """
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.enable_console = enable_console
        self.tracer = None
        
        if OTEL_AVAILABLE:
            self._setup_tracing()
    
    def _setup_tracing(self):
        """Set up OpenTelemetry tracing."""
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Add Jaeger exporter
        try:
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
        except Exception:
            # Jaeger not available, continue without it
            pass
        
        # Add console exporter if enabled
        if self.enable_console:
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        # Instrument requests library
        try:
            RequestsInstrumentor().instrument()
        except Exception:
            pass
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Start a new span.
        
        Args:
            name: Span name
            attributes: Optional span attributes
            
        Returns:
            Span context manager
        """
        if not self.tracer:
            return _NoOpSpan()

        span = self.tracer.start_as_current_span(name)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for a tracing span.

        Args:
            name: Span name
            attributes: Optional span attributes
        """
        if not self.tracer:
            yield _NoOpSpan()
            return

        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    
    def trace(
        self,
        span_name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Decorator to trace a function.
        
        Args:
            span_name: Optional span name (defaults to function name)
            attributes: Optional span attributes
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                name = span_name or f"{func.__module__}.{func.__name__}"
                
                if not self.tracer:
                    return await func(*args, **kwargs)
                
                with self.tracer.start_as_current_span(name) as span:
                    # Add attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function info
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("status", "success")
                        return result
                    except Exception as e:
                        span.set_attribute("status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.record_exception(e)
                        raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                name = span_name or f"{func.__module__}.{func.__name__}"
                
                if not self.tracer:
                    return func(*args, **kwargs)
                
                with self.tracer.start_as_current_span(name) as span:
                    # Add attributes
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # Add function info
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("status", "success")
                        return result
                    except Exception as e:
                        span.set_attribute("status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.record_exception(e)
                        raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the current span.
        
        Args:
            name: Event name
            attributes: Optional event attributes
        """
        if not self.tracer:
            return
        
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})
    
    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the current span.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        if not self.tracer:
            return
        
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """Record an exception in the current span.
        
        Args:
            exception: Exception to record
        """
        if not self.tracer:
            return
        
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)


class _NoOpSpan:
    """No-op span when tracing is not available."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def set_attribute(self, key: str, value: Any):
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass
    
    def record_exception(self, exception: Exception):
        pass


# Global tracing manager
_global_tracing = None


def get_tracing_manager() -> TracingManager:
    """Get global tracing manager.
    
    Returns:
        Global tracing manager instance
    """
    global _global_tracing
    
    if _global_tracing is None:
        # Initialize from environment variables
        service_name = os.getenv("GENXAI_SERVICE_NAME", "genxai")
        jaeger_host = os.getenv("JAEGER_AGENT_HOST", "localhost")
        jaeger_port = int(os.getenv("JAEGER_AGENT_PORT", "6831"))
        enable_console = os.getenv("GENXAI_TRACE_CONSOLE", "false").lower() == "true"
        
        _global_tracing = TracingManager(
            service_name=service_name,
            jaeger_host=jaeger_host,
            jaeger_port=jaeger_port,
            enable_console=enable_console
        )
    
    return _global_tracing


def trace(span_name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator to trace a function.
    
    Args:
        span_name: Optional span name (defaults to function name)
        attributes: Optional span attributes
        
    Returns:
        Decorated function
    """
    return get_tracing_manager().trace(span_name, attributes)


def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Start a new span.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        
    Returns:
        Span context manager
    """
    return get_tracing_manager().start_span(name, attributes)


def span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Context manager for a tracing span.

    Args:
        name: Span name
        attributes: Optional span attributes

    Returns:
        Context manager yielding the span
    """
    return get_tracing_manager().span(name, attributes)


def add_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Add an event to the current span.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    get_tracing_manager().add_event(name, attributes)


def set_attribute(key: str, value: Any):
    """Set an attribute on the current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    get_tracing_manager().set_attribute(key, value)


def record_exception(exception: Exception):
    """Record an exception in the current span.
    
    Args:
        exception: Exception to record
    """
    get_tracing_manager().record_exception(exception)
