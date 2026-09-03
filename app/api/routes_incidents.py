"""Incident, Multi-Agent & Recovery API Routes."""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from app.schemas.incident import Anomaly, AnomalyCreate, Incident, IncidentCreate, IncidentStateTransition
from app.schemas.agent import AgentRun, AgentRunCreate
from app.schemas.recovery import RecoveryPlan, RecoveryPlanCreate, Validation, CommandExecution
from app.schemas.audit import AuditEvent
from app.repositories.incident_repo import IncidentRepository
from app.repositories.agent_repo import AgentRepository
from app.repositories.recovery_repo import RecoveryRepository
from app.repositories.audit_repo import AuditRepository
from app.services.incident_service import IncidentService, InvalidStateTransitionError, SafetyGateError
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/api/incidents", tags=["Incidents & Multi-Agent"])


@router.post("/anomalies", response_model=Anomaly)
def create_anomaly(payload: AnomalyCreate):
    """Persists a detected anomaly with its forensic telemetry evidence."""
    return IncidentRepository.create_anomaly(
        satellite_id=payload.satellite_id,
        subsystem_id=payload.subsystem_id,
        type=payload.type,
        severity=payload.severity,
        confidence=payload.confidence,
        evidence=payload.evidence
    )


@router.post("", response_model=Incident)
def create_incident(payload: IncidentCreate):
    """Opens a new incident case in state DETECTED and logs an audit event."""
    inc = IncidentRepository.create_incident(
        satellite_id=payload.satellite_id,
        title=payload.title,
        priority=payload.priority,
        severity=payload.severity,
        confidence=payload.confidence,
        primary_hypothesis=payload.primary_hypothesis,
        anomaly_id=payload.anomaly_id
    )
    AuditRepository.log_audit_event(
        incident_id=inc["id"],
        event_type="INCIDENT_OPENED",
        actor="DETECTOR",
        payload={"title": payload.title, "priority": payload.priority, "severity": payload.severity}
    )
    return inc


@router.get("/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    inc = IncidentRepository.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@router.post("/{incident_id}/transition", response_model=Incident)
def transition_incident_state(incident_id: str, payload: IncidentStateTransition):
    """Transitions incident lifecycle state, verifying valid sequence."""
    try:
        return IncidentService.transition_state(
            incident_id=incident_id,
            target_state=payload.target_state,
            actor=payload.actor,
            notes=payload.notes
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{incident_id}/context")
def get_incident_context(incident_id: str):
    """AI/ML Contract: Pre-aggregated structured incident context for LLMs."""
    ctx = IncidentRepository.build_incident_context(incident_id)
    if "error" in ctx:
        raise HTTPException(status_code=404, detail=ctx["error"])
    return ctx


@router.post("/{incident_id}/agent-runs", response_model=AgentRun)
def save_agent_run(incident_id: str, payload: AgentRunCreate):
    """AI/ML Contract: Persists agent execution trace, prompt input, and structured output."""
    run = AgentRepository.save_agent_run(
        incident_id=incident_id,
        agent_name=payload.agent_name,
        input_data=payload.input,
        output_data=payload.output,
        confidence=payload.confidence,
        status=payload.status
    )
    AuditRepository.log_audit_event(
        incident_id=incident_id,
        event_type="AGENT_COMPLETED",
        actor=payload.agent_name.upper(),
        payload={"run_id": run["id"], "confidence": payload.confidence}
    )
    return run


@router.get("/{incident_id}/agent-runs", response_model=List[AgentRun])
def get_agent_runs(incident_id: str):
    """Returns chronological multi-agent reasoning steps for operator timeline."""
    return AgentRepository.get_agent_runs(incident_id)


@router.get("/{incident_id}/diagnosis")
def get_latest_diagnosis(incident_id: str):
    diag = AgentRepository.get_latest_diagnosis(incident_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return diag


@router.post("/{incident_id}/plans", response_model=RecoveryPlan)
def create_recovery_plan(incident_id: str, payload: RecoveryPlanCreate):
    """Saves candidate recovery plan produced by planner agent."""
    plan = RecoveryRepository.create_recovery_plan(
        incident_id=incident_id,
        version=payload.version,
        rationale=payload.rationale,
        actions=payload.actions.model_dump(),
        risk_level=payload.risk_level
    )
    AuditRepository.log_audit_event(
        incident_id=incident_id,
        event_type="PLAN_GENERATED",
        actor="PLANNER",
        payload={"plan_id": plan["id"], "version": payload.version, "risk_level": payload.risk_level}
    )
    return plan


@router.get("/{incident_id}/plans", response_model=List[RecoveryPlan])
def get_recovery_plans(incident_id: str):
    return RecoveryRepository.get_recovery_plans(incident_id)


@router.post("/{incident_id}/plans/{plan_id}/validate", response_model=Validation)
def validate_plan(incident_id: str, plan_id: str):
    """Evaluates plan against deterministic safety rules."""
    try:
        return ValidationService.validate_plan(incident_id=incident_id, plan_id=plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{incident_id}/plans/{plan_id}/approve")
def approve_plan(incident_id: str, plan_id: str, authorizer: str = Body("OPERATOR", embed=True)):
    """Approves plan if validation passed, locking transition to APPROVED."""
    try:
        return IncidentService.approve_plan(incident_id=incident_id, plan_id=plan_id, authorizer=authorizer)
    except SafetyGateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, InvalidStateTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{incident_id}/plans/{plan_id}/execute", response_model=CommandExecution)
def execute_plan(
    incident_id: str,
    plan_id: str,
    payload: Dict[str, Any] = Body(...)
):
    """Executes approved plan on spacecraft simulator and records telemetry before/after state."""
    before_state = payload.get("before_state", {})
    after_state = payload.get("after_state", {})
    try:
        return IncidentService.execute_plan(
            incident_id=incident_id,
            plan_id=plan_id,
            before_state=before_state,
            after_state=after_state
        )
    except SafetyGateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{incident_id}/audit", response_model=List[AuditEvent])
def get_incident_audit_trail(incident_id: str):
    """Returns append-only audit event timeline for complete forensic reconstruction."""
    return AuditRepository.get_audit_events(incident_id)


@router.post("/{incident_id}/verify-outcome")
def verify_incident_outcome(
    incident_id: str,
    payload: Dict[str, Any] = Body(...)
):
    """
    Step 6: Outcome verification comparing post-execution telemetry against targets.
    Transitions incident to RESOLVED or FAILED and records OUTCOME_VERIFIED event.
    """
    metric = payload.get("metric")
    observed_value = payload.get("observed_value")
    target_max = payload.get("target_max")
    target_min = payload.get("target_min")
    resolution_code = payload.get("resolution_code", "AUTONOMOUS_RECOVERY_VERIFIED")

    if not metric or observed_value is None:
        raise HTTPException(status_code=400, detail="metric and observed_value are required")

    try:
        return IncidentService.verify_outcome(
            incident_id=incident_id,
            metric=metric,
            observed_value=float(observed_value),
            target_max=float(target_max) if target_max is not None else None,
            target_min=float(target_min) if target_min is not None else None,
            resolution_code=resolution_code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
