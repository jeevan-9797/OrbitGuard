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
app.include_router(health_router)
app.include_router(simulator_router)
app.include_router(agents_router)
app.include_router(validation_router)
app.include_router(execution_router)
app.include_router(stream_router)


from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── Static Files & Dashboard ─────────────────────────────────────────────────
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", tags=["dashboard"])
async def dashboard_root():
    """Serve the OrbitGuard Mission Control Web Dashboard."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/dashboard", tags=["dashboard"])
async def dashboard_view():
    """Alternative dashboard route."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return FileResponse(str(static_dir / "index.html"))


@app.get("/api/info", tags=["root"])
async def api_info() -> dict:
    """Landing probe — confirms the API is alive."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
