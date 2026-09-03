"""
OrbitGuard telemetry simulator.

Generates deterministic-ish spacecraft telemetry for normal operation
and injected anomaly scenarios.
"""

from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

_NORMAL_RANGES = {
    "battery_temperature": {
        "min": 15.0,
        "max": 35.0,
        "unit": "degC",
        "subsystem": "EPS",
    },
    "battery_voltage": {
        "min": 26.0,
        "max": 28.5,
        "unit": "V",
        "subsystem": "EPS",
    },
    "solar_power": {
        "min": 80.0,
        "max": 120.0,
        "unit": "W",
        "subsystem": "EPS",
    },
    "wheel_speed": {
        "min": 2800.0,
        "max": 3200.0,
        "unit": "RPM",
        "subsystem": "ADCS",
    },
    "attitude_error": {
        "min": 0.0,
        "max": 0.05,
        "unit": "deg",
        "subsystem": "ADCS",
    },
    "comm_snr": {
        "min": 15.0,
        "max": 25.0,
        "unit": "dB",
        "subsystem": "COMMS",
    },
}


_MAX_HISTORY = 120


@dataclass
class _SatelliteState:
    active_anomalies: dict[str, float] = field(default_factory=dict)
    history: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=_MAX_HISTORY)
    )
    prev_values: dict[str, float] = field(default_factory=dict)


_satellites: dict[str, _SatelliteState] = {}


def _get_state(satellite_id: str) -> _SatelliteState:
    if satellite_id not in _satellites:
        _satellites[satellite_id] = _SatelliteState()

    return _satellites[satellite_id]


async def _persist_telemetry(snapshot: dict[str, Any]) -> None:
    """
    Persist telemetry if the database service is available.

    Persistence failure must not break the simulator.
    """
    try:
        from app.services.db_sync import persist_telemetry

        result = persist_telemetry(snapshot)

        if hasattr(result, "__await__"):
            await result

    except Exception:
        # Telemetry generation must remain usable even if persistence
        # is unavailable during local/demo execution.
        pass


def generate_normal_telemetry(satellite_id: str) -> dict[str, Any]:
    """
    Generate one telemetry snapshot.

    Injected scenarios override the corresponding normal telemetry values.
    """

    state = _get_state(satellite_id)

    now = datetime.now(timezone.utc)

    metrics: dict[str, dict[str, Any]] = {}

    for metric_name, config in _NORMAL_RANGES.items():

        value = random.uniform(
            config["min"],
            config["max"],
        )

        # --------------------------------------------------------
        # LOW BATTERY SCENARIO
        # --------------------------------------------------------

        if (
            "low_battery" in state.active_anomalies
            and metric_name == "battery_voltage"
        ):
            value = 18.5 + random.uniform(-0.15, 0.15)

        # Keep battery temperature reasonable during low battery.
        if (
            "low_battery" in state.active_anomalies
            and metric_name == "battery_temperature"
        ):
            value = 24.2 + random.uniform(-0.3, 0.3)

        # Add charging current information during low battery.
        if (
            "low_battery" in state.active_anomalies
            and metric_name == "solar_power"
        ):
            value = random.uniform(0.0, 10.0)

        # --------------------------------------------------------
        # BATTERY OVERHEAT SCENARIO
        # --------------------------------------------------------

        if (
            "battery_overheat" in state.active_anomalies
            and metric_name == "battery_temperature"
        ):
            started = state.active_anomalies["battery_overheat"]
            elapsed = max(0.0, time.monotonic() - started)

            value = 48.0 + elapsed * 3.0 + random.uniform(-0.5, 0.5)

        # --------------------------------------------------------
        # WHEEL DEGRADATION SCENARIO
        # --------------------------------------------------------

        if "wheel_degradation" in state.active_anomalies:

            started = state.active_anomalies["wheel_degradation"]
            elapsed = max(0.0, time.monotonic() - started)

            if metric_name == "wheel_speed":
                jitter = min(800.0, 450.0 + elapsed * 20.0)
                value = 3000.0 + random.uniform(-jitter, jitter)

            elif metric_name == "attitude_error":
                error = min(0.8, 0.3 + elapsed * 0.03)
                value = random.uniform(
                    error * 0.8,
                    error * 1.2,
                )

        metrics[metric_name] = {
            "value": round(value, 4),
            "unit": config["unit"],
            "subsystem": config["subsystem"],
        }

        state.prev_values[metric_name] = float(value)

    snapshot = {
        "satellite_id": satellite_id,
        "timestamp": now.isoformat(),
        "metrics": metrics,
    }

    state.history.append(snapshot)

    return snapshot


def inject_battery_overheat(satellite_id: str) -> dict[str, Any]:
    """Inject a battery thermal anomaly."""

    state = _get_state(satellite_id)

    if "battery_overheat" not in state.active_anomalies:
        state.active_anomalies["battery_overheat"] = time.monotonic()

    return {
        "satellite_id": satellite_id,
        "anomaly_type": "battery_overheat",
        "status": "injected",
    }


def inject_low_battery(satellite_id: str) -> dict[str, Any]:
    """Inject a dedicated low-battery scenario."""

    state = _get_state(satellite_id)

    state.active_anomalies["low_battery"] = time.monotonic()

    return {
        "satellite_id": satellite_id,
        "anomaly_type": "low_battery",
        "status": "injected",
    }


def inject_wheel_degradation(satellite_id: str) -> dict[str, Any]:
    """Inject a reaction-wheel degradation scenario."""

    state = _get_state(satellite_id)

    if "wheel_degradation" not in state.active_anomalies:
        state.active_anomalies["wheel_degradation"] = time.monotonic()

    return {
        "satellite_id": satellite_id,
        "anomaly_type": "wheel_degradation",
        "status": "injected",
    }


_INJECTORS = {
    "battery_overheat": inject_battery_overheat,
    "low_battery": inject_low_battery,
    "wheel_degradation": inject_wheel_degradation,
}


def inject_anomaly(
    satellite_id: str,
    anomaly_type: str,
) -> dict[str, Any]:
    """Inject a supported anomaly scenario."""

    injector = _INJECTORS.get(anomaly_type)

    if injector is None:
        available = ", ".join(sorted(_INJECTORS))

        raise ValueError(
            f"Unsupported anomaly type '{anomaly_type}'. "
            f"Available: {available}"
        )

    return injector(satellite_id)


def remediate_anomaly(
    satellite_id: str,
    anomaly_type: str | None = None,
) -> dict[str, Any]:
    """Remove an active anomaly scenario or clear all active anomalies."""

    state = _get_state(satellite_id)

    if anomaly_type is None:
        cleared_count = len(state.active_anomalies)
        state.active_anomalies.clear()
        return {
            "satellite_id": satellite_id,
            "anomaly_type": "all",
            "status": "remediated" if cleared_count > 0 else "not_active",
        }

    removed = state.active_anomalies.pop(
        anomaly_type,
        None,
    )

    return {
        "satellite_id": satellite_id,
        "anomaly_type": anomaly_type,
        "status": "remediated" if removed is not None else "not_active",
    }


def reset_simulator() -> None:
    """Reset all satellite simulator state."""

    _satellites.clear()


def get_telemetry_history(
    satellite_id: str,
    limit: int = 30,
    window: int | None = None,
) -> list[dict[str, Any]]:
    """Return recent telemetry history.

    Supports both ``limit=`` and the backend's existing
    ``window=`` calling convention.
    """

    state = _get_state(satellite_id)

    if window is not None:
        limit = window

    if limit <= 0:
        return []

    return list(state.history)[-limit:]


def get_previous_value(
    satellite_id: str,
    metric_name: str,
) -> float | None:
    """Return the previous generated value for a metric."""

    state = _get_state(satellite_id)

    return state.prev_values.get(metric_name)