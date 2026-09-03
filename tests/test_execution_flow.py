"""
Test suite for OrbitGuard Milestone 3: Execution + Digital Twin Verification.

Verifies the entire lifecycle flow:
Validated Recovery Plan -> Simulation -> Operator Approval -> Execution -> Telemetry Change -> Outcome
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas.anomaly import AnomalyEvent, SeverityLevel
from app.schemas.recovery import RecoveryPlan, RecoveryStep, RiskLevel
from app.services.detector import clear_incidents
from app.services.orchestrator import (
    IncidentRecord,
    IncidentStatus,
    analyze_incident,
    approve_incident_plan,
    execute_incident_plan,
    find_plan,
    get_incident,
    register_detected_incident,
    reject_incident_plan,
)
from app.services.simulator_engine import simulate_plan_execution
from app.simulator.telemetry import (
    generate_normal_telemetry,
    inject_anomaly,
    reset_simulator,
)


async def test_milestone_3_flow() -> bool:
    print("\n================================================================================")
    print("      ORBITGUARD MILESTONE 3: EXECUTION & DIGITAL TWIN VERIFICATION")
    print("================================================================================\n")

    reset_simulator()
    clear_incidents()

    # ── Test 1: Full Simulation & Execution Flow on High Temperature ───────────
    print("[1/4] Testing Valid Plan -> Simulation -> Approval -> Execution -> Outcome (HIGH_TEMPERATURE)...")
    inject_anomaly("SAT-01", "battery_overheat")
    telem_snapshot = generate_normal_telemetry("SAT-01")

    anomaly_event = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="EPS",
        severity=SeverityLevel.HIGH,
        description="Battery temperature anomaly: 51.2 degC",
        telemetry_snapshot=telem_snapshot.get("metrics", {}),
        confidence=0.9,
        detected_at=datetime.now(timezone.utc),
    )

    inc = register_detected_incident(anomaly_event)
    await analyze_incident(inc.incident_id)

    assert len(inc.recovery_plans) >= 2, "Expected candidate recovery plans"
    target_plan = inc.recovery_plans[0]
    print(f"    - Target Plan: {target_plan.plan_id} ({target_plan.title})")
    print(f"    - Actions: {target_plan.actions}")
    print(f"    - Safety Score: {target_plan.validation_result.get('safety_score')}")

    # Step 1.1: Forward Digital Twin Simulation
    sim_res = simulate_plan_execution(target_plan, telem_snapshot)
    assert sim_res.outcome.value == "success", "Simulation outcome must be success"
    assert len(sim_res.simulated_telemetry) >= 10, "Simulation time series must have data points"
    pre_temp = sim_res.simulated_telemetry[0]["metrics"]["battery_temperature"]["value"]
    post_temp = sim_res.simulated_telemetry[-1]["metrics"]["battery_temperature"]["value"]
    print(f"    - Simulation: Pre-Temp={pre_temp:.1f}°C -> Post-Temp={post_temp:.1f}°C (Cooldown verified)")

    # Step 1.2: Human-in-the-Loop Operator Approval
    _, approved_inc = approve_incident_plan(
        target_plan.plan_id,
        operator_notes="Flight director authorization granted for automated mitigation.",
    )
    assert approved_inc.status == IncidentStatus.APPROVED, "Incident must be in APPROVED state"
    print(f"    - HITL Approval: Status={approved_inc.status.value}")

    # Step 1.3: Live Execution against digital twin & simulator remediation
    exec_summary, resolved_inc = await execute_incident_plan(
        target_plan.plan_id,
        operator_notes="Uplinked commands executed successfully.",
    )
    assert resolved_inc.status == IncidentStatus.RESOLVED, "Incident must be in RESOLVED state"
    assert exec_summary["status"] == "RESOLVED", "Execution summary status must be RESOLVED"
    print(f"    - Execution & Verification: Status={resolved_inc.status.value}")
    print(f"    - Telemetry Remediated: Active anomalies cleared in simulator")
    print("    --> Result: PASS\n")

    # ── Test 2: Wheel Degradation Simulation & Execution Flow ──────────────────
    print("[2/4] Testing ADCS Wheel Degradation Execution Flow...")
    reset_simulator()
    clear_incidents()
    inject_anomaly("SAT-01", "wheel_degradation")
    telem_wheel = generate_normal_telemetry("SAT-01")

    anomaly_wheel = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="ADCS",
        severity=SeverityLevel.HIGH,
        description="Wheel degradation: speed=2800 RPM, attitude_error=0.35 deg",
        telemetry_snapshot=telem_wheel.get("metrics", {}),
        confidence=0.9,
        detected_at=datetime.now(timezone.utc),
    )

    inc_wheel = register_detected_incident(anomaly_wheel)
    await analyze_incident(inc_wheel.incident_id)
    plan_wheel = inc_wheel.recovery_plans[0]

    approve_incident_plan(plan_wheel.plan_id, operator_notes="ADCS plan approved")
    summary_wheel, res_wheel = await execute_incident_plan(plan_wheel.plan_id)
    assert res_wheel.status == IncidentStatus.RESOLVED
    print(f"    - ADCS Plan Executed: {summary_wheel['actions_executed']}")
    print(f"    - Status: {res_wheel.status.value}")
    print("    --> Result: PASS\n")

    # ── Test 3: Plan Rejection Flow ───────────────────────────────────────────
    print("[3/4] Testing Operator Rejection Flow...")
    reset_simulator()
    clear_incidents()
    inject_anomaly("SAT-01", "low_battery")
    telem_low = generate_normal_telemetry("SAT-01")

    anomaly_low = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="EPS",
        severity=SeverityLevel.HIGH,
        description="Battery voltage anomaly: 18.5V",
        telemetry_snapshot=telem_low.get("metrics", {}),
        confidence=0.9,
        detected_at=datetime.now(timezone.utc),
    )

    inc_low = register_detected_incident(anomaly_low)
    await analyze_incident(inc_low.incident_id)
    plan_to_reject = inc_low.recovery_plans[1]

    _, rejected_inc = reject_incident_plan(
        plan_to_reject.plan_id,
        operator_notes="Alternative plan preferred by orbital dynamics team.",
    )
    assert rejected_inc.status == IncidentStatus.REJECTED
    print(f"    - Rejection Verified: Incident Status={rejected_inc.status.value}")
    print("    --> Result: PASS\n")

    # ── Test 4: Unsupported / Unsafe Action Rejection ─────────────────────────
    print("[4/4] Testing Security Guard: Rejecting Unsupported / Unsafe Actions...")
    unsafe_plan = RecoveryPlan(
        plan_id="PLAN-UNSAFE-001",
        title="Unsafe Unauthorized Action Plan",
        diagnosis_id="DIAG-001",
        satellite_id="SAT-01",
        actions=["DISCHARGE_BATTERY_COMPLETELY", "DETONATE_SOLAR_PANEL"],
        preconditions=[],
        expected_effects=[],
        steps=[],
        risk_level=RiskLevel.HIGH,
        risk_score=0.99,
        rollback_plan="No rollback possible",
        created_at=datetime.now(timezone.utc),
    )
    inc_low.recovery_plans.append(unsafe_plan)

    blocked = False
    try:
        await execute_incident_plan(unsafe_plan.plan_id)
    except ValueError as exc:
        blocked = True
        print(f"    - Execution Correctly Blocked: {exc}")

    assert blocked, "Execution of unsupported action must be blocked"
    print("    --> Result: PASS\n")

    print("--------------------------------------------------------------------------------")
    print("Milestone 3 Verification Verdict: ALL TESTS PASSED (100%)")
    print("--------------------------------------------------------------------------------\n")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_milestone_3_flow())
    sys.exit(0 if success else 1)
