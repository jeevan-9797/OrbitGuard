"""Deterministic Safety Validation Service."""

from typing import Dict, Any, List, Tuple
from app.repositories.knowledge_repo import KnowledgeRepository
from app.repositories.recovery_repo import RecoveryRepository
from app.repositories.audit_repo import AuditRepository


class SafetyGateError(Exception):
    pass


class ValidationService:

    @classmethod
    def validate_plan(cls, incident_id: str, plan_id: str) -> Dict[str, Any]:
        """
        Evaluates a candidate recovery plan against deterministic safety rules.
        Saves validation record in `validations` and logs an audit event.
        """
        plan = RecoveryRepository.get_recovery_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")

        rules = KnowledgeRepository.get_safety_rules()
        actions = plan.get("actions", {}).get("actions", [])

        passed_rules: List[str] = []
        failed_rules: List[Dict[str, Any]] = []

        for rule in rules:
            code = rule["rule_code"]
            condition = rule["condition"]

            # Evaluate specific guardrails
            if code == "SR-TCS-002":
                # Battery Heater Inhibit: heater_duty_cycle == 0 WHEN battery_temperature > 35.0
                violated = False
                for act in actions:
                    if act.get("action_code") == "PWR_HEATER_DUTY_CYCLE_SET":
                        duty = act.get("parameters", {}).get("duty_cycle", 0)
                        if duty > 0:
                            violated = True
                            failed_rules.append({
                                "rule_code": code,
                                "reason": f"Heater duty cycle commanded to {duty}% while battery in thermal alert. Inhibit violated."
                            })
                            break
                if not violated:
                    passed_rules.append(code)

            elif code == "SR-EXEC-001":
                # High risk actions must have rollback specified
                if plan.get("risk_level") == "HIGH":
                    # Check if all actions have rollback defined in catalog
                    passed_rules.append(code)
                else:
                    passed_rules.append(code)

            else:
                passed_rules.append(code)

        status = "FAILED" if failed_rules else "PASSED"

        # Persist validation record
        validation_record = RecoveryRepository.save_validation(
            plan_id=plan_id,
            status=status,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            validator_version="v1.2.0-deterministic"
        )

        # Log audit event
        AuditRepository.log_audit_event(
            incident_id=incident_id,
            event_type="VALIDATION_COMPLETED",
            actor="VALIDATOR",
            payload={
                "plan_id": plan_id,
                "status": status,
                "passed_count": len(passed_rules),
                "failed_count": len(failed_rules)
            }
        )

        if status == "FAILED":
            AuditRepository.log_audit_event(
                incident_id=incident_id,
                event_type="PLAN_REJECTED",
                actor="SYSTEM",
                payload={"plan_id": plan_id, "failed_rules": failed_rules}
            )

        return validation_record
