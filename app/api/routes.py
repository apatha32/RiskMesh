"""
API Routes for RiskMesh
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import time
import uuid
from datetime import datetime

from app.metrics.metrics import request_counter, request_latency, error_counter
from app.metrics.metrics import graph_node_count, graph_edge_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["events"])


class EventRequest(BaseModel):
    """Transaction event request."""
    user_id: str
    device_id: str
    ip_address: str
    merchant_id: str
    transaction_amount: float


class RiskResponse(BaseModel):
    """Risk calculation response."""
    transaction_id: str
    risk_score: float
    propagation_depth: int
    timestamp: datetime


# Global instances (initialized in app startup)
RISK_ENGINE = None
GRAPH_STORE = None


@router.post("/event", response_model=RiskResponse)
async def handle_event(event: EventRequest):
    """
    Process transaction event and return risk score.
    
    Flow:
    1. Update graph with entities
    2. Calculate base risk
    3. Propagate risk through graph
    4. Store in database
    5. Return risk score
    
    Target latency: <50ms
    """
    try:
        request_counter.inc()
        
        start_time = time.time()
        
        # Process event through risk engine
        result = RISK_ENGINE.process_event(event.dict())
        
        # Track metrics
        latency_ms = (time.time() - start_time) * 1000
        request_latency.observe(latency_ms)
        propagation_latency.observe(result.get("propagation_latency_ms", 0))
        
        # Update graph metrics
        graph_node_count.set(GRAPH_STORE.node_count())
        graph_edge_count.set(GRAPH_STORE.edge_count())
        
        logger.info(f"Event processed: risk={result['risk_score']}, latency={latency_ms:.2f}ms")
        
        # Return response
        return RiskResponse(
            transaction_id=result["transaction_id"],
            risk_score=result["risk_score"],
            propagation_depth=result["propagation_depth"],
            timestamp=result["timestamp"]
        )
    
    except Exception as e:
        error_counter.inc()
        logger.error(f"Error processing event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get current system statistics."""
    return {
        "graph_nodes": GRAPH_STORE.node_count(),
        "graph_edges": GRAPH_STORE.edge_count(),
        "timestamp": datetime.utcnow()
    }
