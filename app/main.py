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
    from app.cache import RedisCache
    from app.graph.time_decay import TimeDecayCalculator
    from app.graph.clustering import ClusteringDetector
    from app.risk.explainer import RiskExplainer
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
    
    # Initialize Phase 2 components
    cache = None
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache = RedisCache(redis_url)
        logger.info("✓ Redis cache initialized")
    except Exception as e:
        logger.warning(f"Redis cache initialization failed: {e}")
    
    time_decay = TimeDecayCalculator(decay_rate=0.995, min_risk=0.01)
    logger.info("✓ Time decay calculator initialized")
    
    clustering_detector = ClusteringDetector(density_threshold=0.3)
    logger.info("✓ Clustering detector initialized")
    
    explainer = RiskExplainer()
    logger.info("✓ Risk explainer initialized")
    
    # Initialize risk engine with Phase 2 components
    risk_engine = RiskEngine(
        graph_store, 
        propagator, 
        base_risk_calc, 
        database,
        cache=cache,
        time_decay=time_decay,
        clustering_detector=clustering_detector,
        explainer=explainer
    )
    logger.info("✓ Risk engine initialized (with Phase 2 enhancements)")
    
    # Set global instances in routes module
    routes.RISK_ENGINE = risk_engine
    routes.GRAPH_STORE = graph_store
    routes.CACHE = cache
    
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
