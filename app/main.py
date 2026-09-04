"""OrbitGuard — Satellite Multi-Agent AI System backend."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Backend + Database
from app.config import settings
from app.api.routes_fleet import router as fleet_router
from app.api.routes_telemetry import router as telemetry_router
from app.api.routes_incidents import router as incident_router
from app.api.routes_demo import router as demo_router
from database.connection import DatabaseManager

# AI/ML
from app.api.agents import router as agents_router
from app.api.execution import router as execution_router
from app.api.health import router as health_router
from app.api.simulator import router as simulator_router
from app.api.stream import router as stream_router
from app.api.validation import router as validation_router


app = FastAPI(
    title=getattr(settings, "APP_NAME", getattr(settings, "app_name", "OrbitGuard")),
    version=getattr(settings, "APP_VERSION", "1.0.0"),
    description="Backend API for the OrbitGuard Satellite Multi-Agent AI System",
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Backend + Database Routers
# ============================================================

app.include_router(fleet_router)
app.include_router(telemetry_router)
app.include_router(incident_router)
app.include_router(demo_router)


# ============================================================
# AI/ML Routers
# ============================================================

app.include_router(health_router)
app.include_router(simulator_router)
app.include_router(agents_router)
app.include_router(validation_router)
app.include_router(execution_router)
app.include_router(stream_router)


# ============================================================
# Database Health Check
# ============================================================

@app.get("/health")
def database_health_check():
    """Health check endpoint reporting database connection and latency."""
    db_health = DatabaseManager.check_health()

    return {
        "app": getattr(
            settings,
            "APP_NAME",
            getattr(settings, "app_name", "OrbitGuard"),
        ),
        "status": (
            "HEALTHY"
            if db_health.get("status") == "HEALTHY"
            else "DEGRADED"
        ),
        "database": db_health,
        "environment": getattr(settings, "environment", "unknown"),
    }


# ============================================================
# Static Files & Dashboard
# ============================================================

static_dir = Path(__file__).resolve().parent / "static"

if static_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static",
    )


@app.get("/", tags=["dashboard"])
async def dashboard_root():
    """Serve the OrbitGuard Mission Control Web Dashboard."""
    index_file = static_dir / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file))

    return {
        "app": getattr(
            settings,
            "APP_NAME",
            getattr(settings, "app_name", "OrbitGuard"),
        ),
        "version": getattr(settings, "APP_VERSION", "1.0.0"),
        "docs": "/docs",
    }


@app.get("/dashboard", tags=["dashboard"])
async def dashboard_view():
    """Alternative dashboard route."""
    index_file = static_dir / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file))

    return {
        "app": getattr(
            settings,
            "APP_NAME",
            getattr(settings, "app_name", "OrbitGuard"),
        ),
        "version": getattr(settings, "APP_VERSION", "1.0.0"),
        "docs": "/docs",
    }


@app.get("/api/info", tags=["root"])
async def api_info() -> dict:
    """Landing probe — confirms the API is alive."""
    return {
        "app": getattr(
            settings,
            "APP_NAME",
            getattr(settings, "app_name", "OrbitGuard"),
        ),
        "version": getattr(settings, "APP_VERSION", "1.0.0"),
        "docs": "/docs",
    }


# ============================================================
# Local Development
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )