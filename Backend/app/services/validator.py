"""Deterministic Safety Validator and Rule Engine for OrbitGuard.

Evaluates candidate Recovery Plans against non-negotiable mission safety constraints,
spacecraft subsystem rules, and live telemetry boundaries.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.recovery import RecoveryPlan
from app.schemas.validation import ValidationCheck, ValidationResult

logger = logging.getLogger(__name__)

# Nominal metric boundaries
WHEEL_NOMINAL_CENTER = 3000.0  # RPM
WHEEL_JITTER_SAFETY_LIMIT = 400.0  # Max tolerable deviation before maneuvers rejected
BATTERY_VOLTAGE_LOW_THRESHOLD = 26.0  # V (corresponds to ~30% SoC)
BATTERY_SOC_MIN_THRESHOLD = 30.0  # %


def _extract_metric_value(telemetry: dict[str, Any], metric_name: str) -> float | None:
    """Helper to extract a metric value from various telemetry dictionary structures."""
    if not telemetry:
        return None
    # Check if nested under "metrics"
    metrics = telemetry.get("metrics", telemetry)
    if isinstance(metrics, dict):
        item = metrics.get(metric_name)
        if isinstance(item, dict) and "value" in item:
            return float(item["value"])
        if isinstance(item, (int, float)):
            return float(item)
    return None


def validate_recovery_plan(
    plan: RecoveryPlan,
    current_telemetry: dict[str, Any] | None = None,
    subsystem_graph: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate a candidate recovery plan against deterministic safety rules.

    Non-negotiable constraints:
    - Constraint 1: Reject ENTER_SAFE_THERMAL_MODE if payload power is active without prior REDUCE_PAYLOAD_LOAD.
    - Constraint 2: Reject maneuvers if reaction wheel speed variance is high (unstable ADCS).
    - Constraint 3: Flag warning if battery state of charge (SoC) < 30%.
    """
    telemetry = current_telemetry or {}
    checks: list[ValidationCheck] = []
    violations: list[str] = []
    warnings: list[str] = []

    # Gather ordered list of actions from steps or actions list
    action_sequence: list[str] = []
    if plan.steps:
        # Sort by step_number
        sorted_steps = sorted(plan.steps, key=lambda s: s.step_number)
        action_sequence = [s.action for s in sorted_steps]
    else:
        action_sequence = list(plan.actions)

    # ── Constraint 1: Thermal Mode vs Payload Power ──────────────────────────
    # Reject ENTER_SAFE_THERMAL_MODE if payload is active without prior REDUCE_PAYLOAD_LOAD
    if "ENTER_SAFE_THERMAL_MODE" in action_sequence:
        thermal_idx = action_sequence.index("ENTER_SAFE_THERMAL_MODE")
        # Check if REDUCE_PAYLOAD_LOAD occurs strictly BEFORE ENTER_SAFE_THERMAL_MODE
        has_prior_payload_reduction = False
        for i in range(thermal_idx):
            if action_sequence[i] == "REDUCE_PAYLOAD_LOAD":
                has_prior_payload_reduction = True
                break

        if not has_prior_payload_reduction:
            msg = "Constraint 1 Violation: ENTER_SAFE_THERMAL_MODE cannot be initiated while payload instruments remain energized. Prior REDUCE_PAYLOAD_LOAD step is required."
            violations.append(msg)
            checks.append(
                ValidationCheck(
                    check_name="Constraint 1: Thermal Mode Payload Interlock",
                    passed=False,
                    message=msg,
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    check_name="Constraint 1: Thermal Mode Payload Interlock",
                    passed=True,
                    message="Payload load reduction is sequenced prior to thermal safe mode.",
                )
            )
    else:
        checks.append(
            ValidationCheck(
                check_name="Constraint 1: Thermal Mode Payload Interlock",
                passed=True,
                message="Plan does not command thermal safe mode.",
            )
        )

    # ── Constraint 2: ADCS Wheel Stability Interlock ─────────────────────────
    # Reject maneuvers if wheel speed variance is high unless stabilizing first
    wheel_speed = _extract_metric_value(telemetry, "wheel_speed")
    wheel_deviation = abs(wheel_speed - WHEEL_NOMINAL_CENTER) if wheel_speed is not None else 0.0
    attitude_error = _extract_metric_value(telemetry, "attitude_error") or 0.0

    is_adcs_unstable = wheel_deviation > WHEEL_JITTER_SAFETY_LIMIT or attitude_error > 0.3

    if is_adcs_unstable:
        # If ADCS is unstable, any high-rate dynamic slew or un-safed activity is prohibited.
        # Plan MUST command stabilization / redundant sensor switch first.
        stabilization_actions = {"SWITCH_REDUNDANT_SENSOR", "REDUCE_MANEUVER_ACTIVITY"}
        first_action = action_sequence[0] if action_sequence else None

        if not first_action or first_action not in stabilization_actions:
            msg = f"Constraint 2 Violation: Reaction wheel jitter ({wheel_deviation:.1f} RPM deviation) or attitude error ({attitude_error:.2f}°) is high. Maneuvers are prohibited until ADCS stabilization or redundant sensor switch is sequenced as initial step."
            violations.append(msg)
            checks.append(
                ValidationCheck(
                    check_name="Constraint 2: ADCS Wheel Stability Interlock",
                    passed=False,
                    message=msg,
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    check_name="Constraint 2: ADCS Wheel Stability Interlock",
                    passed=True,
                    message="Plan appropriately sequences ADCS stabilization/backup switch as first action during wheel instability.",
                )
            )
    else:
        checks.append(
            ValidationCheck(
                check_name="Constraint 2: ADCS Wheel Stability Interlock",
                passed=True,
                message="Reaction wheel dynamics within safe operational tolerances.",
            )
        )

    # ── Constraint 3: Battery State of Charge (SoC) Warning ───────────────────
    # Flag warning if battery SoC < 30% or battery voltage is low
    battery_volt = _extract_metric_value(telemetry, "battery_voltage")
    battery_soc = _extract_metric_value(telemetry, "battery_soc")

    is_low_soc = (
        (battery_soc is not None and battery_soc < BATTERY_SOC_MIN_THRESHOLD)
        or (battery_volt is not None and battery_volt < BATTERY_VOLTAGE_LOW_THRESHOLD)
    )

    if is_low_soc:
        soc_display = f"{battery_soc:.1f}%" if battery_soc is not None else f"{battery_volt:.2f}V"
        msg = f"Constraint 3 Warning: Low battery State of Charge detected ({soc_display}). High-power recovery operations should be closely monitored."
        warnings.append(msg)
        checks.append(
            ValidationCheck(
                check_name="Constraint 3: Battery SoC Safety Margin",
                passed=True,  # Advisory warning, not hard rejection
                message=msg,
            )
        )
    else:
        checks.append(
            ValidationCheck(
                check_name="Constraint 3: Battery SoC Safety Margin",
                passed=True,
                message="Battery voltage and energy reserve exceed minimum safety margins.",
            )
        )

    # ── Check 4: Rollback Strategy Completeness ──────────────────────────────
    has_rollback = bool(plan.rollback_plan or any(s.rollback_action for s in plan.steps))
    if not has_rollback:
        msg = "Advisory: Plan lacks explicit rollback procedures for automated recovery reversion."
        warnings.append(msg)
        checks.append(
            ValidationCheck(
                check_name="Check 4: Contingency Rollback Definition",
                passed=False,
                message=msg,
            )
        )
    else:
        checks.append(
            ValidationCheck(
                check_name="Check 4: Contingency Rollback Definition",
                passed=True,
                message="Contingency rollback procedures are defined.",
            )
        )

    # ── Compute Safety Score & Final Verdict ──────────────────────────────────
    is_safe = len(violations) == 0
    is_valid = is_safe

    # Score calculation: 1.0 base, -0.4 per violation, -0.1 per warning
    calculated_score = max(0.0, 1.0 - (len(violations) * 0.4) - (len(warnings) * 0.1))

    result = ValidationResult(
        validation_id=f"VAL-{uuid.uuid4().hex[:8].upper()}",
        plan_id=plan.plan_id,
        is_valid=is_valid,
        is_safe=is_safe,
        violations=violations,
        warnings=warnings,
        checks=checks,
        safety_score=round(calculated_score, 2),
        validated_at=datetime.now(timezone.utc),
    )

    return result
