"""
Redis Cache Manager for RiskMesh
Caches hot nodes and recent risk scores for 2-3x performance improvement
"""
import redis
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis caching layer for frequently accessed entities.
    
    Caches:
    - User risk scores (30 min TTL)
    - Device reputation (1 hour TTL)
    - IP reputation (2 hours TTL)
    - Recent propagation results (15 min TTL)
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", enabled: bool = True):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection string
            enabled: Enable/disable caching
        """
        self.enabled = enabled
        self.redis_url = redis_url
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
                logger.info("✓ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self.enabled = False
    
    def get_user_risk(self, user_id: str) -> Optional[float]:
        """
        Get cached user risk score.
        
        Args:
            user_id: User ID
            
        Returns:
            Risk score or None if not cached
        """
        if not self.enabled:
            return None
        
        try:
            key = f"user_risk:{user_id}"
            value = self.client.get(key)
            
            if value:
                logger.debug(f"Cache HIT: {key}")
                return float(value)
            
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set_user_risk(self, user_id: str, risk_score: float, ttl_minutes: int = 30):
        """
        Cache user risk score.
        
        Args:
            user_id: User ID
            risk_score: Risk score (0-1)
            ttl_minutes: Time to live in minutes
        """
        if not self.enabled:
            return
        
        try:
            key = f"user_risk:{user_id}"
            self.client.setex(key, timedelta(minutes=ttl_minutes), str(risk_score))
            logger.debug(f"Cache SET: {key} = {risk_score}")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def get_entity(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached entity (device, IP, merchant).
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            
        Returns:
            Entity data or None
        """
        if not self.enabled:
            return None
        
        try:
            key = f"entity:{entity_type}:{entity_id}"
            value = self.client.get(key)
            
            if value:
                return json.loads(value)
            
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any], ttl_minutes: int = 60):
        """
        Cache entity data.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            data: Entity data
            ttl_minutes: Time to live
        """
        if not self.enabled:
            return
        
        try:
            key = f"entity:{entity_type}:{entity_id}"
            self.client.setex(key, timedelta(minutes=ttl_minutes), json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def get_propagation(self, source_node: str) -> Optional[Dict[str, float]]:
        """
        Get cached propagation results.
        
        Args:
            source_node: Source node ID
            
        Returns:
            Propagation results or None
        """
        if not self.enabled:
            return None
        
        try:
            key = f"propagation:{source_node}"
            value = self.client.get(key)
            
            if value:
                return json.loads(value)
            
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set_propagation(self, source_node: str, results: Dict[str, float], ttl_minutes: int = 15):
        """
        Cache propagation results.
        
        Args:
            source_node: Source node ID
            results: Propagation results
            ttl_minutes: Time to live
        """
        if not self.enabled:
            return
        
        try:
            key = f"propagation:{source_node}"
            self.client.setex(key, timedelta(minutes=ttl_minutes), json.dumps(results))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def invalidate_user(self, user_id: str):
        """Invalidate user cache."""
        if not self.enabled:
            return
        
        try:
            self.client.delete(f"user_risk:{user_id}")
            logger.debug(f"Cache invalidated: user:{user_id}")
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}
