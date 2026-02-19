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
