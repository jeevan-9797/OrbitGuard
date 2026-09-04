"""Telemetry API Routes."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.schemas.telemetry import TelemetryPoint, TelemetryCreate, TelemetryBaseline
from app.repositories.telemetry_repo import TelemetryRepository

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("", response_model=List[TelemetryPoint])
def get_telemetry_window(
    satellite_id: str = Query(..., description="Target satellite UUID"),
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    limit: int = Query(100, ge=1, le=1000, description="Max telemetry samples")
):
    """Retrieves ordered, bounded time-series readings for a satellite."""
    return TelemetryRepository.get_telemetry_window(satellite_id=satellite_id, metric=metric, limit=limit)


@router.post("", response_model=TelemetryPoint)
def record_telemetry(payload: TelemetryCreate):
    """Ingests a telemetry measurement into the time-series stream."""
    return TelemetryRepository.record_telemetry(
        satellite_id=payload.satellite_id,
        subsystem_id=payload.subsystem_id,
        metric=payload.metric,
        value=payload.value,
        unit=payload.unit,
        quality=payload.quality
    )


@router.get("/baseline", response_model=Optional[TelemetryBaseline])
def get_baseline(
    satellite_id: str = Query(...),
    mode: str = Query(...),
    metric: str = Query(...)
):
    """Fetches normal range and statistics for a specific metric in a flight mode."""
    b = TelemetryRepository.get_baseline(satellite_id=satellite_id, mode_code=mode, metric=metric)
    if not b:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return b
