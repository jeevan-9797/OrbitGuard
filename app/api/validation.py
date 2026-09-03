"""Validation API endpoints for deterministic safety verification of recovery plans."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.recovery import RecoveryPlan
from app.schemas.validation import ValidationResult
from app.services.orchestrator import (
    attach_plan_validation,
    find_plan,
    get_incident,
    list_incidents,
)
from app.services.validator import validate_recovery_plan
from app.simulator.telemetry import get_telemetry_history

router = APIRouter(prefix="/api", tags=["validation"])


# ── Request Models ───────────────────────────────────────────────────────────

class ValidatePlanRequest(BaseModel):
    """Payload to validate a recovery plan."""

    plan_id: Optional[str] = Field(
        default=None,
        description="ID of an existing recovery plan in the orchestrator registry.",
        examples=["PLAN-A1B2C3D4"],
    )
    plan: Optional[RecoveryPlan] = Field(
        default=None,
        description="Direct candidate recovery plan object to validate.",
    )
    telemetry: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional custom telemetry snapshot to validate against.",
    )


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/plans/validate", response_model=ValidationResult)
async def validate_plan(payload: ValidatePlanRequest) -> ValidationResult:
    """Run deterministic safety validation rules on a candidate recovery plan.

    Enforces:
    - **Constraint 1:** Reject `ENTER_SAFE_THERMAL_MODE` if payload power is active without prior `REDUCE_PAYLOAD_LOAD`.
    - **Constraint 2:** Reject maneuvers if reaction wheel speed jitter is high.
    - **Constraint 3:** Flag warning if battery state of charge (SoC) < 30%.

    Updates the parent incident status to `VALIDATING` and attaches validation results.
    """
    target_plan: RecoveryPlan | None = payload.plan
    telemetry_snapshot: dict[str, Any] = payload.telemetry or {}

    # 1. If plan_id is provided, look it up in active incidents
    if payload.plan_id:
        found_plan, parent_incident = find_plan(payload.plan_id)
        if found_plan is None:
            raise HTTPException(
                status_code=404,
                detail=f"Recovery plan '{payload.plan_id}' not found in active incidents.",
            )
        target_plan = found_plan
        if not telemetry_snapshot and parent_incident:
            # Grab latest telemetry for that satellite
            history = get_telemetry_history(parent_incident.satellite_id, window=5)
            if history:
                telemetry_snapshot = history[-1]

    # 2. If neither plan nor plan_id was provided, check the most recent incident's top plan
    if target_plan is None:
        all_inc = list_incidents()
        for inc in all_inc:
            if inc.recovery_plans:
                target_plan = inc.recovery_plans[0]
                if not telemetry_snapshot:
                    history = get_telemetry_history(inc.satellite_id, window=5)
                    if history:
                        telemetry_snapshot = history[-1]
                break

    if target_plan is None:
        raise HTTPException(
            status_code=400,
            detail="No recovery plan provided or found in active incidents to validate.",
        )

    # 3. Run deterministic safety validation
    result = validate_recovery_plan(target_plan, telemetry_snapshot)

    # 4. Attach validation result to orchestrator plan if it exists
    try:
        attach_plan_validation(target_plan.plan_id, result.model_dump(mode="json"))
    except KeyError:
        # Plan was passed ad-hoc, not pre-registered in orchestrator
        pass

    return result
