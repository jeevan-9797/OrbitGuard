"""Human-in-the-Loop (HITL) Execution and Digital Twin Simulation API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.simulation import SimulationResult
from app.services.orchestrator import (
    IncidentRecord,
    approve_incident_plan,
    execute_incident_plan,
    find_plan,
    reject_incident_plan,
)
from app.services.simulator_engine import simulate_plan_execution
from app.simulator.telemetry import get_telemetry_history

router = APIRouter(prefix="/api", tags=["execution"])


# ── Request / Response Models ────────────────────────────────────────────────

class PlanApprovalRequest(BaseModel):
    """Payload for operator plan approval."""

    operator_id: Optional[str] = Field(default="FLIGHT-DIRECTOR-01", description="Operator / Flight Director identifier")
    notes: Optional[str] = Field(default=None, description="Operator authorization notes or flight directives")


class PlanRejectionRequest(BaseModel):
    """Payload for operator plan rejection."""

    operator_id: Optional[str] = Field(default="FLIGHT-DIRECTOR-01", description="Operator identifier")
    reason: Optional[str] = Field(default="Rejected by flight controller", description="Reason for plan rejection")


class ExecutionResponse(BaseModel):
    """Result of plan execution and live state remediation."""

    incident_id: str
    plan_id: str
    satellite_id: str
    status: str
    actions_executed: list[str]
    simulation: dict
    stabilized_telemetry: dict
    resolved_at: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/plans/{plan_id}/approve", response_model=IncidentRecord)
async def approve_plan(plan_id: str, payload: Optional[PlanApprovalRequest] = None) -> IncidentRecord:
    """Authorize a recovery plan by Human-in-the-Loop (HITL) flight director approval.

    Transitions incident status from `VALIDATING` -> `APPROVED`.
    """
    notes = payload.notes if payload else None
    op_id = payload.operator_id if payload else "OPERATOR"
    full_notes = f"[Authorized by {op_id}] {notes or 'Plan approved for spacecraft uplink.'}"

    try:
        _, updated_incident = approve_incident_plan(plan_id, operator_notes=full_notes)
        return updated_incident
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Approval transition failed: {exc}") from exc


@router.post("/plans/{plan_id}/execute", response_model=ExecutionResponse)
async def execute_plan(plan_id: str, payload: Optional[PlanApprovalRequest] = None) -> ExecutionResponse:
    """Execute an authorized recovery plan against the spacecraft digital twin simulator.

    Transitions incident state:
    `APPROVED` -> `EXECUTING` -> `VERIFYING` -> `RESOLVED`.
    """
    notes = payload.notes if payload else None
    op_id = payload.operator_id if payload else "OPERATOR"
    full_notes = f"[Executed by {op_id}] {notes or 'Commands dispatched to satellite.'}"

    try:
        summary, _ = await execute_incident_plan(plan_id, operator_notes=full_notes)
        return ExecutionResponse(**summary)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Plan execution failed: {exc}") from exc


@router.post("/plans/{plan_id}/reject", response_model=IncidentRecord)
async def reject_plan(plan_id: str, payload: Optional[PlanRejectionRequest] = None) -> IncidentRecord:
    """Reject a candidate recovery plan.

    Transitions incident state to `REJECTED`.
    """
    reason = payload.reason if payload else "Operator rejection"
    op_id = payload.operator_id if payload else "OPERATOR"
    full_notes = f"[Rejected by {op_id}] {reason}"

    try:
        _, updated_incident = reject_incident_plan(plan_id, operator_notes=full_notes)
        return updated_incident
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Rejection transition failed: {exc}") from exc


@router.post("/plans/{plan_id}/simulate", response_model=SimulationResult)
async def simulate_plan_preview(plan_id: str) -> SimulationResult:
    """Run a forward digital twin simulation preview for a plan without executing live commands."""
    plan, inc = find_plan(plan_id)
    if plan is None or inc is None:
        raise HTTPException(status_code=404, detail=f"Recovery plan '{plan_id}' not found")

    latest_telem = inc.telemetry_history[-1] if inc.telemetry_history else {}
    return simulate_plan_execution(plan, latest_telem)
