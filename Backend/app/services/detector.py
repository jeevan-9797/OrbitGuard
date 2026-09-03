"""Deterministic anomaly detection service.

Analyses telemetry snapshots for known anomaly patterns and maintains an
open-incident registry for deduplication.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.schemas.anomaly import AnomalyEvent, SeverityLevel
from app.simulator.telemetry import get_previous_value, get_telemetry_history


# ── Open Incident Registry (deduplication) ───────────────────────────────────
# Key: (satellite_id, anomaly_type)  ->  AnomalyEvent
_open_incidents: dict[tuple[str, str], AnomalyEvent] = {}


def get_open_incidents() -> list[AnomalyEvent]:
    """Return all currently open (non-resolved) anomaly incidents."""
    return list(_open_incidents.values())


def clear_incidents() -> None:
    """Clear all open incidents (used by simulator reset)."""
    from app.services.orchestrator import clear_orchestrator_incidents
    _open_incidents.clear()
    clear_orchestrator_incidents()



# ── Threshold Constants ──────────────────────────────────────────────────────

BATTERY_TEMP_ABSOLUTE_THRESHOLD = 45.0   # degC
BATTERY_TEMP_RATE_THRESHOLD = 2.0        # degC per reading interval

WHEEL_SPEED_NOMINAL_MIN = 2800.0         # RPM
WHEEL_SPEED_NOMINAL_MAX = 3200.0         # RPM
WHEEL_SPEED_JITTER_THRESHOLD = 400.0     # RPM deviation from 3000 centre

ATTITUDE_ERROR_THRESHOLD = 0.3           # deg


# ── Detection Logic ──────────────────────────────────────────────────────────

def _check_battery_overheat(
    satellite_id: str, metrics: dict[str, dict[str, Any]]
) -> AnomalyEvent | None:
    """Detect battery overheat: absolute temp > 45 degC OR rate > 2 degC/reading."""
    bt = metrics.get("battery_temperature")
    if bt is None:
        return None

    temp = bt["value"]
    prev = get_previous_value(satellite_id, "battery_temperature")
    rate = abs(temp - prev) if prev is not None else 0.0

    if temp > BATTERY_TEMP_ABSOLUTE_THRESHOLD or rate > BATTERY_TEMP_RATE_THRESHOLD:
        severity = (
            SeverityLevel.CRITICAL if temp > 60.0
            else SeverityLevel.HIGH if temp > BATTERY_TEMP_ABSOLUTE_THRESHOLD
            else SeverityLevel.MEDIUM
        )
        return AnomalyEvent(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            satellite_id=satellite_id,
            detected_at=datetime.now(timezone.utc),
            subsystem="EPS",
            severity=severity,
            description=(
                f"Battery temperature anomaly: {temp:.1f} degC "
                f"(rate {rate:.2f} degC/reading)"
            ),
            telemetry_snapshot={
                "battery_temperature": temp,
                "rate_of_change": round(rate, 4),
            },
            confidence=min(1.0, 0.6 + (temp - 40.0) * 0.02),
        )
    return None


def _check_wheel_degradation(
    satellite_id: str, metrics: dict[str, dict[str, Any]]
) -> AnomalyEvent | None:
    """Detect wheel degradation: speed jitter or attitude error above threshold."""
    ws = metrics.get("wheel_speed")
    ae = metrics.get("attitude_error")
    if ws is None and ae is None:
        return None

    speed = ws["value"] if ws else 3000.0
    att_err = ae["value"] if ae else 0.0

    speed_deviation = abs(speed - 3000.0)
    speed_anomaly = speed_deviation > WHEEL_SPEED_JITTER_THRESHOLD
    attitude_anomaly = att_err > ATTITUDE_ERROR_THRESHOLD

    if speed_anomaly or attitude_anomaly:
        severity = (
            SeverityLevel.CRITICAL if (speed_anomaly and attitude_anomaly)
            else SeverityLevel.HIGH if attitude_anomaly
            else SeverityLevel.MEDIUM
        )
        return AnomalyEvent(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            satellite_id=satellite_id,
            detected_at=datetime.now(timezone.utc),
            subsystem="ADCS",
            severity=severity,
            description=(
                f"Wheel degradation: speed={speed:.0f} RPM "
                f"(deviation {speed_deviation:.0f}), "
                f"attitude_error={att_err:.3f} deg"
            ),
            telemetry_snapshot={
                "wheel_speed": round(speed, 2),
                "speed_deviation": round(speed_deviation, 2),
                "attitude_error": round(att_err, 4),
            },
            confidence=min(1.0, 0.5 + speed_deviation / 1000.0 + att_err),
        )
    return None


# ── Public API ───────────────────────────────────────────────────────────────

_CHECKS = [
    ("battery_overheat", _check_battery_overheat),
    ("wheel_degradation", _check_wheel_degradation),
]


def analyse_telemetry(snapshot: dict) -> list[AnomalyEvent]:
    """Run all anomaly checks against a telemetry *snapshot*.

    Returns a list of newly detected :class:`AnomalyEvent` instances.
    Duplicate incidents (same satellite + anomaly type already open) are
    suppressed.
    """
    satellite_id: str = snapshot["satellite_id"]
    metrics: dict[str, dict[str, Any]] = snapshot["metrics"]
    detected: list[AnomalyEvent] = []

    for anomaly_type, check_fn in _CHECKS:
        key = (satellite_id, anomaly_type)
        # Skip if an incident is already open for this satellite + type
        if key in _open_incidents:
            continue

        event = check_fn(satellite_id, metrics)
        if event is not None:
            _open_incidents[key] = event
            detected.append(event)
            # Register in orchestrator
            from app.services.orchestrator import register_detected_incident
            register_detected_incident(event)

    return detected

