"""Multi-Agent incident analysis and recovery planning API endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.orchestrator import (
    IncidentRecord,
    analyze_incident,
    get_incident,
    list_incidents,
)

router = APIRouter(prefix="/api", tags=["agents"])


# ── Request Models ───────────────────────────────────────────────────────────

class AnalyzeIncidentRequest(BaseModel):
    """Payload to trigger multi-agent analysis on an incident."""

    incident_id: Optional[str] = Field(
        default=None,
        description="ID of the incident/anomaly to analyze. If omitted, the latest detected incident is analyzed.",
        examples=["ANO-A1B2C3D4"],
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/incidents/analyze", response_model=IncidentRecord)
async def trigger_incident_analysis(payload: Optional[AnalyzeIncidentRequest] = None) -> IncidentRecord:
    """Trigger the Diagnostic Agent and Recovery Planner multi-agent pipeline for an incident.

    Executes state machine transitions:
    `DETECTED` -> `INVESTIGATING` -> `DIAGNOSED` -> `PLANNING` -> `VALIDATING`.
    """
    incident_id = payload.incident_id if payload else None

    # If no incident_id provided, pick the most recent one
    if not incident_id:
        all_inc = list_incidents()
        if not all_inc:
            raise HTTPException(
                status_code=400,
                detail="No active incidents found to analyze. Please inject an anomaly or generate telemetry first.",
            )
        incident_id = all_inc[0].incident_id

    try:
        record = await analyze_incident(incident_id)
        return record
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {exc}") from exc


@router.get("/incidents", response_model=list[IncidentRecord])
async def get_all_incidents() -> list[IncidentRecord]:
    """Return all tracked incidents with current status, diagnosis, and recovery plans."""
    return list_incidents()


@router.get("/incidents/{incident_id}", response_model=IncidentRecord)
async def get_incident_by_id(incident_id: str) -> IncidentRecord:
    """Return a single incident by its unique ID."""
    record = get_incident(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return record
