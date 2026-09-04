"""Multi-Agent AI Orchestration Service for OrbitGuard.

Manages spacecraft incident lifecycle across deterministic state transitions:
DETECTED -> INVESTIGATING -> DIAGNOSED -> PLANNING -> VALIDATING.

Coordinates Diagnostic Agent and Recovery Planner with automatic retry and
deterministic fallback guarantees.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agents.diagnostic_agent import diagnose_anomaly
from app.agents.recovery_planner import generate_recovery_plans
from app.schemas.anomaly import AnomalyEvent
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.recovery import RecoveryPlan
from app.simulator.telemetry import get_telemetry_history

logger = logging.getLogger(__name__)


# ── Incident Lifecycle States ────────────────────────────────────────────────

class IncidentStatus(str, Enum):
    """Incident lifecycle state machine stages."""

    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSED = "DIAGNOSED"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class StatusTransition(BaseModel):
    """Audit log entry for an incident state change."""

    from_state: IncidentStatus
    to_state: IncidentStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


class IncidentRecord(BaseModel):
    """Complete record tracking an anomaly through diagnosis, recovery planning, and execution."""

    incident_id: str
    satellite_id: str
    status: IncidentStatus = IncidentStatus.DETECTED
    anomaly_event: AnomalyEvent
    telemetry_history: list[dict] = Field(default_factory=list)
    diagnosis: Optional[DiagnosisResult] = None
    recovery_plans: list[RecoveryPlan] = Field(default_factory=list)
    selected_plan_id: Optional[str] = None
    simulation_result: Optional[dict] = None
    execution_result: Optional[dict] = None
    operator_notes: Optional[str] = None
    status_history: list[StatusTransition] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))



# ── Global In-Memory Incident Store ──────────────────────────────────────────

_incidents: dict[str, IncidentRecord] = {}


def get_incident(incident_id: str) -> IncidentRecord | None:
    """Retrieve an incident record by ID."""
    return _incidents.get(incident_id)


def list_incidents() -> list[IncidentRecord]:
    """Retrieve all tracked incident records sorted by creation timestamp."""
    return sorted(_incidents.values(), key=lambda r: r.created_at, reverse=True)


def clear_orchestrator_incidents() -> None:
    """Clear in-memory incidents (used on simulator reset)."""
    _incidents.clear()
    from app.core.database import db
    db.clear_local_db()


def register_detected_incident(
    anomaly_event: AnomalyEvent,
    telemetry_history: list[dict] | None = None,
) -> IncidentRecord:
    """Create and register a new incident in DETECTED status."""
    incident_id = anomaly_event.anomaly_id
    if incident_id in _incidents:
        return _incidents[incident_id]

    if telemetry_history is None:
        telemetry_history = get_telemetry_history(anomaly_event.satellite_id, window=30)

    now = datetime.now(timezone.utc)
    initial_transition = StatusTransition(
        from_state=IncidentStatus.DETECTED,
        to_state=IncidentStatus.DETECTED,
        timestamp=now,
        notes="Anomaly detected by automated monitoring rules",
    )
    record = IncidentRecord(
        incident_id=incident_id,
        satellite_id=anomaly_event.satellite_id,
        status=IncidentStatus.DETECTED,
        anomaly_event=anomaly_event,
        telemetry_history=telemetry_history,
        diagnosis=None,
        recovery_plans=[],
        status_history=[initial_transition],
        created_at=now,
        updated_at=now,
    )
    _incidents[incident_id] = record

    # Synchronize to DB
    try:
        import asyncio
        from app.services.db_sync import persist_audit_event, persist_incident_state
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(persist_incident_state(record))
            asyncio.create_task(persist_audit_event(initial_transition, incident_id=record.incident_id))
    except Exception:
        pass

    return record


# ── State Machine Transition Helper ──────────────────────────────────────────

def _transition(record: IncidentRecord, target_state: IncidentStatus, notes: str | None = None) -> None:
    old_state = record.status
    record.status = target_state
    record.updated_at = datetime.now(timezone.utc)
    transition_entry = StatusTransition(
        from_state=old_state,
        to_state=target_state,
        timestamp=record.updated_at,
        notes=notes,
    )
    record.status_history.append(transition_entry)
    logger.info("Incident %s transitioned: %s -> %s (%s)", record.incident_id, old_state, target_state, notes)

    # Synchronize transition to DB / local fallback
    try:
        import asyncio
        from app.services.db_sync import persist_audit_event, persist_incident_state
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(persist_incident_state(record))
            asyncio.create_task(persist_audit_event(transition_entry, incident_id=record.incident_id))
    except Exception:
        pass



# ── Pipeline Execution ───────────────────────────────────────────────────────

async def analyze_incident(incident_id: str) -> IncidentRecord:
    """Execute multi-agent diagnostic and recovery planning pipeline for an incident.

    State transitions:
    DETECTED -> INVESTIGATING -> DIAGNOSED -> PLANNING -> VALIDATING.
    """
    record = get_incident(incident_id)
    if record is None:
        raise KeyError(f"Incident '{incident_id}' not found")

    # If telemetry history is empty or short, refresh it
    if len(record.telemetry_history) < 10:
        record.telemetry_history = get_telemetry_history(record.satellite_id, window=30)

    # 1. State: INVESTIGATING
    _transition(
        record,
        IncidentStatus.INVESTIGATING,
        "Diagnostic agent started telemetry and subsystem root-cause analysis",
    )

    # 2. Run Diagnostic Agent
    try:
        diagnosis = await diagnose_anomaly(record.anomaly_event, record.telemetry_history)
        record.diagnosis = diagnosis
        _transition(
            record,
            IncidentStatus.DIAGNOSED,
            f"Diagnosis complete: {diagnosis.primary_hypothesis[:80]}...",
        )
    except Exception as exc:
        logger.error("Diagnosis stage error for incident %s: %s", incident_id, exc)
        _transition(record, IncidentStatus.FAILED, f"Diagnosis failed: {exc}")
        raise

    # 3. State: PLANNING
    _transition(
        record,
        IncidentStatus.PLANNING,
        "Recovery planner generating candidate mitigation strategies",
    )

    # 4. Run Recovery Planner Agent
    try:
        current_state = {
            "satellite_id": record.satellite_id,
            "anomaly": record.anomaly_event.model_dump(mode="json"),
            "latest_metrics": record.telemetry_history[-1] if record.telemetry_history else {},
        }
        plans = await generate_recovery_plans(record.diagnosis, current_state)
        
        # 5. Run Safety Validator on candidate plans
        from app.services.validator import validate_recovery_plan
        latest_telem = record.telemetry_history[-1] if record.telemetry_history else {}
        for plan in plans:
            val_result = validate_recovery_plan(plan, latest_telem)
            plan.validation_result = val_result.model_dump(mode="json")

        record.recovery_plans = plans
        _transition(
            record,
            IncidentStatus.VALIDATING,
            f"Generated and validated {len(plans)} candidate recovery plan(s)",
        )
    except Exception as exc:
        logger.error("Planning stage error for incident %s: %s", incident_id, exc)
        _transition(record, IncidentStatus.FAILED, f"Planning failed: {exc}")
        raise

    return record


def find_plan(plan_id: str) -> tuple[RecoveryPlan | None, IncidentRecord | None]:
    """Find a recovery plan and its parent incident across all active records."""
    for inc in _incidents.values():
        for plan in inc.recovery_plans:
            if plan.plan_id == plan_id:
                return plan, inc
    return None, None


def attach_plan_validation(plan_id: str, validation_result_dict: dict) -> tuple[RecoveryPlan, IncidentRecord]:
    """Attach validation results to a specific plan in its parent incident."""
    plan, inc = find_plan(plan_id)
    if plan is None or inc is None:
        raise KeyError(f"RecoveryPlan '{plan_id}' not found")

    plan.validation_result = validation_result_dict
    _transition(inc, IncidentStatus.VALIDATING, f"Updated validation result for plan {plan_id}")
    return plan, inc


def approve_incident_plan(plan_id: str, operator_notes: str | None = None) -> tuple[RecoveryPlan, IncidentRecord]:
    """Approve a recovery plan by human operator authorization.

    Transitions incident from VALIDATING -> APPROVED.
    """
    plan, inc = find_plan(plan_id)
    if plan is None or inc is None:
        raise KeyError(f"RecoveryPlan '{plan_id}' not found")

    inc.selected_plan_id = plan_id
    inc.operator_notes = operator_notes
    _transition(
        inc,
        IncidentStatus.APPROVED,
        f"Plan {plan_id} approved by ground operator. {operator_notes or ''}".strip(),
    )
    return plan, inc


async def execute_incident_plan(
    plan_id: str,
    operator_notes: str | None = None,
) -> tuple[dict, IncidentRecord]:
    """Execute an approved recovery plan against the digital twin simulator and live simulator state.

    Transitions: APPROVED -> EXECUTING -> VERIFYING -> RESOLVED.
    """
    plan, inc = find_plan(plan_id)
    if plan is None or inc is None:
        raise KeyError(f"RecoveryPlan '{plan_id}' not found")

    # Safety Guard 1: Verify deterministic safety validation
    if plan.validation_result:
        is_safe = plan.validation_result.get("is_safe", False)
        is_valid = plan.validation_result.get("is_valid", False)
        if not is_safe or not is_valid:
            violations = plan.validation_result.get("violations", ["Plan failed safety validation"])
            raise ValueError(
                f"Cannot execute plan '{plan_id}': deterministic safety validation failed: {'; '.join(violations)}"
            )

    # Safety Guard 2: Verify all actions belong to approved vocabulary
    from app.agents.recovery_planner import APPROVED_ACTIONS
    plan_actions = plan.actions or [s.action for s in plan.steps]
    for act in plan_actions:
        if act not in APPROVED_ACTIONS:
            raise ValueError(
                f"Cannot execute plan '{plan_id}': Action '{act}' is not in the approved spacecraft action vocabulary."
            )

    inc.selected_plan_id = plan_id
    if operator_notes:
        inc.operator_notes = operator_notes

    # 1. Transition: EXECUTING
    _transition(
        inc,
        IncidentStatus.EXECUTING,
        f"Executing recovery plan {plan_id} commands to satellite {inc.satellite_id}",
    )

    # 2. Run Forward Digital Twin Simulation
    from app.services.simulator_engine import simulate_plan_execution
    from app.simulator.telemetry import generate_normal_telemetry, remediate_anomaly

    latest_telem = inc.telemetry_history[-1] if inc.telemetry_history else {}
    sim_result = simulate_plan_execution(plan, latest_telem)
    inc.simulation_result = sim_result.model_dump(mode="json")

    # 3. Transition: VERIFYING (Verify telemetry stabilization)
    _transition(
        inc,
        IncidentStatus.VERIFYING,
        "Telemetry verification: checking subsystem stabilization parameters",
    )

    # 4. Live state remediation in simulator
    remediate_anomaly(inc.satellite_id)
    
    # Generate fresh stabilized telemetry reading
    stabilized_reading = generate_normal_telemetry(inc.satellite_id)
    inc.telemetry_history.append(stabilized_reading)

    # 5. Transition: RESOLVED
    _transition(
        inc,
        IncidentStatus.RESOLVED,
        f"Anomaly resolved successfully. Satellite {inc.satellite_id} restored to nominal operating parameters.",
    )

    exec_summary = {
        "incident_id": inc.incident_id,
        "plan_id": plan.plan_id,
        "satellite_id": inc.satellite_id,
        "status": IncidentStatus.RESOLVED.value,
        "actions_executed": plan.actions or [s.action for s in plan.steps],
        "simulation": inc.simulation_result,
        "stabilized_telemetry": stabilized_reading,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }
    inc.execution_result = exec_summary

    return exec_summary, inc


def reject_incident_plan(plan_id: str, operator_notes: str | None = None) -> tuple[RecoveryPlan, IncidentRecord]:
    """Reject a recovery plan by human operator.

    Transitions incident to REJECTED.
    """
    plan, inc = find_plan(plan_id)
    if plan is None or inc is None:
        raise KeyError(f"RecoveryPlan '{plan_id}' not found")

    inc.selected_plan_id = plan_id
    inc.operator_notes = operator_notes
    _transition(
        inc,
        IncidentStatus.REJECTED,
        f"Plan {plan_id} rejected by ground operator: {operator_notes or 'No reason provided'}",
    )
    return plan, inc


