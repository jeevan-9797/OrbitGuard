"""OrbitGuard — Satellite Multi-Agent AI System backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agents_router
from app.api.execution import router as execution_router
from app.api.health import router as health_router
from app.api.simulator import router as simulator_router
from app.api.stream import router as stream_router
from app.api.validation import router as validation_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for the OrbitGuard Satellite Multi-Agent AI System",
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
# Mount health check with /api prefix so /api/health succeeds
app.include_router(health_router, prefix="/api")

# Include remaining routers
app.include_router(simulator_router)
app.include_router(agents_router)
app.include_router(validation_router)
app.include_router(execution_router)
app.include_router(stream_router)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Landing probe — confirms the API is alive."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }