"""Recovery Planner Agent for OrbitGuard spacecraft incident remediation.

Generates ranked candidate recovery plans restricted strictly to an approved
action command vocabulary, assessing risk, prerequisites, expected effects, and rollbacks.
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
    "REDUCE_PAYLOAD_LOAD": "De-energize non-essential payloads/instruments to lower bus power consumption and thermal dissipation.",
    "ENTER_SAFE_THERMAL_MODE": "Reorient solar panels or spacecraft attitude to minimize direct solar flux on overheated radiators and batteries.",
    "SWITCH_REDUNDANT_SENSOR": "Switch active sensing or control lines to secondary backup sensor/gyro/reaction wheel channels.",
    "REDUCE_MANEUVER_ACTIVITY": "Inhibit high-rate slew maneuvers and transition ADCS to low-momentum stabilization mode.",
    "SWITCH_COMM_PROFILE": "Reduce transmitter RF output power or throttle telemetry downlink rates to conserve power and heat.",
}


# ── Deterministic Fallback Recovery Plan Fixtures ────────────────────────────

def _fallback_battery_overheat_plans(diagnosis: DiagnosisResult) -> list[RecoveryPlan]:
    plan_1 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Immediate Thermal Shedding & Solar Reorientation",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=["REDUCE_PAYLOAD_LOAD", "ENTER_SAFE_THERMAL_MODE"],
        preconditions=[
            "Telemetry downlink operational (COMMS active)",
            "EPS battery state of charge > 40%",
        ],
        expected_effects=[
            "EPS bus power consumption drops by 35W",
            "Battery temperature rate of change drops below 0.1°C/min",
            "Battery temperature stabilizes under 38°C within 15 minutes",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome="Non-essential science instruments powered off, lowering bus load by 40%",
                rollback_action="Re-energize primary science instrument bus relays",
            ),
            RecoveryStep(
                step_number=2,
                action="ENTER_SAFE_THERMAL_MODE",
                subsystem="Thermal",
                expected_outcome="Spacecraft yaw offset by 15° to point EPS radiator into deep space shadow",
                rollback_action="Return to nominal sun-pointing attitude",
            ),
        ],
        risk_level=RiskLevel.LOW,
        risk_score=0.25,
        rollback_plan="If battery voltage drops below 24V during attitude tilt, abort safe thermal mode and restore solar orientation.",
        estimated_duration_seconds=180,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    plan_2 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Comprehensive Power Throttle & RF Profile Switch",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=["REDUCE_PAYLOAD_LOAD", "SWITCH_COMM_PROFILE"],
        preconditions=[
            "Ground station tracking lock acquired",
            "Command link margin > 6dB",
        ],
        expected_effects=[
            "Total EPS internal dissipation reduced by 50W",
            "Battery temperature stabilizes under 40°C within 25 minutes",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome="Primary imaging and payload processors set to standby mode",
                rollback_action="Command payload resume from standby",
            ),
            RecoveryStep(
                step_number=2,
                action="SWITCH_COMM_PROFILE",
                subsystem="COMMS",
                expected_outcome="Transmitter power attenuated from 20W to 5W low-rate beacon mode",
                rollback_action="Restore high-rate telemetry transmitter profile",
            ),
        ],
        risk_level=RiskLevel.MEDIUM,
        risk_score=0.45,
        rollback_plan="Automatically restore standard COMMS power profile if contact is lost for >300 seconds.",
        estimated_duration_seconds=300,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    return [plan_1, plan_2]


def _fallback_wheel_degradation_plans(diagnosis: DiagnosisResult) -> list[RecoveryPlan]:
    plan_1 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="ADCS Redundant Sensor Switch & Momentum Dump",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=["SWITCH_REDUNDANT_SENSOR", "REDUCE_MANEUVER_ACTIVITY"],
        preconditions=[
            "Secondary ADCS sensor/wheel channel healthy and calibrated",
            "Spacecraft attitude error < 1.0°",
        ],
        expected_effects=[
            "Attitude pointing error decreases from >0.3° to <0.04°",
            "Wheel speed jitter nominalized within 3000 ± 50 RPM",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_MANEUVER_ACTIVITY",
                subsystem="ADCS",
                expected_outcome="Inhibit high-torque slew commands and hold steady earth-pointing orientation",
                rollback_action="Re-enable attitude maneuver scheduling",
            ),
            RecoveryStep(
                step_number=2,
                action="SWITCH_REDUNDANT_SENSOR",
                subsystem="ADCS",
                expected_outcome="Cross-strap ADCS control loop to Wheel #2 / Star Tracker B backup branch",
                rollback_action="Switch control back to primary channel",
            ),
        ],
        risk_level=RiskLevel.LOW,
        risk_score=0.20,
        rollback_plan="Revert to primary ADCS branch and initiate magnetic torquer momentum desaturation if backup channel fails cross-calibration.",
        estimated_duration_seconds=240,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    plan_2 = RecoveryPlan(
        plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
        title="Safe Maneuver Inhibit & Payload Stabilization",
        diagnosis_id=diagnosis.diagnosis_id,
        satellite_id=diagnosis.satellite_id,
        actions=["REDUCE_MANEUVER_ACTIVITY", "REDUCE_PAYLOAD_LOAD"],
        preconditions=[
            "Attitude rate sensors operational",
        ],
        expected_effects=[
            "ADCS actuator mechanical stress reduced by 70%",
            "Prevents catastrophic wheel bearing seizure",
        ],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="Payload",
                expected_outcome="De-rate gimbaled payload instruments to eliminate reaction torques",
                rollback_action="Re-enable gimbal motor drives",
            ),
            RecoveryStep(
                step_number=2,
                action="REDUCE_MANEUVER_ACTIVITY",
                subsystem="ADCS",
                expected_outcome="Limit maximum angular slew rates to 0.05 deg/s",
                rollback_action="Restore standard slew rate limit (0.5 deg/s)",
            ),
        ],
        risk_level=RiskLevel.MEDIUM,
        risk_score=0.40,
        rollback_plan="Initiate sun-safe hold mode if attitude drift exceeds 1.5°.",
        estimated_duration_seconds=150,
        requires_ground_approval=True,
        created_at=datetime.now(timezone.utc),
    )

    return [plan_1, plan_2]


def _fallback_generic_plans(diagnosis: DiagnosisResult) -> list[RecoveryPlan]:
    return [
        RecoveryPlan(
            plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
            title="Safe Standby & Diagnostic Isolation",
            diagnosis_id=diagnosis.diagnosis_id,
            satellite_id=diagnosis.satellite_id,
            actions=["REDUCE_PAYLOAD_LOAD", "REDUCE_MANEUVER_ACTIVITY"],
            preconditions=["Telemetry bus active"],
            expected_effects=["Reduces subsystem stress to facilitate telemetry analysis"],
            steps=[
                RecoveryStep(
                    step_number=1,
                    action="REDUCE_PAYLOAD_LOAD",
                    subsystem=diagnosis.affected_subsystems[0] if diagnosis.affected_subsystems else "EPS",
                    expected_outcome="Lower subsystem operational load",
                    rollback_action="Restore nominal load",
                ),
            ],
            risk_level=RiskLevel.LOW,
            risk_score=0.30,
            rollback_plan="Restore nominal operation upon ground confirmation.",
            estimated_duration_seconds=120,
            requires_ground_approval=True,
            created_at=datetime.now(timezone.utc),
        )
    ]


def get_fallback_recovery_plans(diagnosis: DiagnosisResult) -> list[RecoveryPlan]:
    """Return deterministic candidate recovery plans based on diagnosis."""
    hypo = (diagnosis.primary_hypothesis + " " + (diagnosis.root_cause or "")).lower()
    if "battery" in hypo or "thermal" in hypo or "temperature" in hypo or "EPS" in diagnosis.affected_subsystems:
        return _fallback_battery_overheat_plans(diagnosis)
    if "wheel" in hypo or "attitude" in hypo or "ADCS" in diagnosis.affected_subsystems:
        return _fallback_wheel_degradation_plans(diagnosis)
    return _fallback_generic_plans(diagnosis)


# ── Recovery Planner Prompt & Execution ──────────────────────────────────────

async def generate_recovery_plans(
    diagnosis_result: DiagnosisResult,
    current_state: dict[str, Any] | None = None,
) -> list[RecoveryPlan]:
    """Generate 2-3 candidate recovery plans using LLM restricted to approved actions.

    Falls back to deterministic plan fixtures on failure.
    """
    prompt = f"""You are the Spacecraft Recovery Planning AI. Based on the diagnosis, generate 2 or 3 distinct, ranked candidate Recovery Plans.

### APPROVED ACTION VOCABULARY (You MUST ONLY select action commands from this exact list):
{json.dumps(APPROVED_ACTIONS, indent=2)}

### ACTION DEFINITIONS:
{json.dumps(ACTION_DESCRIPTIONS, indent=2)}

### DIAGNOSIS RESULT:
- Satellite: {diagnosis_result.satellite_id}
- Primary Hypothesis: {diagnosis_result.primary_hypothesis}
- Root Cause: {diagnosis_result.root_cause}
- Affected Subsystems: {diagnosis_result.affected_subsystems}
- Confidence: {diagnosis_result.confidence}
- Evidence: {diagnosis_result.evidence}

### CURRENT SPACECRAFT STATE:
{json.dumps(current_state or {}, indent=2)}

### REQUIRED JSON OUTPUT FORMAT:
Return a JSON array of 2 to 3 candidate plan objects matching:
[
  {{
    "title": "Strategy Title",
    "actions": ["REDUCE_PAYLOAD_LOAD", "ENTER_SAFE_THERMAL_MODE"],
    "preconditions": ["Prerequisite 1", "Prerequisite 2"],
    "expected_effects": ["Expected metric change 1", "Expected stabilization 2"],
    "risk_level": "low", 
    "risk_score": 0.25,
    "rollback_plan": "Specific rollback strategy if plan fails",
    "estimated_duration_seconds": 180,
    "requires_ground_approval": true,
    "steps": [
      {{
        "step_number": 1,
        "action": "REDUCE_PAYLOAD_LOAD",
        "subsystem": "EPS",
        "expected_outcome": "Outcome of step 1",
        "rollback_action": "Rollback command for step 1"
      }}
    ]
  }}
]

CRITICAL CONSTRAINT: Every item in "actions" and every step's "action" MUST be EXACTLY one of:
REDUCE_PAYLOAD_LOAD, ENTER_SAFE_THERMAL_MODE, SWITCH_REDUNDANT_SENSOR, REDUCE_MANEUVER_ACTIVITY, SWITCH_COMM_PROFILE.
"""

    try:
        data = await call_llm_structured(
            prompt=prompt,
            system_prompt="You are an autonomous spacecraft recovery planning AI. You generate candidate recovery plans in strict JSON format using only approved vocabulary.",
            retries=1,
            timeout=12.0,
        )

        plans_raw = data if isinstance(data, list) else data.get("plans", []) if isinstance(data, dict) else []
        
        valid_plans: list[RecoveryPlan] = []
        for raw in plans_raw:
            if not isinstance(raw, dict):
                continue
            
            # Validate and filter actions to approved vocabulary only
            filtered_actions = [a for a in raw.get("actions", []) if a in APPROVED_ACTIONS]
            if not filtered_actions:
                continue

            steps: list[RecoveryStep] = []
            for i, st in enumerate(raw.get("steps", []), start=1):
                act = st.get("action")
                if act not in APPROVED_ACTIONS:
                    act = filtered_actions[0]
                steps.append(
                    RecoveryStep(
                        step_number=st.get("step_number", i),
                        action=act,
                        subsystem=st.get("subsystem", diagnosis_result.affected_subsystems[0] if diagnosis_result.affected_subsystems else "EPS"),
                        expected_outcome=st.get("expected_outcome", "Subsystem stabilized"),
                        rollback_action=st.get("rollback_action"),
                    )
                )

            # Map risk level
            raw_risk = str(raw.get("risk_level", "medium")).lower()
            risk_level = (
                RiskLevel.LOW if "low" in raw_risk
                else RiskLevel.HIGH if "high" in raw_risk
                else RiskLevel.MEDIUM
            )

            valid_plans.append(
                RecoveryPlan(
                    plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
                    title=raw.get("title", f"Recovery Plan - {', '.join(filtered_actions)}"),
                    diagnosis_id=diagnosis_result.diagnosis_id,
                    satellite_id=diagnosis_result.satellite_id,
                    actions=filtered_actions,
                    preconditions=raw.get("preconditions", []),
                    expected_effects=raw.get("expected_effects", []),
                    steps=steps,
                    risk_level=risk_level,
                    risk_score=float(min(1.0, max(0.0, raw.get("risk_score", 0.35)))),
                    rollback_plan=raw.get("rollback_plan"),
                    estimated_duration_seconds=int(raw.get("estimated_duration_seconds", 180)),
                    requires_ground_approval=bool(raw.get("requires_ground_approval", True)),
                    created_at=datetime.now(timezone.utc),
                )
            )

        if len(valid_plans) >= 2:
            return valid_plans
        logger.warning("LLM returned fewer than 2 valid recovery plans, using deterministic fallback.")
    except Exception as exc:
        logger.warning("Recovery planner LLM execution failed (%s), using deterministic fallback.", exc)

    return get_fallback_recovery_plans(diagnosis_result)
