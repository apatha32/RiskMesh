"""
RiskMesh FastAPI Application
"""
from fastapi import FastAPI
from prometheus_client import make_asgi_app
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RiskMesh",
    description="Real Time Graph Based Risk Propagation Engine",
    version="0.1.0"
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("RiskMesh starting up...")
    
    from app.graph.graph_store import GraphStore
    from app.graph.propagation import RiskPropagator
    from app.risk.base_risk import BaseRiskCalculator
    from app.risk.risk_engine import RiskEngine
    from app.db.database import Database
    from app.api import routes
    
    # Initialize components
    graph_store = GraphStore()
    logger.info("✓ Graph store initialized")
    
    propagator = RiskPropagator(alpha=0.5, max_depth=2, risk_threshold=0.1)
    logger.info("✓ Risk propagator initialized")
    
    base_risk_calc = BaseRiskCalculator()
    logger.info("✓ Base risk calculator initialized")
    
    # Initialize database
    db_url = os.getenv("DATABASE_URL", "postgresql://riskmesh:riskmesh123@localhost:5432/riskmesh")
    database = Database(db_url)
    try:
        database.init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    # Initialize risk engine
    risk_engine = RiskEngine(graph_store, propagator, base_risk_calc, database)
    logger.info("✓ Risk engine initialized")
    
    # Set global instances in routes module
    routes.RISK_ENGINE = risk_engine
    routes.GRAPH_STORE = graph_store
    
    logger.info("✓ RiskMesh startup complete")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "riskmesh",
        "version": "0.1.0"
    }


# Import routes after app is created
from app.api.routes import router
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
