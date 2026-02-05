"""Sandboxed execution environment for dynamic tools."""

import signal
import logging
from typing import Any, Dict, Optional
from contextlib import contextmanager

try:
    from RestrictedPython import compile_restricted, safe_globals
    from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr
    RESTRICTED_PYTHON_AVAILABLE = True
except ImportError:
    RESTRICTED_PYTHON_AVAILABLE = False
    safe_globals = {}
    guarded_iter_unpack_sequence = None
    safer_getattr = None

logger = logging.getLogger(__name__)


class ExecutionTimeout(Exception):
    """Raised when code execution exceeds timeout limit."""
    pass


class SafeExecutor:
    """Secure executor for dynamic Python code using RestrictedPython."""

    def __init__(self, timeout: int = 30):
        """Initialize safe executor.

        Args:
            timeout: Maximum execution time in seconds (default: 30)
        """
        if not RESTRICTED_PYTHON_AVAILABLE:
            logger.warning(
                "RestrictedPython not available. Falling back to basic execution. "
                "Install with: pip install RestrictedPython"
            )
        
        self.timeout = timeout
        self._safe_builtins = self._create_safe_builtins()

    def _create_safe_builtins(self) -> Dict[str, Any]:
        """Create a safe set of built-in functions.

        Returns:
            Dictionary of safe built-in functions
        """
        if RESTRICTED_PYTHON_AVAILABLE:
            # Use RestrictedPython's safe globals as base
            safe_builtins = safe_globals.copy()
            
            # Add additional safe functions
            safe_builtins.update({
                '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
                '_getattr_': safer_getattr,
                # Safe built-ins
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'dict': dict,
                'enumerate': enumerate,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'max': max,
                'min': min,
                'range': range,
                'round': round,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'zip': zip,
                'isinstance': isinstance,
                'type': type,
                'hasattr': hasattr,
                'getattr': safer_getattr,
            })
        else:
            # Fallback to basic safe builtins
            safe_builtins = {
                'abs': abs,
                'all': all,
                'any': any,
                'bool': bool,
                'dict': dict,
                'enumerate': enumerate,
                'float': float,
                'int': int,
                'len': len,
                'list': list,
                'max': max,
                'min': min,
                'range': range,
                'round': round,
                'sorted': sorted,
                'str': str,
                'sum': sum,
                'tuple': tuple,
                'zip': zip,
                'isinstance': isinstance,
                'type': type,
            }
        
        return safe_builtins

    @contextmanager
    def _timeout_context(self):
        """Context manager for execution timeout.

        Raises:
            ExecutionTimeout: If execution exceeds timeout
        """
        def timeout_handler(signum, frame):
            raise ExecutionTimeout(f"Execution exceeded {self.timeout} seconds")

        # Set the signal handler and alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout)
        
        try:
            yield
        finally:
            # Disable the alarm and restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def compile_code(self, code: str, filename: str = '<dynamic>') -> Any:
        """Compile Python code with security restrictions.

        Args:
            code: Python source code to compile
            filename: Filename for error messages

        Returns:
            Compiled code object

        Raises:
            SyntaxError: If code has syntax errors
            ValueError: If code contains restricted operations
        """
        if RESTRICTED_PYTHON_AVAILABLE:
            # Use RestrictedPython for compilation
            byte_code = compile_restricted(code, filename, 'exec')
            
            # Check for compilation errors
            if byte_code.errors:
                error_msg = "; ".join(byte_code.errors)
                raise ValueError(f"Code contains restricted operations: {error_msg}")
            
            return byte_code.code
        else:
            # Fallback to standard compilation
            try:
                return compile(code, filename, 'exec')
            except SyntaxError as e:
                raise SyntaxError(f"Invalid Python code: {e}")

    def execute(
        self, 
        compiled_code: Any, 
        parameters: Dict[str, Any],
        enable_timeout: bool = True
    ) -> Any:
        """Execute compiled code in a sandboxed environment.

        Args:
            compiled_code: Compiled code object
            parameters: Parameters to pass to the code
            enable_timeout: Whether to enforce timeout (default: True)

        Returns:
            Execution result from 'result' variable

        Raises:
            ExecutionTimeout: If execution exceeds timeout
            ValueError: If code doesn't set 'result' variable
            RuntimeError: If execution fails
        """
        # Create execution namespace with safe builtins
        namespace = {
            '__builtins__': self._safe_builtins,
            'params': parameters,
        }

        try:
            # Execute with timeout if enabled
            if enable_timeout:
                with self._timeout_context():
                    exec(compiled_code, namespace)
            else:
                exec(compiled_code, namespace)

            # Check for result variable
            if 'result' not in namespace:
                raise ValueError(
                    "Tool code must set a 'result' variable with the output"
                )

            return namespace['result']

        except ExecutionTimeout:
            logger.error("Code execution timed out")
            raise
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            raise RuntimeError(f"Execution failed: {e}")

    def execute_code(
        self, 
        code: str, 
        parameters: Dict[str, Any],
        enable_timeout: bool = True
    ) -> Any:
        """Compile and execute code in one step.

        Args:
            code: Python source code
            parameters: Parameters to pass to the code
            enable_timeout: Whether to enforce timeout (default: True)

        Returns:
            Execution result

        Raises:
            SyntaxError: If code has syntax errors
            ValueError: If code contains restricted operations or missing result
            ExecutionTimeout: If execution exceeds timeout
            RuntimeError: If execution fails
        """
        compiled_code = self.compile_code(code)
        return self.execute(compiled_code, parameters, enable_timeout)


def create_safe_executor(timeout: int = 30) -> SafeExecutor:
    """Factory function to create a SafeExecutor instance.

    Args:
        timeout: Maximum execution time in seconds

    Returns:
        SafeExecutor instance
    """
    return SafeExecutor(timeout=timeout)
