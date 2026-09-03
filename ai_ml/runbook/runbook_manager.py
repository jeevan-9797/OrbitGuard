"""
Runbook Manager for OrbitGuard.

Manages spacecraft standard operating procedures (SOPs), emergency containment
runbooks, and subsystem contingency protocols.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RunbookEntry:
    """Structured flight operations runbook entry."""

    runbook_id: str
    title: str
    subsystem: str
    applicable_anomalies: list[str]
    trigger_condition: str
    recommended_actions: list[str]
    diagnostic_checks: list[str]
    safety_constraints: list[str]
    rollback_procedure: str
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "source": "SATELLITE_OPERATIONS_MANUAL_V2",
            "status": "REFERENCE_GUIDELINE_ONLY",
            "is_advisory": True,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runbook_id": self.runbook_id,
            "title": self.title,
            "subsystem": self.subsystem,
            "applicable_anomalies": self.applicable_anomalies,
            "trigger_condition": self.trigger_condition,
            "recommended_actions": self.recommended_actions,
            "diagnostic_checks": self.diagnostic_checks,
            "safety_constraints": self.safety_constraints,
            "rollback_procedure": self.rollback_procedure,
            "metadata": self.metadata,
        }


def _get_default_runbooks() -> list[dict[str, Any]]:
    return [
        {
            "runbook_id": "RB-EPS-001",
            "title": "EPS Bus Low-Voltage & Battery Depletion Containment",
            "subsystem": "EPS",
            "applicable_anomalies": ["LOW_BATTERY", "low_battery", "BATTERY_UNDERVOLTAGE"],
            "trigger_condition": "Battery bus voltage drops below configured operating limit (< 20.0V).",
            "recommended_actions": [
                "REDUCE_PAYLOAD_LOAD",
                "SWITCH_COMM_PROFILE",
            ],
            "diagnostic_checks": [
                "Verify battery current, charging/input telemetry, redundant voltage sensing, and relevant power-system telemetry.",
                "Verify redundant battery voltage sensor readings.",
                "Request battery charge/discharge current telemetry.",
                "Review solar array power generation and bus load history.",
            ],
            "safety_constraints": [
                "Do not shed critical thermal survival heaters or command telemetry receivers.",
                "Verify bus voltage recovery before restoring nominal payload power.",
            ],
            "rollback_procedure": "Restore nominal payload and comms configuration if bus voltage exceeds 26.0V and telemetry indicates stable solar power input.",
            "metadata": {
                "source": "SATELLITE_OPERATIONS_MANUAL_V2",
                "status": "REFERENCE_GUIDELINE_ONLY",
                "is_advisory": True,
            },
        },
        {
            "runbook_id": "RB-THM-001",
            "title": "Battery Thermal Runaway & High-Temperature Mitigation",
            "subsystem": "Thermal",
            "applicable_anomalies": ["HIGH_TEMPERATURE", "battery_overheat", "BATTERY_OVERTEMPERATURE"],
            "trigger_condition": "Battery temperature exceeds nominal thermal boundary (> 45.0°C).",
            "recommended_actions": [
                "REDUCE_PAYLOAD_LOAD",
                "ENTER_SAFE_THERMAL_MODE",
            ],
            "diagnostic_checks": [
                "Verify redundant battery temperature sensor readings.",
                "Request battery charge/discharge current telemetry.",
                "Request thermal subsystem and radiator telemetry.",
            ],
            "safety_constraints": [
                "Payload load reduction must precede transition into safe thermal mode.",
                "Do not command full safe hold unless single-subsystem thermal shedding fails to arrest temperature rise.",
            ],
            "rollback_procedure": "Exit safe thermal mode and restore nominal payload activity once battery temperature falls below 35.0°C.",
            "metadata": {
                "source": "SATELLITE_OPERATIONS_MANUAL_V2",
                "status": "REFERENCE_GUIDELINE_ONLY",
                "is_advisory": True,
            },
        },
        {
            "runbook_id": "RB-ADCS-001",
            "title": "Reaction Wheel Momentum & Attitude Degradation Stabilization",
            "subsystem": "ADCS",
            "applicable_anomalies": ["REACTION_WHEEL_OVERLOAD", "wheel_degradation", "ATTITUDE_CONTROL_ERROR"],
            "trigger_condition": "Reaction wheel speed deviation exceeds 400 RPM or attitude error exceeds 0.3 deg.",
            "recommended_actions": [
                "REDUCE_MANEUVER_ACTIVITY",
                "SWITCH_REDUNDANT_SENSOR",
            ],
            "diagnostic_checks": [
                "Request reaction wheel motor current and torque telemetry.",
                "Verify redundant attitude sensor measurements.",
                "Review reaction wheel speed history for sustained deviations.",
            ],
            "safety_constraints": [
                "ADCS maneuver activity reduction must be executed prior to any non-ADCS action.",
                "Verify health of redundant sensor channel before executing sensor switchover.",
            ],
            "rollback_procedure": "Return to primary attitude sensing channel and restore nominal maneuver profile if redundant channel validation fails.",
            "metadata": {
                "source": "SATELLITE_OPERATIONS_MANUAL_V2",
                "status": "REFERENCE_GUIDELINE_ONLY",
                "is_advisory": True,
            },
        },
    ]


class RunbookManager:
    """Manages satellite runbook registry and lookup."""

    def __init__(self, data_path: Optional[Path] = None) -> None:
        self.data_path = data_path or Path("data/historical/runbooks.json")
        self._runbooks: dict[str, RunbookEntry] = {}
        self.reload()

    def reload(self) -> None:
        """Load runbooks from JSON file with fallback to default definitions."""
        self._runbooks.clear()
        raw_entries: list[dict[str, Any]] = []

        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    raw_entries = json.load(f)
            except Exception:
                raw_entries = _get_default_runbooks()
        else:
            raw_entries = _get_default_runbooks()

        for entry in raw_entries:
            rb = RunbookEntry(
                runbook_id=entry["runbook_id"],
                title=entry["title"],
                subsystem=entry["subsystem"],
                applicable_anomalies=entry.get("applicable_anomalies", []),
                trigger_condition=entry.get("trigger_condition", ""),
                recommended_actions=entry.get("recommended_actions", []),
                diagnostic_checks=entry.get("diagnostic_checks", []),
                safety_constraints=entry.get("safety_constraints", []),
                rollback_procedure=entry.get("rollback_procedure", ""),
                metadata=entry.get("metadata", {}),
            )
            self._runbooks[rb.runbook_id] = rb

    def get_runbook(self, runbook_id: str) -> Optional[RunbookEntry]:
        return self._runbooks.get(runbook_id)

    def list_runbooks(self) -> list[RunbookEntry]:
        return list(self._runbooks.values())

    def find_by_anomaly(self, anomaly_type: str) -> list[RunbookEntry]:
        """Find runbooks applicable to a given anomaly type string."""
        if not anomaly_type:
            return []
        
        target = anomaly_type.strip().lower()
        matches = []
        for rb in self._runbooks.values():
            for app in rb.applicable_anomalies:
                if target == app.lower() or target in app.lower() or app.lower() in target:
                    matches.append(rb)
                    break
        return matches

    def find_by_subsystem(self, subsystem: str) -> list[RunbookEntry]:
        if not subsystem:
            return []
        subsys_clean = subsystem.strip().lower()
        return [
            rb for rb in self._runbooks.values()
            if rb.subsystem.lower() == subsys_clean
        ]
