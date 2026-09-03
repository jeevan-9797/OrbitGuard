"""
Deterministic Safety Validator and Rule Engine for OrbitGuard.

The validator evaluates recovery plans using explicit action-sequencing
rules and only makes telemetry claims when the corresponding telemetry
is actually available.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.recovery import RecoveryPlan
from app.schemas.validation import (
    ValidationCheck,
    ValidationResult,
)


logger = logging.getLogger(__name__)


# ============================================================
# SAFETY CONSTANTS
# ============================================================

WHEEL_NOMINAL_CENTER = 3000.0

WHEEL_JITTER_SAFETY_LIMIT = 400.0

BATTERY_VOLTAGE_LOW_THRESHOLD = 26.0

BATTERY_SOC_MIN_THRESHOLD = 30.0


# ============================================================
# TELEMETRY EXTRACTION
# ============================================================

def _extract_metric_value(
    telemetry: dict[str, Any],
    metric_name: str,
) -> float | None:

    if not telemetry:
        return None

    metrics = telemetry.get(
        "metrics",
        telemetry,
    )

    if not isinstance(metrics, dict):
        return None

    item = metrics.get(
        metric_name
    )

    if isinstance(item, dict):

        if "value" in item:

            try:
                return float(
                    item["value"]
                )

            except (
                TypeError,
                ValueError,
            ):
                return None

    if isinstance(
        item,
        (int, float),
    ) and not isinstance(
        item,
        bool,
    ):

        return float(item)

    return None


# ============================================================
# VALIDATION
# ============================================================

def validate_recovery_plan(
    plan: RecoveryPlan,
    current_telemetry: dict[str, Any] | None = None,
    subsystem_graph: Any = None,
) -> ValidationResult:

    telemetry = (
        current_telemetry
        or {}
    )

    checks: list[ValidationCheck] = []

    violations: list[str] = []

    warnings: list[str] = []

    # --------------------------------------------------------
    # Extract action sequence
    # --------------------------------------------------------

    action_sequence: list[str] = []

    if getattr(
        plan,
        "steps",
        None,
    ):

        steps = sorted(
            plan.steps,
            key=lambda step: getattr(
                step,
                "step_number",
                0,
            ),
        )

        for step in steps:

            action = getattr(
                step,
                "action",
                None,
            )

            if action:
                action_sequence.append(
                    action
                )

    elif getattr(
        plan,
        "actions",
        None,
    ):

        action_sequence = list(
            plan.actions
        )

    # --------------------------------------------------------
    # Constraint 1:
    # Thermal safe mode sequencing
    # --------------------------------------------------------

    if "ENTER_SAFE_THERMAL_MODE" in action_sequence:

        thermal_index = (
            action_sequence.index(
                "ENTER_SAFE_THERMAL_MODE"
            )
        )

        if (
            "REDUCE_PAYLOAD_LOAD"
            not in action_sequence[:thermal_index]
        ):

            message = (
                "Constraint 1 violation: "
                "REDUCE_PAYLOAD_LOAD must be "
                "sequenced before "
                "ENTER_SAFE_THERMAL_MODE."
            )

            violations.append(
                message
            )

            checks.append(
                ValidationCheck(
                    check_name=(
                        "thermal_action_sequence"
                    ),
                    passed=False,
                    message=message,
                )
            )

        else:

            message = (
                "Thermal action sequence is "
                "consistent with the required "
                "payload-load reduction ordering."
            )

            checks.append(
                ValidationCheck(
                    check_name=(
                        "thermal_action_sequence"
                    ),
                    passed=True,
                    message=message,
                )
            )

    else:

        message = (
            "Plan does not command "
            "ENTER_SAFE_THERMAL_MODE; "
            "thermal sequencing constraint "
            "was not triggered."
        )

        checks.append(
            ValidationCheck(
                check_name=(
                    "thermal_action_sequence"
                ),
                passed=True,
                message=message,
            )
        )

    # --------------------------------------------------------
    # Constraint 2:
    # ADCS telemetry-aware validation
    # --------------------------------------------------------

    wheel_speed = _extract_metric_value(
        telemetry,
        "wheel_speed",
    )

    attitude_error = _extract_metric_value(
        telemetry,
        "attitude_error",
    )

    wheel_deviation = None

    if wheel_speed is not None:

        wheel_deviation = abs(
            wheel_speed
            - WHEEL_NOMINAL_CENTER
        )

    adcs_unstable = (
        (
            wheel_deviation is not None
            and wheel_deviation
            > WHEEL_JITTER_SAFETY_LIMIT
        )
        or
        (
            attitude_error is not None
            and attitude_error
            > 0.3
        )
    )

    if adcs_unstable:

        if not action_sequence:

            message = (
                "ADCS instability indicators "
                "are present, but the plan contains "
                "no actions to evaluate."
            )

            violations.append(
                message
            )

            checks.append(
                ValidationCheck(
                    check_name="adcs_stability",
                    passed=False,
                    message=message,
                )
            )

        elif action_sequence[0] not in {
            "SWITCH_REDUNDANT_SENSOR",
            "REDUCE_MANEUVER_ACTIVITY",
        }:

            message = (
                "ADCS telemetry indicates "
                "instability, but the plan does "
                "not begin with an ADCS "
                "stabilization action."
            )

            violations.append(
                message
            )

            checks.append(
                ValidationCheck(
                    check_name="adcs_stability",
                    passed=False,
                    message=message,
                )
            )

        else:

            message = (
                "ADCS telemetry indicates "
                "instability and the plan begins "
                "with an approved stabilization action."
            )

            checks.append(
                ValidationCheck(
                    check_name="adcs_stability",
                    passed=True,
                    message=message,
                )
            )

    else:

        evidence_parts = []

        if wheel_speed is not None:

            evidence_parts.append(
                f"wheel speed {wheel_speed:.1f} RPM"
            )

        if attitude_error is not None:

            evidence_parts.append(
                f"attitude error "
                f"{attitude_error:.3f} deg"
            )

        if evidence_parts:

            message = (
                "ADCS telemetry does not indicate "
                "a configured instability condition: "
                + ", ".join(evidence_parts)
                + "."
            )

        else:

            message = (
                "No wheel-speed or attitude-error "
                "telemetry was supplied; no ADCS "
                "stability claim was made."
            )

            warnings.append(
                message
            )

        checks.append(
            ValidationCheck(
                check_name="adcs_stability",
                passed=True,
                message=message,
            )
        )

    # --------------------------------------------------------
    # Constraint 3:
    # Battery telemetry-aware validation
    # --------------------------------------------------------

    battery_voltage = _extract_metric_value(
        telemetry,
        "battery_voltage",
    )

    battery_soc = _extract_metric_value(
        telemetry,
        "battery_soc",
    )

    battery_warning = False

    if (
        battery_voltage is not None
        and battery_voltage
        < BATTERY_VOLTAGE_LOW_THRESHOLD
    ):

        battery_warning = True

        message = (
            f"Battery voltage telemetry is "
            f"{battery_voltage:.2f} V, below the "
            f"configured safety boundary of "
            f"{BATTERY_VOLTAGE_LOW_THRESHOLD:.1f} V."
        )

        warnings.append(
            message
        )

        checks.append(
            ValidationCheck(
                check_name="battery_margin",
                passed=True,
                message=message,
            )
        )

    elif (
        battery_soc is not None
        and battery_soc
        < BATTERY_SOC_MIN_THRESHOLD
    ):

        battery_warning = True

        message = (
            f"Battery SoC telemetry is "
            f"{battery_soc:.1f}%, below the "
            f"configured minimum of "
            f"{BATTERY_SOC_MIN_THRESHOLD:.1f}%."
        )

        warnings.append(
            message
        )

        checks.append(
            ValidationCheck(
                check_name="battery_margin",
                passed=True,
                message=message,
            )
        )

    elif battery_voltage is not None:

        message = (
            f"Battery voltage telemetry is "
            f"{battery_voltage:.2f} V, at or above "
            f"the configured safety boundary of "
            f"{BATTERY_VOLTAGE_LOW_THRESHOLD:.1f} V."
        )

        checks.append(
            ValidationCheck(
                check_name="battery_margin",
                passed=True,
                message=message,
            )
        )

    elif battery_soc is not None:

        message = (
            f"Battery SoC telemetry is "
            f"{battery_soc:.1f}%, at or above "
            f"the configured minimum of "
            f"{BATTERY_SOC_MIN_THRESHOLD:.1f}%."
        )

        checks.append(
            ValidationCheck(
                check_name="battery_margin",
                passed=True,
                message=message,
            )
        )

    else:

        message = (
            "No battery voltage or battery SoC "
            "telemetry was supplied; no battery "
            "margin claim was made."
        )

        warnings.append(
            message
        )

        checks.append(
            ValidationCheck(
                check_name="battery_margin",
                passed=True,
                message=message,
            )
        )

    # --------------------------------------------------------
    # Constraint 4:
    # Rollback
    # --------------------------------------------------------

    has_plan_rollback = bool(
        (
            getattr(plan, "rollback_plan", None)
            and str(getattr(plan, "rollback_plan")).strip()
        )
        or (
            getattr(plan, "rollback", None)
            and str(getattr(plan, "rollback", "")).strip()
        )
    )

    has_step_rollback = any(
        bool(
            getattr(step, "rollback_action", None)
            and str(getattr(step, "rollback_action")).strip()
        )
        for step in getattr(plan, "steps", [])
    )

    rollback_defined = has_plan_rollback or has_step_rollback

    if rollback_defined:

        message = (
            "Contingency rollback procedures "
            "are defined for the proposed plan."
        )

        checks.append(
            ValidationCheck(
                check_name="rollback_defined",
                passed=True,
                message=message,
            )
        )

    else:

        message = (
            "No rollback procedure was supplied "
            "with the proposed plan."
        )

        warnings.append(
            message
        )

        checks.append(
            ValidationCheck(
                check_name="rollback_defined",
                passed=False,
                message=message,
            )
        )

    # --------------------------------------------------------
    # Safety score
    # --------------------------------------------------------

    safety_score = max(
        0.0,
        1.0
        - (
            len(violations)
            * 0.4
        )
        - (
            len(warnings)
            * 0.1
        ),
    )

    is_valid = (
        len(violations) == 0
    )

    is_safe = is_valid

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    return ValidationResult(
        validation_id=(
            f"VAL-{uuid.uuid4().hex[:8].upper()}"
        ),
        plan_id=plan.plan_id,
        is_valid=is_valid,
        is_safe=is_safe,
        violations=violations,
        warnings=warnings,
        checks=checks,
        safety_score=safety_score,
        validated_at=datetime.now(
            timezone.utc
        ),
    )