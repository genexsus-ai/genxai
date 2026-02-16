"""OAuth 2.0 integration for GenXAI."""

import requests
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from urllib.parse import urlencode


class OAuthProvider(ABC):
    """Base OAuth 2.0 provider."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize OAuth provider.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI after authentication
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get OAuth authorization URL.
        
        Args:
            state: Optional state parameter
            
        Returns:
            Authorization URL
        """
        pass
    
    @abstractmethod
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens.
        
        Args:
            code: Authorization code
            
        Returns:
            Token response with access_token, refresh_token, etc.
        """
        pass
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information.
        
        Args:
            access_token: Access token
            
        Returns:
            User information
        """
        pass


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider."""
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        
        if state:
            params["state"] = state
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        response.raise_for_status()
        
        return response.json()


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 provider."""
    
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read:user user:email",
        }
        
        if state:
            params["state"] = state
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        headers = {"Accept": "application/json"}
        response = requests.post(self.TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        response = requests.get(self.USER_INFO_URL, headers=headers)
        response.raise_for_status()
        
        return response.json()


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth 2.0 provider."""
    
    AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Microsoft OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile User.Read",
        }
        
        if state:
            params["state"] = state
        
        return f"{self.AUTH_URL}?{urlencode(params)}"
    
    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        response.raise_for_status()
        
        return response.json()


def create_oauth_provider(
    provider: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str
) -> OAuthProvider:
    """Create OAuth provider instance.
    
    Args:
        provider: Provider name (google, github, microsoft)
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: Redirect URI
        
    Returns:
        OAuthProvider instance
    """
    providers = {
        "google": GoogleOAuthProvider,
        "github": GitHubOAuthProvider,
        "microsoft": MicrosoftOAuthProvider,
    }
    
    provider_class = providers.get(provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown OAuth provider: {provider}")
    
    return provider_class(client_id, client_secret, redirect_uri)
