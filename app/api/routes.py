"""
API Routes for RiskMesh - Phase 2 Enhanced
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import time
from datetime import datetime

from app.metrics.metrics import request_counter, request_latency, error_counter
from app.metrics.metrics import graph_node_count, graph_edge_count
from app.auth import APIKeyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["events"])

# Initialize API key manager with default keys
API_KEY_MANAGER = APIKeyManager()


def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, Any]:
    """Verify API key and return user info."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    if not API_KEY_MANAGER.validate_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user_info = {
        "user_id": API_KEY_MANAGER.get_user_id(x_api_key),
        "rate_limit": API_KEY_MANAGER.get_rate_limit(x_api_key)
    }
    return user_info


class EventRequest(BaseModel):
    """Transaction event request."""
    user_id: str
    device_id: str
    ip_address: str
    merchant_id: str
    transaction_amount: float


class ExplanationModel(BaseModel):
    """Risk explanation details."""
    recommendation: str
    reason: str
    confidence: Optional[float] = None
    base_risk_factors: Optional[Dict[str, Any]] = None
    propagation_impact: Optional[Dict[str, Any]] = None


class ClusteringModel(BaseModel):
    """Clustering/fraud ring information."""
    rings: Optional[List[Dict[str, Any]]] = None
    dense_subgraphs: Optional[List[Dict[str, Any]]] = None
    star_patterns: Optional[List[Dict[str, Any]]] = None


class EnhancedRiskResponse(BaseModel):
    """Enhanced risk calculation response with Phase 2 features."""
    transaction_id: str
    risk_score: float
    base_risk: float
    clustering_boost: float
    propagation_depth: int
    propagation_latency_ms: float
    total_latency_ms: float
    timestamp: datetime
    cached: bool = False
    explanation: Optional[ExplanationModel] = None
    clustering_info: Optional[ClusteringModel] = None


# Global instances (initialized in app startup)
RISK_ENGINE = None
GRAPH_STORE = None
CACHE = None


def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, Any]:
    """Verify API key and return user info."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    user_info = API_KEY_MANAGER.validate_key(x_api_key)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return user_info


@router.post("/event", response_model=EnhancedRiskResponse)
async def handle_event(
    event: EventRequest,
    x_api_key: str = Header(None)
):
    """
    Process transaction event and return enhanced risk score with Phase 2 features.
    
    Features:
    1. API key authentication
    2. Redis caching for hot users
    3. Time decay on risk scores
    4. Fraud ring detection
    5. Risk explanation (why score)
    6. Rate limiting
    
    Headers:
    - X-API-Key: Required API key
    
    Target latency: <100ms
    """
    try:
        request_counter.inc()
        
        # Verify API key
        user_info = verify_api_key(x_api_key)
        logger.info(f"Request from user: {user_info['user_id']}")
        
        start_time = time.time()
        
        # Process event through risk engine
        result = RISK_ENGINE.process_event(event.dict())
        
        # Track metrics
        latency_ms = (time.time() - start_time) * 1000
        request_latency.observe(latency_ms)
        
        # Update graph metrics
        graph_node_count.set(GRAPH_STORE.node_count())
        graph_edge_count.set(GRAPH_STORE.edge_count())
        
        logger.info(f"Event processed: risk={result['risk_score']}, latency={latency_ms:.2f}ms")
        
        # Parse explanation and clustering info
        explanation = None
        if result.get("explanation"):
            explanation = ExplanationModel(**result["explanation"])
        
        clustering_info = None
        if result.get("clustering_info"):
            clustering_info = ClusteringModel(**result["clustering_info"])
        
        # Return enhanced response
        return EnhancedRiskResponse(
            transaction_id=result["transaction_id"],
            risk_score=result["risk_score"],
            base_risk=result["base_risk"],
            clustering_boost=result.get("clustering_boost", 0.0),
            propagation_depth=result["propagation_depth"],
            propagation_latency_ms=result.get("propagation_latency_ms", 0.0),
            total_latency_ms=result.get("total_latency_ms", latency_ms),
            timestamp=result["timestamp"],
            cached=result.get("cached", False),
            explanation=explanation,
            clustering_info=clustering_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error_counter.inc()
        logger.error(f"Error processing event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(x_api_key: str = Header(None)):
    """Get current system statistics."""
    verify_api_key(x_api_key)
    
    return {
        "graph_nodes": GRAPH_STORE.node_count(),
        "graph_edges": GRAPH_STORE.edge_count(),
        "timestamp": datetime.utcnow()
    }


@router.get("/cache/stats")
async def get_cache_stats(x_api_key: str = Header(None)):
    """Get cache statistics."""
    verify_api_key(x_api_key)
    
    if not CACHE:
        return {"status": "cache_disabled"}
    
    try:
        stats = CACHE.stats()
        return {
            "cache_enabled": True,
            "memory_usage_bytes": stats.get("memory_usage", 0),
            "keys_count": stats.get("keys_count", 0),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.warning(f"Cache stats failed: {e}")
        return {"error": str(e)}


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    hours: int = Query(24, ge=1, le=720),
    x_api_key: str = Header(None)
):
    """Get risk score distribution over last N hours."""
    verify_api_key(x_api_key)
    
    try:
        from app.analytics import FraudAnalytics
        analytics = FraudAnalytics(RISK_ENGINE.database)
        
        distribution = analytics.get_risk_distribution(hours)
        return {
            "hours": hours,
            "distribution": distribution,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Risk distribution query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/user/{user_id}")
async def get_user_behavior(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    x_api_key: str = Header(None)
):
    """Get user behavior and transaction history."""
    verify_api_key(x_api_key)
    
    try:
        from app.analytics import FraudAnalytics
        analytics = FraudAnalytics(RISK_ENGINE.database)
        
        behavior = analytics.get_user_behavior(user_id, days)
        return {
            "user_id": user_id,
            "days": days,
            "behavior": behavior,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"User behavior query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/top-risky")
async def get_top_risky_users(
    limit: int = Query(10, ge=1, le=100),
    x_api_key: str = Header(None)
):
    """Get top risky users."""
    verify_api_key(x_api_key)
    
    try:
        from app.analytics import FraudAnalytics
        analytics = FraudAnalytics(RISK_ENGINE.database)
        
        top_users = analytics.get_top_risky_users(limit)
        return {
            "limit": limit,
            "top_risky_users": top_users,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Top risky users query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=720),
    x_api_key: str = Header(None)
):
    """Get performance metrics."""
    verify_api_key(x_api_key)
    
    try:
        from app.analytics import FraudAnalytics
        analytics = FraudAnalytics(RISK_ENGINE.database)
        
        metrics = analytics.get_performance_metrics(hours)
        return {
            "hours": hours,
            "metrics": metrics,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Performance metrics query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
