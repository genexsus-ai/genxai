"""Role-Based Access Control (RBAC) for GenXAI."""

import sys
from enum import Enum
from typing import List, Set, Optional
from functools import wraps
from dataclasses import dataclass


class Role(Enum):
    """User roles."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission(Enum):
    """System permissions."""
    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    WORKFLOW_EXECUTE = "workflow:execute"
    
    # Tool permissions
    TOOL_CREATE = "tool:create"
    TOOL_READ = "tool:read"
    TOOL_UPDATE = "tool:update"
    TOOL_DELETE = "tool:delete"
    TOOL_EXECUTE = "tool:execute"
    
    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    
    Role.DEVELOPER: {
        Permission.AGENT_CREATE,
        Permission.AGENT_READ,
        Permission.AGENT_UPDATE,
        Permission.AGENT_EXECUTE,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_UPDATE,
        Permission.WORKFLOW_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
    },
    
    Role.OPERATOR: {
        Permission.AGENT_READ,
        Permission.AGENT_EXECUTE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_EXECUTE,
        Permission.TOOL_READ,
        Permission.TOOL_EXECUTE,
        Permission.MEMORY_READ,
    },
    
    Role.VIEWER: {
        Permission.AGENT_READ,
        Permission.WORKFLOW_READ,
        Permission.TOOL_READ,
        Permission.MEMORY_READ,
    },
}


@dataclass
class User:
    """User model."""
    user_id: str
    role: Role
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission
        """
        return permission in ROLE_PERMISSIONS[self.role]
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the permissions.
        
        Args:
            permissions: List of permissions
            
        Returns:
            True if user has any permission
        """
        user_permissions = ROLE_PERMISSIONS[self.role]
        return any(p in user_permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all permissions.
        
        Args:
            permissions: List of permissions
            
        Returns:
            True if user has all permissions
        """
        user_permissions = ROLE_PERMISSIONS[self.role]
        return all(p in user_permissions for p in permissions)


class PermissionDenied(Exception):
    """Permission denied exception."""
    pass


# Current user context (thread-local in production)
_current_user: Optional[User] = None


def set_current_user(user: User):
    """Set current user.
    
    Args:
        user: User object
    """
    global _current_user
    _current_user = user


def get_current_user() -> Optional[User]:
    """Get current user.
    
    Returns:
        Current user or None
    """
    return _current_user


def require_permission(permission: Permission):
    """Decorator to require permission.
    
    Args:
        permission: Required permission
        
    Usage:
        @require_permission(Permission.AGENT_EXECUTE)
        async def execute_agent():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user context")
            
            if not user.has_permission(permission):
                raise PermissionDenied(
                    f"User {user.user_id} missing permission: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user context")
            
            if not user.has_permission(permission):
                raise PermissionDenied(
                    f"User {user.user_id} missing permission: {permission.value}"
                )
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def require_role(role: Role):
    """Decorator to require specific role.
    
    Args:
        role: Required role
        
    Usage:
        @require_role(Role.ADMIN)
        async def admin_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user context")
            
            if user.role != role:
                raise PermissionDenied(
                    f"User {user.user_id} requires role: {role.value}"
                )
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user context")
            
            if user.role != role:
                raise PermissionDenied(
                    f"User {user.user_id} requires role: {role.value}"
                )
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _alias_enterprise_module() -> None:
    """Ensure enterprise.* imports resolve to this module instance."""
    module_name = __name__
    alias_name = "enterprise.genxai.security.rbac"
    sys.modules[alias_name] = sys.modules[module_name]
    sys.modules["genxai.security.rbac"] = sys.modules[module_name]


_alias_enterprise_module()
