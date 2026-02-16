"""Authentication and API key management for GenXAI."""

import secrets
import hashlib
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
import sqlite3
import os


@dataclass
class APIKey:
    """API key model."""
    key_id: str
    user_id: str
    name: str
    key_hash: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class APIKeyManager:
    """Manage API keys for GenXAI services."""
    
    def __init__(self, db_path: str = "genxai_keys.db"):
        """Initialize API key manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN NOT NULL DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id ON api_keys(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)
        """)
        
        conn.commit()
        conn.close()
    
    def generate_key(
        self, 
        user_id: str, 
        name: str,
        expires_in_days: Optional[int] = None
    ) -> str:
        """Generate new API key.
        
        Args:
            user_id: User ID
            name: Key name/description
            expires_in_days: Optional expiration in days
            
        Returns:
            Generated API key
        """
        # Generate random key
        random_part = secrets.token_urlsafe(32)
        env = os.getenv("GENXAI_ENV", "dev")
        api_key = f"genxai_{env}_{random_part}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Generate key ID
        key_id = secrets.token_urlsafe(16)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_keys (key_id, user_id, name, key_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key_id, user_id, name, key_hash, datetime.now(UTC), expires_at))
        
        conn.commit()
        conn.close()
        
        return api_key
    
    def validate_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            APIKey object if valid, None otherwise
        """
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key_id, user_id, name, key_hash, created_at, last_used, expires_at, is_active
            FROM api_keys
            WHERE key_hash = ? AND is_active = 1
        """, (key_hash,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Parse row
        key_id, user_id, name, key_hash, created_at, last_used, expires_at, is_active = row
        
        # Check expiration
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=UTC)
            if datetime.now(UTC) > expires_dt:
                conn.close()
                return None
        
        # Update last used
        cursor.execute("""
            UPDATE api_keys SET last_used = ? WHERE key_id = ?
        """, (datetime.now(UTC), key_id))
        
        conn.commit()
        conn.close()
        
        return APIKey(
            key_id=key_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            created_at=datetime.fromisoformat(created_at),
            last_used=datetime.fromisoformat(last_used) if last_used else None,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            is_active=bool(is_active)
        )
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke API key.
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            True if revoked, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys SET is_active = 0 WHERE key_id = ?
        """, (key_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def list_keys(self, user_id: str) -> List[APIKey]:
        """List all keys for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of API keys
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key_id, user_id, name, key_hash, created_at, last_used, expires_at, is_active
            FROM api_keys
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        keys = []
        for row in cursor.fetchall():
            key_id, user_id, name, key_hash, created_at, last_used, expires_at, is_active = row
            keys.append(APIKey(
                key_id=key_id,
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                created_at=datetime.fromisoformat(created_at),
                last_used=datetime.fromisoformat(last_used) if last_used else None,
                expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
                is_active=bool(is_active)
            ))
        
        conn.close()
        return keys
    
    def rotate_key(self, key_id: str) -> str:
        """Rotate API key.
        
        Args:
            key_id: Key ID to rotate
            
        Returns:
            New API key
        """
        # Get existing key
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, name, expires_at FROM api_keys WHERE key_id = ?
        """, (key_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise ValueError(f"Key not found: {key_id}")
        
        user_id, name, expires_at = row
        
        # Revoke old key
        self.revoke_key(key_id)
        
        # Generate new key
        expires_in_days = None
        if expires_at:
            expires_dt = datetime.fromisoformat(expires_at)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=UTC)
            expires_in_days = (expires_dt - datetime.now(UTC)).days
        
        return self.generate_key(user_id, name, expires_in_days)


# Global API key manager
_api_key_manager = None


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager.
    
    Returns:
        APIKeyManager instance
    """
    global _api_key_manager
    
    if _api_key_manager is None:
        db_path = os.getenv("GENXAI_API_KEY_DB", "genxai_keys.db")
        _api_key_manager = APIKeyManager(db_path)
    
    return _api_key_manager


def require_api_key(func):
    """Decorator to require API key authentication.
    
    Usage:
        @require_api_key
        async def my_endpoint():
            pass
    """
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get API key from request headers
        # This is a placeholder - actual implementation depends on web framework
        api_key = kwargs.get("api_key") or os.getenv("GENXAI_API_KEY")
        
        if not api_key:
            raise ValueError("API key required")
        
        # Validate key
        manager = get_api_key_manager()
        key_obj = manager.validate_key(api_key)
        
        if not key_obj:
            raise ValueError("Invalid API key")
        
        # Add user_id to kwargs
        kwargs["user_id"] = key_obj.user_id
        
        return await func(*args, **kwargs)
    
    return wrapper
