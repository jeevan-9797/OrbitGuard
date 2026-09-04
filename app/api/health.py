"""Health-check endpoint for OrbitGuard."""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["health"])


async def _check_supabase() -> str:
    """Ping Supabase REST endpoint to verify connectivity."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        return "not_configured"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                },
            )
            return "connected" if response.status_code < 400 else "error"
    except httpx.HTTPError:
        return "unreachable"


def _check_llm() -> str:
    """Return configuration status of the LLM provider."""
    return "configured" if settings.LLM_API_KEY else "not_configured"


@router.get("/health")
async def health_check() -> dict:
    """Return current system health status.

    Checks:
    - **api**: Always ``operational`` if the endpoint responds.
    - **database**: Supabase connectivity (``connected`` | ``not_configured`` | ``unreachable`` | ``error``).
    - **ai_provider**: LLM API key presence (``configured`` | ``not_configured``).
    """
    db_status = await _check_supabase()
    llm_status = _check_llm()

    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "services": {
            "api": "operational",
            "database": db_status,
            "ai_provider": llm_status,
        },
    }
