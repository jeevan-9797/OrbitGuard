"""Digital Twin Simulation Engine for Spacecraft Recovery Plans.

Performs forward simulation of recovery actions against simulated physical metrics
over time, projecting pre-execution, in-flight execution, and post-stabilization dynamics.
"""

from __future__ import annotations

import copy
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.schemas.recovery import RecoveryPlan
from app.schemas.simulation import SimulationOutcome, SimulationResult

logger = logging.getLogger(__name__)


def _extract_metric_val(metrics: dict[str, Any], name: str, default: float) -> float:
    """Helper to extract numeric value from metrics dictionary."""
    if not metrics:
        return default
    m = metrics.get(name)
    if isinstance(m, dict) and "value" in m:
        return float(m["value"])
    if isinstance(m, (int, float)):
        return float(m)
    return default


def simulate_plan_execution(
    plan: RecoveryPlan,
    initial_telemetry: dict[str, Any] | None = None,
    intervals_count: int = 12,
) -> SimulationResult:
    """Run a forward digital twin simulation of recovery plan execution.

    Physics models:
    - REDUCE_PAYLOAD_LOAD: Drops power by 35W and starts battery temperature decay (-1.5°C/step).
    - ENTER_SAFE_THERMAL_MODE: Accelerates thermal cooling (-3.0°C/step).
    - SWITCH_REDUNDANT_SENSOR: Restores wheel speed to nominal 3000 RPM (±15 RPM) and attitude error < 0.04°.
    - REDUCE_MANEUVER_ACTIVITY: Quenches slew attitude error and momentum buildup.
    - SWITCH_COMM_PROFILE: Reduces RF dissipation and bus current.

    Returns a SimulationResult with simulated_telemetry time-series (pre, during, post)
    and detailed step checkpoints.
    """
    now = datetime.now(timezone.utc)
    base_metrics: dict[str, Any] = {}

    if initial_telemetry:
        if "metrics" in initial_telemetry:
            base_metrics = initial_telemetry["metrics"]
        else:
            base_metrics = initial_telemetry

    # Seed current initial physical state
    curr_temp = _extract_metric_val(base_metrics, "battery_temperature", 48.5)
    curr_volt = _extract_metric_val(base_metrics, "battery_voltage", 27.2)
    curr_power = _extract_metric_val(base_metrics, "solar_power", 105.0)
    curr_wheel = _extract_metric_val(base_metrics, "wheel_speed", 3450.0)
    curr_att_err = _extract_metric_val(base_metrics, "attitude_error", 0.42)
    curr_snr = _extract_metric_val(base_metrics, "comm_snr", 20.0)

    # Gather actions to execute
    action_list = plan.actions if plan.actions else [s.action for s in plan.steps]

    time_series: list[dict[str, Any]] = []
    steps_executed: list[dict[str, Any]] = []
    side_effects: list[str] = []
    log_lines: list[str] = [
        f"[{now.isoformat()}] Digital Twin Forward Simulation initiated for Plan: {plan.plan_id}",
        f"[{now.isoformat()}] Initial State: Temp={curr_temp:.1f}°C, Wheel={curr_wheel:.0f} RPM, AttitudeErr={curr_att_err:.3f}°",
    ]

    # ── Phase 1: Pre-Execution Baseline (T-2, T-1) ───────────────────────────
    for t_idx in range(-2, 0):
        t_stamp = (now + timedelta(seconds=t_idx * 10)).isoformat()
        time_series.append({
            "step_phase": "PRE_EXECUTION",
            "interval": t_idx,
            "timestamp": t_stamp,
            "metrics": {
                "battery_temperature": {"value": round(curr_temp, 2), "unit": "degC"},
                "battery_voltage": {"value": round(curr_volt, 2), "unit": "V"},
                "solar_power": {"value": round(curr_power, 2), "unit": "W"},
                "wheel_speed": {"value": round(curr_wheel, 1), "unit": "RPM"},
                "attitude_error": {"value": round(curr_att_err, 4), "unit": "deg"},
                "comm_snr": {"value": round(curr_snr, 1), "unit": "dB"},
            },
        })

    # ── Phase 2: In-Flight Step Execution (T=0 to T=6) ───────────────────────
    # Apply effects progressively as steps execute
    applied_actions: set[str] = set()

    for t_step in range(0, 7):
        t_stamp = (now + timedelta(seconds=t_step * 15)).isoformat()
        phase_label = "IN_EXECUTION"

        # Trigger step 1 at t_step=1, step 2 at t_step=3
        if t_step == 1 and len(action_list) >= 1:
            act = action_list[0]
            applied_actions.add(act)
            log_lines.append(f"[{t_stamp}] Executing Step 1: {act}")
            steps_executed.append({
                "step_index": 1,
                "action": act,
                "status": "COMPLETED",
                "timestamp": t_stamp,
                "effect": f"Applied {act} dynamic remediation",
            })
            if act == "REDUCE_PAYLOAD_LOAD":
                side_effects.append("Non-essential instrument science capture paused during load shed.")
            elif act == "SWITCH_REDUNDANT_SENSOR":
                side_effects.append("ADCS primary sensor line switched to secondary backup channel.")

        if t_step == 3 and len(action_list) >= 2:
            act = action_list[1]
            applied_actions.add(act)
            log_lines.append(f"[{t_stamp}] Executing Step 2: {act}")
            steps_executed.append({
                "step_index": 2,
                "action": act,
                "status": "COMPLETED",
                "timestamp": t_stamp,
                "effect": f"Applied {act} dynamic remediation",
            })
            if act == "ENTER_SAFE_THERMAL_MODE":
                side_effects.append("Spacecraft solar offset introduces minor temporary power intake reduction.")
            elif act == "SWITCH_COMM_PROFILE":
                side_effects.append("Telemetry downlink bitrate throttled to safe beacon mode.")

        # Simulate physics decay/stabilization based on applied actions
        if "REDUCE_PAYLOAD_LOAD" in applied_actions:
            curr_power = max(60.0, curr_power - 5.0)
            curr_temp = max(28.0, curr_temp - 1.5)

        if "ENTER_SAFE_THERMAL_MODE" in applied_actions:
            curr_temp = max(24.0, curr_temp - 3.0)
            curr_volt = max(26.2, curr_volt - 0.05)

        if "SWITCH_REDUNDANT_SENSOR" in applied_actions:
            # Settle wheel speed to 3000 RPM
            curr_wheel = 3000.0 + (curr_wheel - 3000.0) * 0.4
            curr_att_err = max(0.02, curr_att_err * 0.4)

        if "REDUCE_MANEUVER_ACTIVITY" in applied_actions:
            curr_att_err = max(0.015, curr_att_err * 0.5)
            curr_wheel = 3000.0 + (curr_wheel - 3000.0) * 0.6

        if "SWITCH_COMM_PROFILE" in applied_actions:
            curr_snr = max(14.0, curr_snr - 1.0)

        time_series.append({
            "step_phase": phase_label,
            "interval": t_step,
            "timestamp": t_stamp,
            "metrics": {
                "battery_temperature": {"value": round(curr_temp, 2), "unit": "degC"},
                "battery_voltage": {"value": round(curr_volt, 2), "unit": "V"},
                "solar_power": {"value": round(curr_power, 2), "unit": "W"},
                "wheel_speed": {"value": round(curr_wheel, 1), "unit": "RPM"},
                "attitude_error": {"value": round(curr_att_err, 4), "unit": "deg"},
                "comm_snr": {"value": round(curr_snr, 1), "unit": "dB"},
            },
        })

    # ── Phase 3: Post-Execution Stabilization (T=7 to T=10) ──────────────────
    for t_post in range(7, intervals_count):
        t_stamp = (now + timedelta(seconds=t_post * 15)).isoformat()
        # Full nominal stabilization
        if curr_temp > 32.0:
            curr_temp = max(26.0, curr_temp - 1.0)
        curr_wheel = 3000.0 + (curr_wheel - 3000.0) * 0.2
        curr_att_err = max(0.018, curr_att_err * 0.7)

        time_series.append({
            "step_phase": "POST_RECOVERY",
            "interval": t_post,
            "timestamp": t_stamp,
            "metrics": {
                "battery_temperature": {"value": round(curr_temp, 2), "unit": "degC"},
                "battery_voltage": {"value": round(curr_volt, 2), "unit": "V"},
                "solar_power": {"value": round(curr_power, 2), "unit": "W"},
                "wheel_speed": {"value": round(curr_wheel, 1), "unit": "RPM"},
                "attitude_error": {"value": round(curr_att_err, 4), "unit": "deg"},
                "comm_snr": {"value": round(curr_snr, 1), "unit": "dB"},
            },
        })

    log_lines.append(
        f"[{datetime.now(timezone.utc).isoformat()}] Simulation completed. Final State: Temp={curr_temp:.1f}°C, Wheel={curr_wheel:.0f} RPM, AttErr={curr_att_err:.4f}°"
    )

    # Success probability computation
    prob = max(0.70, min(0.99, 1.0 - (plan.risk_score * 0.35)))

    return SimulationResult(
        simulation_id=f"SIM-{uuid.uuid4().hex[:8].upper()}",
        plan_id=plan.plan_id,
        satellite_id=plan.satellite_id,
        outcome=SimulationOutcome.SUCCESS,
        success_probability=round(prob, 2),
        side_effects=list(set(side_effects)),
        recommended_adjustments=[
            "Monitor battery temperature gradient for 15 minutes post-stabilization.",
            "Verify backup star-tracker alignment prior to commanding payload resume.",
        ],
        simulated_telemetry=time_series,
        steps_executed=steps_executed,
        logs="\n".join(log_lines),
        simulated_at=datetime.now(timezone.utc),
    )
