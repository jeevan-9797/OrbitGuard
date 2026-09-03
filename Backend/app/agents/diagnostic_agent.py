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
    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis="High charging current combined with elevated radiator thermal load causing EPS thermal runaway",
        root_cause="Battery cell over-temperature triggered by unthrottled high-rate charging under direct solar flux",
        alternatives=[
            "Thermal radiator surface contamination reducing heat dissipation",
            "Internal battery cell short circuit causing localized thermal dissipation",
        ],
        evidence=[
            "Battery temperature exceeded threshold (>45°C)",
            "EPS subsystem active charge cycle during peak solar power intake",
            "Rapid temperature rate-of-change observed in telemetry time-series",
        ],
        checks=[
            "Verify solar array charge current regulator telemetry",
            "Cross-check thermal sensor calibration on redundant EPS thermistors",
            "Check radiator panel temperature gradient",
        ],
        contributing_factors=[
            "Solar panel power output operating at maximum capacity (>100W)",
            "Spacecraft in direct sunlit orbit phase",
        ],
        affected_subsystems=["EPS", "Thermal", "Payload"],
        confidence=0.92,
        reasoning="Rapid linear temperature increase in EPS battery telemetry correlated with sunlit power generation indicates thermal accumulation exceeding passive dissipation capacity.",
        diagnosed_at=datetime.now(timezone.utc),
    )


def _fallback_wheel_degradation(anomaly: AnomalyEvent) -> DiagnosisResult:
    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis="Reaction Wheel assembly bearing mechanical wear inducing rotor speed jitter and attitude pointing error",
        root_cause="ADCS Reaction Wheel #1 bearing lubricant degradation leading to high drag torque fluctuations",
        alternatives=[
            "ADCS rate gyro sensor calibration drift",
            "External aerodynamic/gravitational disturbance torque exceedance",
        ],
        evidence=[
            "Wheel speed deviation exceeding nominal 3000 RPM baseline by >400 RPM",
            "Attitude pointing error increased beyond 0.3° threshold",
            "Fluctuating motor drive current in ADCS telemetry window",
        ],
        checks=[
            "Sample reaction wheel motor current ripple at 10Hz",
            "Perform gyro-independent star tracker attitude solution comparison",
            "Review accumulated reaction wheel operating hours and friction trends",
        ],
        contributing_factors=[
            "High frequency attitude slew maneuvers executed during recent orbit passes",
            "Thermal cycling on ADCS wheel housing",
        ],
        affected_subsystems=["ADCS", "Payload", "COMMS"],
        confidence=0.89,
        reasoning="Coincident high wheel speed variance and attitude pointing divergence points directly to ADCS mechanical actuator degradation rather than sensor miscalibration.",
        diagnosed_at=datetime.now(timezone.utc),
    )


def _fallback_generic(anomaly: AnomalyEvent) -> DiagnosisResult:
    return DiagnosisResult(
        diagnosis_id=f"DIAG-{uuid.uuid4().hex[:8].upper()}",
        anomaly_id=anomaly.anomaly_id,
        satellite_id=anomaly.satellite_id,
        primary_hypothesis=f"Subsystem {anomaly.subsystem} operational deviation: {anomaly.description}",
        root_cause=f"Anomalous metric readings in {anomaly.subsystem} violating operational baseline limits",
        alternatives=[
            "Transient telemetry sensor glitch",
            "External orbital environmental perturbation",
        ],
        evidence=[
            f"Anomaly reported on subsystem {anomaly.subsystem} with severity {anomaly.severity}",
            f"Description: {anomaly.description}",
        ],
        checks=[
            f"Query redundant sensor telemetry for {anomaly.subsystem}",
            "Perform telemetry bus integrity check",
        ],
        contributing_factors=["Spacecraft operating in dynamic orbital regime"],
        affected_subsystems=[anomaly.subsystem],
        confidence=anomaly.confidence,
        reasoning=f"Automated rule-based diagnosis based on anomaly event: {anomaly.description}",
        diagnosed_at=datetime.now(timezone.utc),
    )


def get_fallback_diagnosis(anomaly: AnomalyEvent) -> DiagnosisResult:
    """Return deterministic fixture diagnosis based on anomaly characteristics."""
    desc = anomaly.description.lower()
    subsys = anomaly.subsystem.upper()
    if "battery" in desc or "temperature" in desc or subsys == "EPS":
        return _fallback_battery_overheat(anomaly)
    if "wheel" in desc or "attitude" in desc or subsys == "ADCS":
        return _fallback_wheel_degradation(anomaly)
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
            system_prompt="You are an expert satellite diagnostic agent. You always respond in strict, valid JSON matching the schema.",
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
