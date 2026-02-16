"""JWT token management for GenXAI."""

import jwt
import os
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenPayload:
    """JWT token payload."""
    user_id: str
    role: str
    permissions: list[str]
    exp: int
    iat: int
    iss: str = "genxai"


class JWTManager:
    """Manage JWT tokens."""
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        """Initialize JWT manager.
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
        """
        self.secret_key = secret_key or os.getenv("GENXAI_JWT_SECRET", "change-me-in-production")
        self.algorithm = algorithm
        self.issuer = "genxai"
    
    def create_token(
        self,
        user_id: str,
        role: str,
        permissions: list[str],
        expires_in: int = 3600
    ) -> str:
        """Create JWT token.
        
        Args:
            user_id: User ID
            role: User role
            permissions: List of permissions
            expires_in: Token expiration in seconds (default: 1 hour)
            
        Returns:
            JWT token string
        """
        now = datetime.now(UTC)
        exp = now + timedelta(seconds=expires_in)
        
        payload = {
            "sub": user_id,
            "role": role,
            "permissions": permissions,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "iss": self.issuer
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def refresh_token(self, token: str, expires_in: int = 3600) -> str:
        """Refresh JWT token.
        
        Args:
            token: Existing JWT token
            expires_in: New token expiration in seconds
            
        Returns:
            New JWT token
        """
        # Verify existing token
        payload = self.verify_token(token)
        
        # Create new token with same claims
        return self.create_token(
            user_id=payload["sub"],
            role=payload["role"],
            permissions=payload["permissions"],
            expires_in=expires_in
        )
    
    def decode_token_unsafe(self, token: str) -> Dict[str, Any]:
        """Decode token without verification (for debugging).
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
        """
        return jwt.decode(token, options={"verify_signature": False})


# Global JWT manager
_jwt_manager = None


def get_jwt_manager() -> JWTManager:
    """Get global JWT manager.
    
    Returns:
        JWTManager instance
    """
    global _jwt_manager
    
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    
    return _jwt_manager
