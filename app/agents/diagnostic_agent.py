"""Diagnostic Agent for OrbitGuard spacecraft anomaly root-cause analysis.

Analyzes telemetry history, anomaly events, and subsystem dependency graphs
using an LLM to generate structured diagnostic hypotheses, evidence, and verification checks.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.llm import call_llm_structured
from app.schemas.anomaly import AnomalyEvent
from app.schemas.diagnosis import DiagnosisResult

logger = logging.getLogger(__name__)
DIAGNOSTIC_SYSTEM_PROMPT = """
You are the OrbitGuard Lead Satellite Diagnostic Agent. Your role is to analyze anomaly snapshots and provide precise, evidence-grounded root-cause analysis.

STRICT EVIDENCE-GROUNDING RULES:

1. ONLY make factual statements supported by metrics explicitly present in the provided telemetry_snapshot or telemetry history.

2. NEVER assume or invent unmeasured orbital conditions, hardware states, or physical mechanisms.
   Do NOT claim things such as "high charging current", "direct sunlit phase", "rapid temperature increase", "bearing wear", or "sensor drift" unless the provided telemetry actually supports them.

3. All possible root causes must be presented as HYPOTHESES, not confirmed facts.

4. If the available telemetry is insufficient to determine a precise root cause, explicitly state:
   "Telemetry is inconclusive for root cause determination without [missing metric]."

5. Evidence must refer only to values or events actually present in the supplied telemetry.

6. Verification checks may request additional telemetry streams, but must NOT claim that missing telemetry already exists.

7. Do not fabricate telemetry values, operating conditions, spacecraft states, or historical events.

8. Keep confidence proportional to the available evidence. Limited telemetry must result in lower confidence.

9. Distinguish clearly between:
   - observed facts
   - possible hypotheses
   - missing information required for verification

10. Distinguish anomaly types carefully based on the primary out-of-boundary metric:
    - If the anomaly is a LOW BATTERY / LOW VOLTAGE event (battery_voltage below threshold), formulate hypotheses, evidence, and checks specific to electrical power, bus voltage, charging/input conditions, load, or sensor behavior. Do NOT misclassify or describe low voltage as a thermal anomaly unless telemetry explicitly shows abnormal temperatures.
    - If the anomaly is a THERMAL / TEMPERATURE event, formulate hypotheses specific to thermal dissipation and temperature control.
"""

# ── Subsystem Dependency Knowledge Graph ─────────────────────────────────────
SUBSYSTEM_GRAPH = {
    "EPS": {
        "description": "Electrical Power Subsystem (Battery, Solar Arrays, Power Distribution)",
        "dependencies": ["Thermal"],
        "critical_metrics": ["battery_temperature", "battery_voltage", "solar_power"],
        "failure_modes": ["Thermal runaway", "Battery cell degradation", "Shunt regulator failure"],
    },
    "ADCS": {
        "description": "Attitude Determination & Control Subsystem (Reaction Wheels, Gyros, Star Trackers)",
        "dependencies": ["EPS", "Structural"],
        "critical_metrics": ["wheel_speed", "attitude_error"],
        "failure_modes": ["Reaction wheel bearing friction", "Sensor drift", "Actuator saturation"],
    },
    "COMMS": {
        "description": "Communications Subsystem (Transponder, Antennas, RF Amplifiers)",
        "dependencies": ["EPS", "Thermal"],
        "critical_metrics": ["comm_snr"],
        "failure_modes": ["RF amplifier power drop", "Antenna pointing misalignment", "Thermal noise"],
    },
    "Thermal": {
        "description": "Thermal Control Subsystem (Heat Pipes, Radiators, Multi-layer Insulation)",
        "dependencies": ["EPS"],
        "critical_metrics": ["battery_temperature"],
        "failure_modes": ["Heater stuck on", "Radiator surface degradation", "Heat pipe freeze"],
    },
}


# ── Deterministic Fallback Fixtures ──────────────────────────────────────────
def _fallback_battery_overheat(anomaly: AnomalyEvent) -> DiagnosisResult:
    telemetry = anomaly.telemetry_snapshot or {}

    temperature = telemetry.get("battery_temperature")
    voltage = telemetry.get("battery_voltage")
    solar_power = telemetry.get("solar_power")

    evidence = []

    if temperature is not None:
        evidence.append(
            f"Battery temperature observed at {temperature}°C."
        )

    if voltage is not None:
        evidence.append(
            f"Battery voltage observed at {voltage}V."
        )

    if solar_power is not None:
        evidence.append(
            f"Solar power observed at {solar_power}W."
        )

    if not evidence:
        evidence.append(
            "Anomaly was detected, but the telemetry snapshot contains no usable measurements."
        )

    if temperature is not None:
        primary_hypothesis = (
            "Possible thermal dissipation inefficiency or another "
            "battery thermal-control issue causing the observed "
            "temperature threshold excursion."
        )
        root_cause = (
            "Telemetry confirms elevated battery temperature, but "
            "the available measurements are insufficient to determine "
            "the precise physical root cause."
        )
    else:
        primary_hypothesis = (
            "Possible battery thermal anomaly; insufficient telemetry "
            "is available to identify the cause."
        )
        root_cause = (
            "Telemetry is inconclusive for root cause determination "
            "without battery temperature measurements."
        )

    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis=primary_hypothesis,
        root_cause=root_cause,
        alternatives=[
            "Possible telemetry sensor error or calibration issue.",
            "Possible internal battery degradation requiring additional diagnostics.",
        ],
        evidence=evidence,
        checks=[
            "Verify redundant battery temperature sensor readings.",
            "Request battery charge/discharge current telemetry.",
            "Request thermal subsystem and radiator telemetry.",
        ],
        contributing_factors=[
            "Available telemetry shows a battery thermal anomaly."
        ],
        affected_subsystems=["EPS", "Thermal"],
        confidence=0.65,
        reasoning=(
            "The fallback diagnosis is limited to measurements explicitly "
            "present in the anomaly telemetry. A precise physical root "
            "cause cannot be confirmed without additional subsystem telemetry."
        ),
        diagnosed_at=datetime.now(timezone.utc),
    )


def _fallback_low_battery(anomaly: AnomalyEvent) -> DiagnosisResult:
    telemetry = anomaly.telemetry_snapshot or {}

    voltage = telemetry.get("battery_voltage")
    temperature = telemetry.get("battery_temperature")
    solar_power = telemetry.get("solar_power")

    evidence = []

    if voltage is not None:
        evidence.append(
            f"Battery voltage observed at {voltage} V."
        )

    if temperature is not None:
        evidence.append(
            f"Battery temperature observed at {temperature}°C."
        )

    if solar_power is not None:
        evidence.append(
            f"Solar power observed at {solar_power} W."
        )

    if not evidence:
        evidence.append(
            "Anomaly was detected, but the telemetry snapshot contains no usable measurements."
        )

    if voltage is not None:
        primary_hypothesis = (
            "Battery voltage is below the configured detection boundary; "
            "the available telemetry is insufficient to determine the physical cause."
        )
        root_cause = (
            "Insufficient telemetry to determine whether the low voltage is "
            "caused by charging/input conditions, battery condition, load, or sensor behavior."
        )
    else:
        primary_hypothesis = (
            "Possible low battery voltage anomaly; insufficient telemetry "
            "is available to identify the cause."
        )
        root_cause = (
            "Telemetry is inconclusive for root cause determination "
            "without battery voltage measurements."
        )

    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis=primary_hypothesis,
        root_cause=root_cause,
        alternatives=[
            "Possible battery cell degradation or reduced storage capacity.",
            "Possible elevated subsystem load drawing excessive bus power.",
            "Possible power input or charging shortfall.",
            "Possible telemetry sensor error or voltage calibration drift.",
        ],
        evidence=evidence,
        checks=[
            "Verify battery current, charging/input telemetry, redundant voltage sensing, and relevant power-system telemetry.",
            "Verify redundant battery voltage sensor readings.",
            "Request battery charge/discharge current telemetry.",
            "Review solar array power generation and bus load history.",
        ],
        contributing_factors=[
            "Available telemetry shows a low battery voltage condition."
        ],
        affected_subsystems=["EPS"],
        confidence=0.70,
        reasoning=(
            "The fallback diagnosis is limited to measurements explicitly "
            "present in the anomaly telemetry. A precise physical root "
            "cause cannot be confirmed without additional power-subsystem telemetry."
        ),
        diagnosed_at=datetime.now(timezone.utc),
    )


def _fallback_wheel_degradation(anomaly: AnomalyEvent) -> DiagnosisResult:
    telemetry = anomaly.telemetry_snapshot or {}

    wheel_speed = telemetry.get("wheel_speed")
    attitude_error = telemetry.get("attitude_error")

    evidence = []

    if wheel_speed is not None:
        evidence.append(
            f"Reaction wheel speed observed at {wheel_speed} RPM."
        )

    if attitude_error is not None:
        evidence.append(
            f"Attitude error observed at {attitude_error}°."
        )

    if not evidence:
        evidence.append(
            "Anomaly was detected, but the telemetry snapshot contains no usable measurements."
        )

    primary_hypothesis = (
        "Possible reaction wheel or ADCS control anomaly based on "
        "the observed telemetry."
    )

    root_cause = (
        "Telemetry indicates an ADCS-related anomaly, but the available "
        "measurements are insufficient to confirm a specific mechanical "
        "or sensor root cause."
    )

    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis=primary_hypothesis,
        root_cause=root_cause,
        alternatives=[
            "Possible reaction wheel mechanical degradation.",
            "Possible attitude sensor or control-loop issue.",
        ],
        evidence=evidence,
        checks=[
            "Request reaction wheel motor current and torque telemetry.",
            "Verify redundant attitude sensor measurements.",
            "Review reaction wheel speed history for sustained deviations.",
        ],
        contributing_factors=[
            "Available telemetry shows an ADCS-related anomaly."
        ],
        affected_subsystems=["ADCS"],
        confidence=0.65,
        reasoning=(
            "The fallback diagnosis uses only measurements explicitly "
            "present in the anomaly telemetry and does not treat a "
            "specific physical failure as confirmed."
        ),
        diagnosed_at=datetime.now(timezone.utc),
    )


def _fallback_generic(anomaly: AnomalyEvent) -> DiagnosisResult:
    telemetry = anomaly.telemetry_snapshot or {}

    evidence = []

    for key, value in telemetry.items():
        evidence.append(
            f"{key}: {value}"
        )

    if not evidence:
        evidence.append(
            "Anomaly was detected, but no telemetry measurements were provided."
        )

    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis=(
            f"An operational anomaly was detected in the "
            f"{anomaly.subsystem} subsystem."
        ),
        root_cause=(
            f"Telemetry is inconclusive for root cause determination "
            f"without additional {anomaly.subsystem} diagnostic telemetry."
        ),
        alternatives=[
            "Possible transient telemetry or sensor issue.",
            "Possible subsystem-level operational fault requiring verification.",
        ],
        evidence=evidence,
        checks=[
            f"Request additional diagnostic telemetry for the {anomaly.subsystem} subsystem.",
            "Verify redundant sensor measurements.",
        ],
        contributing_factors=[],
        affected_subsystems=[anomaly.subsystem],
        confidence=min(0.5, anomaly.confidence),
        reasoning=(
            "The fallback diagnosis is based only on the telemetry "
            "measurements supplied with the anomaly event."
        ),
        diagnosed_at=datetime.now(timezone.utc),
    )


def get_fallback_diagnosis(anomaly: AnomalyEvent) -> DiagnosisResult:
    """Return deterministic fixture diagnosis based on anomaly characteristics."""
    desc = anomaly.description.lower()
    subsys = anomaly.subsystem.upper()
    snapshot = anomaly.telemetry_snapshot or {}

    # 1. Check for ADCS / reaction wheel anomalies
    if "wheel" in desc or "attitude" in desc or subsys == "ADCS":
        return _fallback_wheel_degradation(anomaly)

    # 2. Check for low battery / voltage anomalies
    is_low_battery = (
        "low_battery" in desc
        or "low battery" in desc
        or "voltage" in desc
        or (subsys == "EPS" and float(snapshot.get("battery_voltage", 30.0) if not isinstance(snapshot.get("battery_voltage"), dict) else snapshot["battery_voltage"].get("value", 30.0)) < 20.0)
    )
    if is_low_battery:
        return _fallback_low_battery(anomaly)

    # 3. Check for battery overheat / thermal anomalies
    temp_val = float(snapshot.get("battery_temperature", 0.0) if not isinstance(snapshot.get("battery_temperature"), dict) else snapshot["battery_temperature"].get("value", 0.0))
    is_thermal = (
        "temperature" in desc
        or "overheat" in desc
        or "thermal" in desc
        or subsys == "THERMAL"
        or (subsys == "EPS" and temp_val > 45.0)
    )
    if is_thermal:
        return _fallback_battery_overheat(anomaly)

    return _fallback_generic(anomaly)


# ── Diagnostic Agent Prompt & Execution ──────────────────────────────────────

async def diagnose_anomaly(
    anomaly_event: AnomalyEvent,
    telemetry_history: list[dict],
) -> DiagnosisResult:
    """Perform root cause analysis on an anomaly event using telemetry history and LLM.

    Falls back to deterministic diagnostic fixtures on LLM failure or timeout.
    """
    recent_telemetry = telemetry_history[-15:] if telemetry_history else []
    from ai_ml.retrieval.retriever import retrieve_anomaly_knowledge
    retrieved = retrieve_anomaly_knowledge(
        anomaly_type=anomaly_event.description,
        subsystem=anomaly_event.subsystem,
    )
    retrieval_section = retrieved.format_for_prompt()

    prompt = f"""You are the Spacecraft Chief Diagnostic AI. Analyze the following spacecraft anomaly and telemetry history to produce a structured diagnosis.

### ANOMALY EVENT:
- ID: {anomaly_event.anomaly_id}
- Satellite: {anomaly_event.satellite_id}
- Subsystem: {anomaly_event.subsystem}
- Severity: {anomaly_event.severity.value}
- Description: {anomaly_event.description}
- Snapshot: {json.dumps(anomaly_event.telemetry_snapshot or {})}

### SUBSYSTEM KNOWLEDGE GRAPH:
{json.dumps(SUBSYSTEM_GRAPH, indent=2)}

### RECENT TELEMETRY HISTORY (Last {len(recent_telemetry)} readings):
{json.dumps(recent_telemetry, indent=2)}

### RETRIEVED ADVISORY RUNBOOKS & HISTORICAL OPS (REFERENCE ONLY):
{retrieval_section}

### EVIDENCE REQUIREMENTS:
- Every item in "evidence" must be directly traceable to a value in the supplied telemetry.
- Do not describe a trend unless multiple telemetry readings demonstrate that trend.
- Do not claim a physical cause as fact when the telemetry only shows a symptom.
- If a root cause cannot be established from the available telemetry, say so explicitly.
- Missing telemetry must be listed as a verification requirement rather than treated as if it exists.
- Retrieved runbooks/historical cases are advisory guidelines; never treat historical events as live telemetry.
- For LOW_BATTERY or low-voltage anomalies, ground reasoning strictly in voltage and power observations; do not describe low voltage as a thermal anomaly unless thermal telemetry specifically demonstrates an overtemperature condition.

### REQUIRED JSON OUTPUT FORMAT:
Return a single valid JSON object with EXACTLY the following keys:
{{
  "primary_hypothesis": "Clear statement of primary root-cause hypothesis",
  "root_cause": "Specific technical root cause description",
  "alternatives": ["Alternative hypothesis 1", "Alternative hypothesis 2"],
  "evidence": ["Evidence 1 from telemetry", "Evidence 2 from subsystem graph"],
  "checks": ["Verification step 1 to confirm", "Verification step 2"],
  "contributing_factors": ["Factor 1", "Factor 2"],
  "affected_subsystems": ["Subsystem 1", "Subsystem 2"],
  "confidence": 0.90,
  "reasoning": "Step-by-step diagnostic reasoning chain"
}}
"""

    try:
        data = await call_llm_structured(
            prompt=prompt,
            system_prompt=DIAGNOSTIC_SYSTEM_PROMPT,
            retries=1,
            timeout=10.0,
        )

        if isinstance(data, dict) and "primary_hypothesis" in data:
            return DiagnosisResult(
                diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
                anomaly_id=anomaly_event.anomaly_id,
                satellite_id=anomaly_event.satellite_id,
                primary_hypothesis=data.get("primary_hypothesis", "Unknown hypothesis"),
                root_cause=data.get("root_cause") or data.get("primary_hypothesis"),
                alternatives=data.get("alternatives", []),
                evidence=data.get("evidence", []),
                checks=data.get("checks", []),
                contributing_factors=data.get("contributing_factors", []),
                affected_subsystems=data.get("affected_subsystems", [anomaly_event.subsystem]),
                confidence=float(min(1.0, max(0.0, data.get("confidence", 0.85)))),
                reasoning=data.get("reasoning"),
                diagnosed_at=datetime.now(timezone.utc),
            )
        logger.warning("LLM response lacked expected keys, falling back to deterministic fixture.")
    except Exception as exc:
        logger.warning("Diagnostic agent LLM execution failed (%s), using deterministic fallback.", exc)

    return get_fallback_diagnosis(anomaly_event)
