"""
API Authentication & Rate Limiting
"""
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Tracks requests per user/IP and enforces limits.
    """
    
    def __init__(self, default_limit: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Requests per window
            window_seconds: Time window in seconds
        """
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.buckets = {}  # user_id -> (tokens, last_refill)
    
    def allow_request(self, user_id: str, limit: Optional[int] = None) -> bool:
        """
        Check if request is allowed.
        
        Args:
            user_id: User identifier
            limit: Optional custom limit (uses default if None)
            
        Returns:
            True if allowed, False if rate limited
        """
        limit = limit or self.default_limit
        now = time.time()
        
        if user_id not in self.buckets:
            # New user: start with full bucket
            self.buckets[user_id] = (limit, now)
            return True
        
        tokens, last_refill = self.buckets[user_id]
        
        # Refill tokens based on time elapsed
        elapsed = now - last_refill
        refill_rate = (limit / self.window_seconds)
        tokens_gained = elapsed * refill_rate
        tokens = min(limit, tokens + tokens_gained)
        
        if tokens >= 1:
            # Allow request
            tokens -= 1
            self.buckets[user_id] = (tokens, now)
            return True
        else:
            # Rate limited
            self.buckets[user_id] = (tokens, now)
            return False
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining tokens for user."""
        if user_id not in self.buckets:
            return self.default_limit
        
        tokens, last_refill = self.buckets[user_id]
        now = time.time()
        elapsed = now - last_refill
        refill_rate = (self.default_limit / self.window_seconds)
        tokens_gained = elapsed * refill_rate
        tokens = min(self.default_limit, tokens + tokens_gained)
        
        return int(tokens)


class APIKeyManager:
    """
    Simple API key management.
    
    In production, use database-backed auth (JWT, OAuth2).
    """
    
    def __init__(self):
        """Initialize with default keys."""
        # In production: load from database/vault
        self.valid_keys = {
            "riskmesh-key-demo-001": {"name": "demo", "rate_limit": 100},
            "riskmesh-key-demo-002": {"name": "test", "rate_limit": 50},
        }
    
    def validate_key(self, api_key: str) -> bool:
        """Validate API key."""
        return api_key in self.valid_keys
    
    def get_user_id(self, api_key: str) -> Optional[str]:
        """Get user ID from API key."""
        if api_key in self.valid_keys:
            return self.valid_keys[api_key]["name"]
        return None
    
    def get_rate_limit(self, api_key: str) -> int:
        """Get rate limit for API key."""
        if api_key in self.valid_keys:
            return self.valid_keys[api_key]["rate_limit"]
        return 50  # Default
