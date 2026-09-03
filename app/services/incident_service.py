"""Incident Lifecycle & Workflow Service."""

from typing import Dict, Any, Optional
from app.repositories.incident_repo import IncidentRepository
from app.repositories.recovery_repo import RecoveryRepository
from app.repositories.audit_repo import AuditRepository
from app.services.validation_service import ValidationService, SafetyGateError

VALID_TRANSITIONS = {
    "DETECTED": ["INVESTIGATING"],
    "INVESTIGATING": ["DIAGNOSED", "FAILED"],
    "DIAGNOSED": ["PLANNING", "FAILED"],
    "PLANNING": ["VALIDATING", "FAILED"],
    "VALIDATING": ["APPROVED", "REJECTED", "FAILED"],
    "REJECTED": ["PLANNING", "FAILED"],  # Can return to planning for safer alternative
    "APPROVED": ["EXECUTING", "FAILED"],
    "EXECUTING": ["VERIFYING", "FAILED"],
    "VERIFYING": ["RESOLVED", "FAILED"],
    "RESOLVED": [],
    "FAILED": []
}


class InvalidStateTransitionError(Exception):
    pass


class IncidentService:

    @classmethod
    def transition_state(
        cls,
        incident_id: str,
        target_state: str,
        actor: str = "SYSTEM",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transitions an incident along its lifecycle sequence.
        Rejects invalid transitions and logs an immutable audit event.
        """
        incident = IncidentRepository.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        current_state = incident["state"]
        allowed = VALID_TRANSITIONS.get(current_state, [])

        if target_state not in allowed:
            raise InvalidStateTransitionError(
                f"Invalid transition from {current_state} to {target_state}. Allowed: {allowed}"
            )

        updated = IncidentRepository.update_incident_state(incident_id, target_state, resolution_code=notes)

        # Map target state to valid audit event_type per Roadmap constraint
        event_type_map = {
            "DETECTED": "INCIDENT_OPENED",
            "INVESTIGATING": "AGENT_STARTED",
            "DIAGNOSED": "AGENT_COMPLETED",
            "PLANNING": "PLAN_GENERATED",
            "VALIDATING": "VALIDATION_COMPLETED",
            "APPROVED": "PLAN_APPROVED",
            "REJECTED": "PLAN_REJECTED",
            "EXECUTING": "COMMAND_EXECUTED",
            "VERIFYING": "OUTCOME_VERIFIED",
            "RESOLVED": "INCIDENT_RESOLVED",
            "FAILED": "INCIDENT_RESOLVED"
        }
        event_type = event_type_map.get(target_state, "MANUAL_OVERRIDE")

        # Log transition audit event
        AuditRepository.log_audit_event(
            incident_id=incident_id,
            event_type=event_type,
            actor=actor,
            payload={
                "from_state": current_state,
                "to_state": target_state,
                "notes": notes
            }
        )
        return updated

    @classmethod
    def approve_plan(cls, incident_id: str, plan_id: str, authorizer: str = "OPERATOR") -> Dict[str, Any]:
        """
        Approves a plan ONLY IF safety validation passed.
        Enforces: Recovery Plan -> Safety Validation -> Approval
        """
        validation = RecoveryRepository.get_validation(plan_id)
        if not validation or validation.get("status") != "PASSED":
            raise SafetyGateError(f"Cannot approve plan {plan_id}: Safety validation not passed!")

        # Update incident to point to current plan
        IncidentRepository.set_current_plan(incident_id, plan_id)

        # Transition incident to APPROVED (automatically logs PLAN_APPROVED event)
        cls.transition_state(incident_id, "APPROVED", actor=authorizer, notes=f"Plan {plan_id} approved")
        return {"status": "APPROVED", "plan_id": plan_id}

    @classmethod
    def execute_plan(
        cls,
        incident_id: str,
        plan_id: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes an approved plan on the simulator.
        Enforces: Approval -> Execution -> Verification
        """
        incident = IncidentRepository.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        if incident["state"] != "APPROVED":
            raise SafetyGateError(
                f"Cannot execute plan: Incident is in state {incident['state']}, expected APPROVED."
            )

        # Idempotency check: verify plan has not already been executed
        existing_exec = RecoveryRepository.get_execution(plan_id)
        if existing_exec and existing_exec.get("status") == "SUCCESS":
            raise SafetyGateError(f"Idempotency violation: Plan {plan_id} has already been executed successfully.")

        # Transition to EXECUTING
        cls.transition_state(incident_id, "EXECUTING", actor="SIMULATOR")

        plan = RecoveryRepository.get_recovery_plan(plan_id)
        actions = plan.get("actions", {}).get("actions", [])

        # Record command execution
        exec_record = RecoveryRepository.save_command_execution(
            plan_id=plan_id,
            status="SUCCESS",
            command={"actions_count": len(actions), "actions": actions},
            before_state=before_state,
            after_state=after_state
        )

        AuditRepository.log_audit_event(
            incident_id=incident_id,
            event_type="COMMAND_EXECUTED",
            actor="SIMULATOR",
            payload={"execution_id": exec_record["id"], "plan_id": plan_id}
        )

        # Transition to VERIFYING
        cls.transition_state(incident_id, "VERIFYING", actor="SIMULATOR")

        return exec_record

    @classmethod
    def verify_outcome(
        cls,
        incident_id: str,
        metric: str,
        observed_value: float,
        target_max: Optional[float] = None,
        target_min: Optional[float] = None,
        resolution_code: str = "AUTONOMOUS_RECOVERY_VERIFIED"
    ) -> Dict[str, Any]:
        """
        Step 6: Outcome verification comparing post-execution telemetry against targets.
        If verified: transitions VERIFYING -> RESOLVED.
        If failed: transitions VERIFYING -> FAILED.
        """
        incident = IncidentRepository.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        if incident["state"] != "VERIFYING":
            raise ValueError(f"Incident is in state {incident['state']}, expected VERIFYING.")

        success = True
        failure_reasons = []

        if target_max is not None and observed_value > target_max:
            success = False
            failure_reasons.append(f"{metric} observed {observed_value} exceeds target max {target_max}")

        if target_min is not None and observed_value < target_min:
            success = False
            failure_reasons.append(f"{metric} observed {observed_value} below target min {target_min}")

        target_state = "RESOLVED" if success else "FAILED"
        res_code = resolution_code if success else f"RECOVERY_VERIFICATION_FAILED: {'; '.join(failure_reasons)}"

        # Log OUTCOME_VERIFIED audit event
        AuditRepository.log_audit_event(
            incident_id=incident_id,
            event_type="OUTCOME_VERIFIED",
            actor="EVALUATOR",
            payload={
                "metric": metric,
                "observed_value": observed_value,
                "target_min": target_min,
                "target_max": target_max,
                "verified": success,
                "reasons": failure_reasons
            }
        )

        # Transition to terminal state (RESOLVED or FAILED)
        updated = cls.transition_state(
            incident_id=incident_id,
            target_state=target_state,
            actor="EVALUATOR",
            notes=res_code
        )

        return {
            "status": target_state,
            "verified": success,
            "metric": metric,
            "observed_value": observed_value,
            "resolution_code": res_code,
            "incident": updated
        }
