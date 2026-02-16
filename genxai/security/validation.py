"""Input validation and sanitization for GenXAI."""

import re
from typing import Any, Dict
from pydantic import BaseModel, Field, validator
import html


class AgentExecutionRequest(BaseModel):
    """Validate agent execution request."""
    task: str = Field(..., min_length=1, max_length=10000)
    agent_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=300, ge=1, le=3600)
    
    @validator('task')
    def validate_task(cls, v):
        """Validate task for SQL injection patterns."""
        dangerous_patterns = [
            r'(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s+(TABLE|DATABASE|INDEX)',
            r';\s*(DROP|DELETE|INSERT|UPDATE)',
            r'--\s*$',
            r'/\*.*\*/',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potential SQL injection detected")
        
        return v


class WorkflowExecutionRequest(BaseModel):
    """Validate workflow execution request."""
    workflow_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    inputs: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=600, ge=1, le=7200)


class ToolExecutionRequest(BaseModel):
    """Validate tool execution request."""
    tool_name: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=60, ge=1, le=600)


def sanitize_sql(query: str) -> str:
    """Sanitize SQL query.
    
    Args:
        query: SQL query string
        
    Returns:
        Sanitized query
        
    Note:
        This is a basic sanitizer. Always use parameterized queries in production.
    """
    # Remove comments
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    
    # Remove dangerous keywords
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
    for keyword in dangerous_keywords:
        query = re.sub(rf'\b{keyword}\b', '', query, flags=re.IGNORECASE)
    
    # Escape single quotes
    query = query.replace("'", "''")
    
    return query.strip()


def sanitize_html(text: str) -> str:
    """Sanitize HTML to prevent XSS.
    
    Args:
        text: HTML text
        
    Returns:
        Sanitized text
    """
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    text = re.sub(r'\s*on\w+\s*=\s*["\']?[^"\']*["\']?', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text


def sanitize_command(cmd: str) -> str:
    """Sanitize shell command.
    
    Args:
        cmd: Shell command
        
    Returns:
        Sanitized command
        
    Raises:
        ValueError: If command contains dangerous patterns
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        r'[;&|`$]',  # Command chaining
        r'\$\(',  # Command substitution
        r'>\s*/dev/',  # Device access
        r'<\s*/dev/',
        r'/etc/passwd',  # Sensitive files
        r'/etc/shadow',
        r'rm\s+-rf',  # Dangerous commands
        r'dd\s+if=',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd):
            raise ValueError(f"Dangerous command pattern detected: {pattern}")
    
    # Whitelist allowed commands
    allowed_commands = ['ls', 'cat', 'echo', 'pwd', 'date', 'whoami']
    cmd_name = cmd.split()[0] if cmd.split() else ''
    
    if cmd_name not in allowed_commands:
        raise ValueError(f"Command not in whitelist: {cmd_name}")
    
    return cmd


def validate_file_path(path: str) -> str:
    """Validate file path to prevent directory traversal.
    
    Args:
        path: File path
        
    Returns:
        Validated path
        
    Raises:
        ValueError: If path contains dangerous patterns
    """
    # Check for directory traversal
    if '..' in path:
        raise ValueError("Directory traversal detected")
    
    # Check for absolute paths
    if path.startswith('/'):
        raise ValueError("Absolute paths not allowed")
    
    # Check for null bytes
    if '\x00' in path:
        raise ValueError("Null byte detected")
    
    # Normalize path
    path = path.replace('\\', '/')
    path = re.sub(r'/+', '/', path)
    
    return path


def validate_url(url: str) -> str:
    """Validate URL to prevent SSRF.
    
    Args:
        url: URL string
        
    Returns:
        Validated URL
        
    Raises:
        ValueError: If URL is dangerous
    """
    # Check for dangerous protocols
    dangerous_protocols = ['file://', 'ftp://', 'gopher://', 'dict://']
    for protocol in dangerous_protocols:
        if url.lower().startswith(protocol):
            raise ValueError(f"Dangerous protocol: {protocol}")
    
    # Check for localhost/internal IPs
    internal_patterns = [
        r'localhost',
        r'127\.0\.0\.1',
        r'0\.0\.0\.0',
        r'10\.\d+\.\d+\.\d+',
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+',
        r'192\.168\.\d+\.\d+',
    ]
    
    for pattern in internal_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            raise ValueError("Internal/localhost URLs not allowed")
    
    return url


def sanitize_json(data: Any) -> Any:
    """Sanitize JSON data recursively.
    
    Args:
        data: JSON data
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_html(data)
    elif isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    else:
        return data
