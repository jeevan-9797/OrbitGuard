"""Recovery Planner Agent for OrbitGuard spacecraft incident remediation.

Generates ranked candidate recovery plans restricted strictly to an approved
action command vocabulary, with evidence-grounded prerequisites, expected
effects, and rollback guidance.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.llm import call_llm_structured
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.recovery import RecoveryPlan, RecoveryStep, RiskLevel

logger = logging.getLogger(__name__)


# ── Approved Action Vocabulary ───────────────────────────────────────────────

APPROVED_ACTIONS = [
    "REDUCE_PAYLOAD_LOAD",
    "ENTER_SAFE_THERMAL_MODE",
    "SWITCH_REDUNDANT_SENSOR",
    "REDUCE_MANEUVER_ACTIVITY",
    "SWITCH_COMM_PROFILE",
]

ACTION_DESCRIPTIONS = {
    "REDUCE_PAYLOAD_LOAD": (
        "Reduce non-essential payload activity to lower subsystem load. "
        "Do not assume a specific payload, power reduction, or thermal reduction."
    ),
    "ENTER_SAFE_THERMAL_MODE": (
        "Enter the approved spacecraft thermal protection mode. "
        "Do not assume a specific attitude change, solar geometry, or temperature target."
    ),
    "SWITCH_REDUNDANT_SENSOR": (
        "Switch to an approved redundant sensor or control channel. "
        "Do not assume a specific backup component is healthy unless telemetry verifies it."
    ),
    "REDUCE_MANEUVER_ACTIVITY": (
        "Reduce or inhibit non-essential spacecraft maneuver activity. "
        "Do not assume a specific slew rate, attitude state, or actuator condition."
    ),
    "SWITCH_COMM_PROFILE": (
        "Switch to an approved lower-resource communications profile. "
        "Do not assume a specific transmitter power, data rate, or link margin."
    ),
}


# ── Strict Evidence-Grounding Prompt ─────────────────────────────────────────

RECOVERY_PLANNER_SYSTEM_PROMPT = """
You are the OrbitGuard Lead Satellite Recovery Planner Agent.

Your role is to generate precise, executable recovery plans based only on
verified diagnostic hypotheses and telemetry supplied in the input.

STRICT EVIDENCE-GROUNDING & SAFETY RULES:

1. DO NOT fabricate or assume numeric telemetry values.
   Never invent values such as temperature limits, battery state of charge,
   voltage thresholds, power reductions, transmitter power, attitude angles,
   slew rates, timing thresholds, or sensor values.

2. Prerequisites and expected effects MUST be expressed using:
   - facts explicitly present in the supplied telemetry,
   - relative or qualitative conditions,
   - conditional verification requirements,
   - or explicit references to telemetry that must be checked.

3. Do not claim that an unprovided telemetry value has already been measured.

4. If a prerequisite depends on missing telemetry, phrase it as a verification
   requirement. For example:
   "Verify battery telemetry is within nominal operating limits."
   Do NOT invent a numeric limit.

5. Expected outcomes must be qualitative or relative unless an exact baseline
   and target are explicitly provided in the input telemetry.

6. Do not claim a specific physical mechanism, hardware failure, orbital
   condition, attitude state, or subsystem state unless it is directly supported
   by the supplied evidence.

7. Use ONLY the approved operational action vocabulary supplied in the prompt.

8. Every step action MUST be one of the approved action commands.

9. Recovery plans must be conservative when diagnostic confidence is limited.

10. Rollback instructions must not contain fabricated numeric thresholds or
    unsupported spacecraft states.

11. AI-generated plans are candidate plans only. Deterministic safety
    validation remains authoritative.

12. Do not fabricate telemetry, historical events, verification results,
    hardware states, or operational conditions.
"""


# ── Deterministic Fallback Recovery Plans ────────────────────────────────────

def _fallback_battery_overheat_plans(
    diagnosis: DiagnosisResult,
) -> list[RecoveryPlan]:
    """Generate evidence-grounded fallback plans for thermal/EPS anomalies."""

    plan_1 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Thermal Load Reduction",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=[
            "REDUCE_PAYLOAD_LOAD",
            "ENTER_SAFE_THERMAL_MODE",
        ],
        preconditions=[
            "Telemetry streaming is active.",
            "Verify current battery and thermal telemetry before execution.",
        ],
        expected_effects=[
            "Reduce non-essential subsystem activity.",
            "Reduce thermal and operational load on the affected spacecraft systems.",
            "Monitor telemetry for stabilization after each recovery step.",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome=(
                    "Non-essential payload activity is reduced while telemetry "
                    "is monitored for a stabilizing response."
                ),
                rollback_action=(
                    "Restore nominal payload activity if telemetry indicates "
                    "the recovery action is not beneficial."
                ),
            ),
            RecoveryStep(
                step_number=2,
                action="ENTER_SAFE_THERMAL_MODE",
                subsystem="Thermal",
                expected_outcome=(
                    "The spacecraft enters the approved thermal protection "
                    "mode and thermal telemetry is monitored for stabilization."
                ),
                rollback_action=(
                    "Exit safe thermal mode and restore the previous approved "
                    "thermal configuration if validation indicates it is safe."
                ),
            ),
        ],
        risk_level=RiskLevel.LOW,
        risk_score=0.25,
        rollback_plan=(
            "Rollback the most recent recovery action if verified telemetry "
            "indicates degradation or if deterministic safety validation fails."
        ),
        estimated_duration_seconds=180,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    plan_2 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Conservative Power and Communications Reduction",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=[
            "REDUCE_PAYLOAD_LOAD",
            "SWITCH_COMM_PROFILE",
        ],
        preconditions=[
            "Telemetry streaming is active.",
            "Verify communications availability before changing the communications profile.",
        ],
        expected_effects=[
            "Reduce non-essential spacecraft resource usage.",
            "Reduce communications resource demand using the approved profile.",
            "Monitor battery and thermal telemetry for stabilization.",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome=(
                    "Non-essential payload activity is reduced and the "
                    "resulting telemetry response is monitored."
                ),
                rollback_action=(
                    "Restore nominal payload activity if verified telemetry "
                    "indicates an adverse response."
                ),
            ),
            RecoveryStep(
                step_number=2,
                action="SWITCH_COMM_PROFILE",
                subsystem="COMMS",
                expected_outcome=(
                    "The approved lower-resource communications profile is "
                    "activated while maintaining required telemetry."
                ),
                rollback_action=(
                    "Restore the previous approved communications profile "
                    "if link health or telemetry availability degrades."
                ),
            ),
        ],
        risk_level=RiskLevel.MEDIUM,
        risk_score=0.45,
        rollback_plan=(
            "Restore the previous communications and payload configuration "
            "if verified telemetry indicates degraded spacecraft or link performance."
        ),
        estimated_duration_seconds=300,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    return [plan_1, plan_2]


def _fallback_wheel_degradation_plans(
    diagnosis: DiagnosisResult,
) -> list[RecoveryPlan]:
    """Generate evidence-grounded fallback plans for ADCS anomalies."""

    plan_1 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="ADCS Activity Reduction and Redundancy Check",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=[
            "REDUCE_MANEUVER_ACTIVITY",
            "SWITCH_REDUNDANT_SENSOR",
        ],
        preconditions=[
            "Telemetry streaming is active.",
            "Verify the redundant ADCS channel before switching to it.",
        ],
        expected_effects=[
            "Reduce non-essential maneuver activity.",
            "Reduce unnecessary ADCS activity while diagnostic telemetry is collected.",
            "Use redundant sensing only after its health is verified.",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_MANEUVER_ACTIVITY",
                subsystem="ADCS",
                expected_outcome=(
                    "Non-essential maneuver activity is reduced while "
                    "attitude and wheel telemetry are monitored."
                ),
                rollback_action=(
                    "Restore the previous approved maneuver configuration "
                    "if telemetry indicates an adverse response."
                ),
            ),
            RecoveryStep(
                step_number=2,
                action="SWITCH_REDUNDANT_SENSOR",
                subsystem="ADCS",
                expected_outcome=(
                    "An approved redundant sensing/control channel is selected "
                    "after its health is verified."
                ),
                rollback_action=(
                    "Return to the previous approved sensing/control channel "
                    "if validation indicates degraded performance."
                ),
            ),
        ],
        risk_level=RiskLevel.LOW,
        risk_score=0.20,
        rollback_plan=(
            "Return to the previous approved ADCS configuration if the "
            "redundant channel fails deterministic safety validation."
        ),
        estimated_duration_seconds=240,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    plan_2 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Conservative ADCS Stabilization",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=[
            "REDUCE_MANEUVER_ACTIVITY",
            "REDUCE_PAYLOAD_LOAD",
        ],
        preconditions=[
            "Telemetry streaming is active.",
            "Verify current attitude and actuator telemetry before execution.",
        ],
        expected_effects=[
            "Reduce non-essential maneuver activity.",
            "Reduce operational load that could contribute to unnecessary spacecraft activity.",
            "Monitor attitude and actuator telemetry for stabilization.",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_MANEUVER_ACTIVITY",
                subsystem="ADCS",
                expected_outcome=(
                    "Non-essential maneuver activity is reduced and the "
                    "resulting attitude telemetry is monitored."
                ),
                rollback_action=(
                    "Restore the previous approved maneuver configuration "
                    "if validation indicates it is safe to do so."
                ),
            ),
            RecoveryStep(
                step_number=2,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="Payload",
                expected_outcome=(
                    "Non-essential payload activity is reduced while "
                    "ADCS telemetry is monitored."
                ),
                rollback_action=(
                    "Restore nominal payload activity if verified telemetry "
                    "indicates an adverse response."
                ),
            ),
        ],
        risk_level=RiskLevel.MEDIUM,
        risk_score=0.40,
        rollback_plan=(
            "Restore the previous approved ADCS and payload configuration "
            "if deterministic validation or telemetry monitoring indicates degradation."
        ),
        estimated_duration_seconds=150,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    return [plan_1, plan_2]


def _fallback_generic_plans(
    diagnosis: DiagnosisResult,
) -> list[RecoveryPlan]:
    """Generate a conservative generic recovery plan."""

    affected_subsystem = (
        diagnosis.affected_subsystems[0]
        if diagnosis.affected_subsystems
        else "Unknown"
    )

    return [
        RecoveryPlan(
            plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
            title="Conservative Standby and Diagnostic Isolation",
            diagnosis_id=diagnosis.diagnosis_id,
            satellite_id=diagnosis.satellite_id,
            actions=[
                "REDUCE_PAYLOAD_LOAD",
                "REDUCE_MANEUVER_ACTIVITY",
            ],
            preconditions=[
                "Telemetry streaming is active.",
                "Verify affected subsystem telemetry before execution.",
            ],
            expected_effects=[
                "Reduce non-essential spacecraft activity.",
                "Provide additional telemetry for diagnosis verification.",
            ],
            steps=[
                RecoveryStep(
                    step_number=1,
                    action="REDUCE_PAYLOAD_LOAD",
                    subsystem=affected_subsystem,
                    expected_outcome=(
                        "Reduce non-essential operational load while "
                        "monitoring the affected subsystem."
                    ),
                    rollback_action=(
                        "Restore nominal load if verified telemetry indicates "
                        "an adverse response."
                    ),
                ),
            ],
            risk_level=RiskLevel.LOW,
            risk_score=0.30,
            rollback_plan=(
                "Restore nominal operation after deterministic safety "
                "validation and telemetry verification."
            ),
            estimated_duration_seconds=120,
            requires_ground_approval=True,
            created_at=datetime.now(timezone.utc),
        )
    ]


def get_fallback_recovery_plans(
    diagnosis: DiagnosisResult,
) -> list[RecoveryPlan]:
    """Return deterministic candidate recovery plans based on diagnosis."""

    hypo = (
        diagnosis.primary_hypothesis
        + " "
        + (diagnosis.root_cause or "")
    ).lower()

    affected = [
        subsystem.upper()
        for subsystem in diagnosis.affected_subsystems
    ]

    if (
        "battery" in hypo
        or "thermal" in hypo
        or "temperature" in hypo
        or "EPS" in affected
    ):
        return _fallback_battery_overheat_plans(diagnosis)

    if (
        "wheel" in hypo
        or "attitude" in hypo
        or "ADCS" in affected
    ):
        return _fallback_wheel_degradation_plans(diagnosis)

    return _fallback_generic_plans(diagnosis)


# ── Recovery Planner Prompt & Execution ──────────────────────────────────────

async def generate_recovery_plans(
    diagnosis_result: DiagnosisResult,
    current_state: dict[str, Any] | None = None,
) -> list[RecoveryPlan]:
    """Generate 2-3 candidate recovery plans using the LLM.

    The LLM is restricted to the approved action vocabulary and strict
    evidence-grounding rules. Deterministic fallback plans are used if
    the LLM fails or returns insufficient valid plans.
    """
    from ai_ml.retrieval.retriever import retrieve_anomaly_knowledge
    subsys = diagnosis_result.affected_subsystems[0] if diagnosis_result.affected_subsystems else None
    retrieved = retrieve_anomaly_knowledge(
        anomaly_type=diagnosis_result.primary_hypothesis,
        subsystem=subsys,
    )
    retrieval_section = retrieved.format_for_prompt()

    prompt = f"""
Generate 2 or 3 distinct, ranked candidate Recovery Plans.

The plans must be based ONLY on the diagnosis evidence and spacecraft
telemetry supplied below.

### APPROVED ACTION VOCABULARY

{json.dumps(APPROVED_ACTIONS, indent=2)}

### ACTION DEFINITIONS

{json.dumps(ACTION_DESCRIPTIONS, indent=2)}

### DIAGNOSIS RESULT

Satellite:
{diagnosis_result.satellite_id}

Primary Hypothesis:
{diagnosis_result.primary_hypothesis}

Root Cause:
{diagnosis_result.root_cause}

Affected Subsystems:
{json.dumps(diagnosis_result.affected_subsystems, indent=2)}

Confidence:
{diagnosis_result.confidence}

Evidence:
{json.dumps(diagnosis_result.evidence, indent=2)}

Diagnostic Checks:
{json.dumps(diagnosis_result.checks, indent=2)}

### CURRENT SPACECRAFT STATE

{json.dumps(current_state or {}, indent=2)}

### RETRIEVED ADVISORY RUNBOOKS & HISTORICAL OPS (REFERENCE ONLY):

{retrieval_section}

### PLANNING REQUIREMENTS

- Every action MUST be from the approved action vocabulary.
- Every step action MUST be from the approved action vocabulary.
- Do NOT invent telemetry values.
- Do NOT invent thresholds.
- Do NOT invent spacecraft states.
- Do NOT invent orbital conditions.
- Do NOT invent hardware health states.
- Do NOT invent specific physical failure mechanisms.
- Do NOT claim a verification result unless it is present in the input.
- If information is missing, make it a verification prerequisite.
- Expected effects must be qualitative or relative unless the input explicitly
  provides a baseline and a target.
- Do not state unsupported numeric values in preconditions, expected effects,
  expected outcomes, rollback actions, or rollback plans.
- Keep the plan conservative when diagnosis confidence is limited.
- Recovery actions are candidate actions and remain subject to deterministic
  safety validation.

### REQUIRED JSON OUTPUT FORMAT

Return a JSON array containing 2 or 3 candidate plan objects:

[
  {{
    "title": "Strategy Title",
    "actions": [
      "REDUCE_PAYLOAD_LOAD"
    ],
    "preconditions": [
      "Telemetry streaming is active.",
      "Verify the required subsystem telemetry before execution."
    ],
    "expected_effects": [
      "Reduce non-essential subsystem activity.",
      "Monitor telemetry for stabilization."
    ],
    "risk_level": "low",
    "risk_score": 0.25,
    "rollback_plan": "Restore the previous approved configuration if verified telemetry indicates degradation.",
    "estimated_duration_seconds": 180,
    "requires_ground_approval": true,
    "steps": [
      {{
        "step_number": 1,
        "action": "REDUCE_PAYLOAD_LOAD",
        "subsystem": "EPS",
        "expected_outcome": "Reduce non-essential operational load while monitoring telemetry.",
        "rollback_action": "Restore the previous approved configuration if telemetry indicates an adverse response."
      }}
    ]
  }}
]

CRITICAL ACTION CONSTRAINT:

Every item in "actions" and every step's "action" MUST be EXACTLY one of:

REDUCE_PAYLOAD_LOAD
ENTER_SAFE_THERMAL_MODE
SWITCH_REDUNDANT_SENSOR
REDUCE_MANEUVER_ACTIVITY
SWITCH_COMM_PROFILE
"""

    try:
        data = await call_llm_structured(
            prompt=prompt,
            system_prompt=RECOVERY_PLANNER_SYSTEM_PROMPT,
            retries=1,
            timeout=12.0,
        )

        plans_raw = (
            data
            if isinstance(data, list)
            else data.get("plans", [])
            if isinstance(data, dict)
            else []
        )

        valid_plans: list[RecoveryPlan] = []

        for raw in plans_raw:
            if not isinstance(raw, dict):
                continue

            # Keep only approved actions.
            filtered_actions = [
                action
                for action in raw.get("actions", [])
                if action in APPROVED_ACTIONS
            ]

            if not filtered_actions:
                continue

            steps: list[RecoveryStep] = []

            for index, step in enumerate(
                raw.get("steps", []),
                start=1,
            ):
                if not isinstance(step, dict):
                    continue

                action = step.get("action")

                if action not in APPROVED_ACTIONS:
                    action = filtered_actions[0]

                subsystem = step.get("subsystem")

                if not subsystem:
                    subsystem = (
                        diagnosis_result.affected_subsystems[0]
                        if diagnosis_result.affected_subsystems
                        else "Unknown"
                    )

                steps.append(
                    RecoveryStep(
                        step_number=step.get("step_number", index),
                        action=action,
                        subsystem=subsystem,
                        expected_outcome=step.get(
                            "expected_outcome",
                            "Monitor telemetry for the expected stabilization response.",
                        ),
                        rollback_action=step.get(
                            "rollback_action",
                            "Restore the previous approved configuration if validation indicates degradation.",
                        ),
                    )
                )

            if not steps:
                steps.append(
                    RecoveryStep(
                        step_number=1,
                        action=filtered_actions[0],
                        subsystem=(
                            diagnosis_result.affected_subsystems[0]
                            if diagnosis_result.affected_subsystems
                            else "Unknown"
                        ),
                        expected_outcome=(
                            "Execute the approved recovery action while "
                            "monitoring relevant telemetry."
                        ),
                        rollback_action=(
                            "Restore the previous approved configuration "
                            "if validation indicates degradation."
                        ),
                    )
                )

            # Map risk level.
            raw_risk = str(
                raw.get("risk_level", "medium")
            ).lower()

            if "low" in raw_risk:
                risk_level = RiskLevel.LOW
            elif "high" in raw_risk:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.MEDIUM

            # Safely normalize risk score.
            try:
                risk_score = float(raw.get("risk_score", 0.35))
            except (TypeError, ValueError):
                risk_score = 0.35

            risk_score = min(
                1.0,
                max(0.0, risk_score),
            )

            # Keep duration as planner metadata rather than claiming it as
            # a telemetry-derived prediction.
            try:
                estimated_duration = int(
                    raw.get("estimated_duration_seconds", 180)
                )
            except (TypeError, ValueError):
                estimated_duration = 180

            estimated_duration = max(
                1,
                estimated_duration,
            )

            valid_plans.append(
                RecoveryPlan(
                    plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
                    title=raw.get(
                        "title",
                        f"Recovery Plan - {', '.join(filtered_actions)}",
                    ),
                    diagnosis_id=diagnosis_result.diagnosis_id,
                    satellite_id=diagnosis_result.satellite_id,
                    actions=filtered_actions,
                    preconditions=raw.get(
                        "preconditions",
                        [],
                    ),
                    expected_effects=raw.get(
                        "expected_effects",
                        [],
                    ),
                    steps=steps,
                    risk_level=risk_level,
                    risk_score=risk_score,
                    rollback_plan=raw.get(
                        "rollback_plan"
                    ),
                    estimated_duration_seconds=estimated_duration,
                    requires_ground_approval=bool(
                        raw.get(
                            "requires_ground_approval",
                            True,
                        )
                    ),
                    created_at=datetime.now(timezone.utc),
                )
            )

        if len(valid_plans) >= 2:
            return valid_plans

        logger.warning(
            "LLM returned fewer than 2 valid recovery plans, "
            "using deterministic fallback."
        )

    except Exception as exc:
        logger.warning(
            "Recovery planner LLM execution failed (%s), "
            "using deterministic fallback.",
            exc,
        )

    return get_fallback_recovery_plans(diagnosis_result)