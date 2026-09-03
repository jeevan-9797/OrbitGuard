"""Satellite telemetry simulator.

Generates realistic telemetry for virtual satellites and supports anomaly
injection (battery overheat, wheel degradation) with time-progressive
deterioration.
"""

from __future__ import annotations

import random
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Metric Baselines ─────────────────────────────────────────────────────────

_NORMAL_RANGES: dict[str, dict[str, Any]] = {
    "battery_temperature": {"min": 15.0, "max": 35.0, "unit": "degC", "subsystem": "EPS"},
    "battery_voltage": {"min": 26.0, "max": 28.5, "unit": "V", "subsystem": "EPS"},
    "solar_power": {"min": 80.0, "max": 120.0, "unit": "W", "subsystem": "EPS"},
    "wheel_speed": {"min": 2800.0, "max": 3200.0, "unit": "RPM", "subsystem": "ADCS"},
    "attitude_error": {"min": 0.0, "max": 0.05, "unit": "deg", "subsystem": "ADCS"},
    "comm_snr": {"min": 15.0, "max": 25.0, "unit": "dB", "subsystem": "COMMS"},
}

# Maximum telemetry readings retained per satellite
_MAX_HISTORY = 120


# ── Per-Satellite State ──────────────────────────────────────────────────────

@dataclass
class _SatelliteState:
    """Mutable runtime state for a single simulated satellite."""

    # Active anomaly injections mapped by type name
    active_anomalies: dict[str, float] = field(default_factory=dict)
    # Rolling telemetry history (most-recent last)
    history: deque[dict] = field(default_factory=lambda: deque(maxlen=_MAX_HISTORY))
    # Previous metric values for rate-of-change calculations
    prev_values: dict[str, float] = field(default_factory=dict)


# Global satellite states keyed by satellite_id
_satellites: dict[str, _SatelliteState] = {}


def _get_state(satellite_id: str) -> _SatelliteState:
    """Return (or create) the runtime state for *satellite_id*."""
    if satellite_id not in _satellites:
        _satellites[satellite_id] = _SatelliteState()
    return _satellites[satellite_id]


# ── Normal Telemetry Generation ──────────────────────────────────────────────

def generate_normal_telemetry(satellite_id: str) -> dict:
    """Generate a realistic telemetry snapshot for *satellite_id*.

    Returns a dict with a ``timestamp``, ``satellite_id``, and a ``metrics``
    mapping of metric-name -> ``{value, unit, subsystem}``.

    If anomaly injections are active the affected metrics are distorted
    accordingly.
    """
    state = _get_state(satellite_id)
    now = datetime.now(timezone.utc)
    metrics: dict[str, dict[str, Any]] = {}

    for metric_name, spec in _NORMAL_RANGES.items():
        # Start from a normal random value
        value = random.uniform(spec["min"], spec["max"])

        # Apply anomaly distortions if active
        if "battery_overheat" in state.active_anomalies and metric_name == "battery_temperature":
            elapsed = time.monotonic() - state.active_anomalies["battery_overheat"]
            # Temperature rises ~3 degC per second of elapsed sim-time, with noise
            value = 35.0 + elapsed * 3.0 + random.uniform(-0.5, 0.5)

        if "wheel_degradation" in state.active_anomalies:
            if metric_name == "wheel_speed":
                elapsed = time.monotonic() - state.active_anomalies["wheel_degradation"]
                # Speed fluctuates increasingly with time
                jitter = min(elapsed * 50.0, 800.0)
                value = 3000.0 + random.uniform(-jitter, jitter)
            elif metric_name == "attitude_error":
                elapsed = time.monotonic() - state.active_anomalies["wheel_degradation"]
                # Attitude error grows as wheel degrades
                value = 0.02 + elapsed * 0.15 + random.uniform(0.0, 0.05)

        metrics[metric_name] = {
            "value": round(value, 4),
            "unit": spec["unit"],
            "subsystem": spec["subsystem"],
        }

    snapshot = {
        "satellite_id": satellite_id,
        "timestamp": now.isoformat(),
        "metrics": metrics,
    }

    # Record history & previous values for rate-of-change detection
    state.history.append(snapshot)
    for m, data in metrics.items():
        state.prev_values[m] = data["value"]

    # Synchronize to DB
    try:
        import asyncio
        from app.services.db_sync import persist_telemetry_snapshot
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(persist_telemetry_snapshot(snapshot))
    except Exception:
        pass

    return snapshot



# ── Anomaly Injection ────────────────────────────────────────────────────────

def inject_battery_overheat(satellite_id: str) -> dict:
    """Begin a battery overheat anomaly for *satellite_id*.

    Subsequent calls to :func:`generate_normal_telemetry` will show
    progressively rising battery temperature.
    """
    state = _get_state(satellite_id)
    if "battery_overheat" not in state.active_anomalies:
        state.active_anomalies["battery_overheat"] = time.monotonic()
    return {
        "status": "injected",
        "satellite_id": satellite_id,
        "anomaly_type": "battery_overheat",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


def inject_wheel_degradation(satellite_id: str) -> dict:
    """Begin a reaction wheel degradation anomaly for *satellite_id*.

    Subsequent calls to :func:`generate_normal_telemetry` will show
    increasing wheel-speed jitter and rising attitude error.
    """
    state = _get_state(satellite_id)
    if "wheel_degradation" not in state.active_anomalies:
        state.active_anomalies["wheel_degradation"] = time.monotonic()
    return {
        "status": "injected",
        "satellite_id": satellite_id,
        "anomaly_type": "wheel_degradation",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Injection Dispatcher ────────────────────────────────────────────────────

_INJECTORS: dict[str, Any] = {
    "battery_overheat": inject_battery_overheat,
    "wheel_degradation": inject_wheel_degradation,
}


def inject_anomaly(satellite_id: str, anomaly_type: str) -> dict:
    """Dispatch to the correct injector by *anomaly_type* name."""
    injector = _INJECTORS.get(anomaly_type)
    if injector is None:
        available = ", ".join(_INJECTORS)
        raise ValueError(
            f"Unknown anomaly_type '{anomaly_type}'. Available: {available}"
        )
    return injector(satellite_id)


def remediate_anomaly(satellite_id: str, anomaly_type: str | None = None) -> dict:
    """Clear active anomaly injection(s) for a satellite upon recovery plan execution."""
    state = _get_state(satellite_id)
    cleared: list[str] = []
    if anomaly_type:
        if anomaly_type in state.active_anomalies:
            del state.active_anomalies[anomaly_type]
            cleared.append(anomaly_type)
    else:
        cleared = list(state.active_anomalies.keys())
        state.active_anomalies.clear()
    
    return {
        "status": "remediated",
        "satellite_id": satellite_id,
        "anomalies_cleared": cleared,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }




# ── Reset ────────────────────────────────────────────────────────────────────

def reset_simulator() -> dict:
    """Clear all satellite states and anomaly injections."""
    count = len(_satellites)
    _satellites.clear()
    return {
        "status": "reset",
        "satellites_cleared": count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── History Access ───────────────────────────────────────────────────────────

def get_telemetry_history(satellite_id: str, window: int = 30) -> list[dict]:
    """Return the most recent *window* telemetry snapshots for *satellite_id*."""
    state = _get_state(satellite_id)
    history = list(state.history)
    return history[-window:]


def get_previous_value(satellite_id: str, metric: str) -> float | None:
    """Return the last recorded value for *metric* on *satellite_id*."""
    state = _get_state(satellite_id)
    return state.prev_values.get(metric)
