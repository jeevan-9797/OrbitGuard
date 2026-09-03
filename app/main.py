"""
FastAPI Main Application Entrypoint
Module: app.main
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes_fleet import router as fleet_router
from app.api.routes_telemetry import router as telemetry_router
from app.api.routes_incidents import router as incident_router
from app.api.routes_demo import router as demo_router
from database.connection import DatabaseManager

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Mission Control Database & Backend API for Satellite Multi-Agent AI System"
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(fleet_router)
app.include_router(telemetry_router)
app.include_router(incident_router)
app.include_router(demo_router)


@app.get("/health")
def health_check():
    """Health check endpoint reporting database connection and latency."""
    db_health = DatabaseManager.check_health()
    return {
        "app": settings.app_name,
        "status": "HEALTHY" if db_health.get("status") == "HEALTHY" else "DEGRADED",
        "database": db_health,
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
