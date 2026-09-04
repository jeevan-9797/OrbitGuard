"""Simulator & telemetry API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.detector import analyse_telemetry, clear_incidents, get_open_incidents
from app.simulator.telemetry import (
    generate_normal_telemetry,
    get_telemetry_history,
    inject_anomaly,
    reset_simulator,
)

router = APIRouter(prefix="/api", tags=["simulator"])


# ── Request / Response Schemas ───────────────────────────────────────────────

class InjectRequest(BaseModel):
    """Payload for anomaly injection."""
    satellite_id: str = Field(..., examples=["SAT-01"])
    anomaly_type: str = Field(
        ...,
        examples=["battery_overheat", "wheel_degradation"],
        description="One of: battery_overheat, wheel_degradation",
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/simulate/reset")
async def reset() -> dict:
    """Reset the simulator: clear all satellite states, anomalies, and open incidents."""
    sim_result = reset_simulator()
    clear_incidents()
    return sim_result


@router.post("/simulate/inject")
async def inject(payload: InjectRequest) -> dict:
    """Inject a named anomaly into a satellite's telemetry stream.

    The injected anomaly progressively distorts telemetry over time until the
    simulator is reset.
    """
    try:
        return inject_anomaly(payload.satellite_id, payload.anomaly_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/telemetry/{satellite_id}")
async def telemetry(
    satellite_id: str,
    window: int = Query(default=30, ge=1, le=120, description="Number of recent readings to return"),
    generate: int = Query(default=0, ge=0, le=60, description="Generate N new readings before returning"),
) -> dict:
    """Return a recent telemetry time-series window for *satellite_id*.

    Optionally pass ``generate=N`` to produce *N* new telemetry snapshots
    first (each is also run through the anomaly detector).
    """
    anomalies_detected: list[dict] = []

    for _ in range(generate):
        snapshot = generate_normal_telemetry(satellite_id)
        new_anomalies = analyse_telemetry(snapshot)
        anomalies_detected.extend(a.model_dump(mode="json") for a in new_anomalies)

    history = get_telemetry_history(satellite_id, window=window)

    return {
        "satellite_id": satellite_id,
        "readings": len(history),
        "telemetry": history,
        "anomalies_detected": anomalies_detected,
        "open_incidents": [i.model_dump(mode="json") for i in get_open_incidents()],
    }
