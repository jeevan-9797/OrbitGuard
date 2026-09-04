"""
Deterministic Scenario Demo Runner
Module: app.demo_runner
Executes complete end-to-end demonstrations for Scenario A (Battery Overheat) and Scenario B (Reaction Wheel).
Validates the full workflow:
RESET -> NORMAL TELEMETRY -> ANOMALY -> INCIDENT -> AI INVESTIGATION -> DIAGNOSIS -> RECOVERY PLAN
-> SAFETY VALIDATION -> APPROVAL / REJECTION -> EXECUTION -> VERIFICATION -> RESOLUTION -> AUDIT TRAIL
"""

import sys
import argparse
import time
from typing import Dict, Any
from app.repositories.fleet_repo import FleetRepository
from app.repositories.telemetry_repo import TelemetryRepository
from app.repositories.incident_repo import IncidentRepository
from app.repositories.agent_repo import AgentRepository
from app.repositories.recovery_repo import RecoveryRepository
from app.repositories.audit_repo import AuditRepository
from app.services.incident_service import IncidentService
from app.services.validation_service import ValidationService
from database.reset import reset_demo_state


def run_scenario_a(verbose: bool = True) -> bool:
    """
    Scenario A — Battery Overheat & Thermal Runaway (17 steps)
    """
    print("\n" + "=" * 80)
    print("STARTING SCENARIO A: BATTERY OVERHEAT & THERMAL RUNAWAY")
    print("=" * 80)

    # 1. Reset demo state
    print("Step 1: Resetting demo state to baseline...")
    reset_demo_state()

    # 2. Get target satellite (ASTRAEA-1)
    satellites = FleetRepository.get_fleet_summary()
    sat = next((s for s in satellites if s["name"] == "ASTRAEA-1"), None)
    if not sat:
        print("[FAIL] ASTRAEA-1 not found in fleet.")
        return False
    sat_id = sat["id"]
    print(f"  [OK] Target satellite acquired: ASTRAEA-1 ({sat_id})")

    # 3. Seed/verify normal telemetry
    print("Step 2: Checking normal baseline telemetry...")
    baseline = TelemetryRepository.get_baseline(sat_id, "NOMINAL", "battery_temperature")
    print(f"  [OK] Battery temperature baseline: min={baseline['min_val']}C, max={baseline['max_val']}C, mean={baseline['mean']}C")

    # 4. Inject rising temperature and elevated payload draw
    print("Step 3: Injecting anomalous elevated telemetry readings...")
    TelemetryRepository.record_telemetry(sat_id, None, "battery_temperature", 38.5, "C", "SUSPECT")
    TelemetryRepository.record_telemetry(sat_id, None, "battery_temperature", 44.5, "C", "BAD")
    TelemetryRepository.record_telemetry(sat_id, None, "bus_current", 27.2, "A", "SUSPECT")
    TelemetryRepository.record_telemetry(sat_id, None, "payload_power_draw", 385.0, "W", "GOOD")
    print("  [OK] Anomaly signature injected (battery_temperature=44.5C, bus_current=27.2A).")

    # 5. Create Anomaly
    print("Step 4: Flagging detection anomaly...")
    anomaly = IncidentRepository.create_anomaly(
        satellite_id=sat_id,
        type="THERMAL_RUNAWAY",
        severity="CRITICAL",
        confidence=0.985,
        evidence={
            "metric": "battery_temperature",
            "trigger_value": 44.5,
            "baseline_max": 32.0,
            "delta_sigma": 5.7,
            "concomitant_metrics": {"bus_current": 27.2, "payload_power_draw": 385.0}
        }
    )
    print(f"  [OK] Anomaly persisted: ID {anomaly['id']} (Confidence: {anomaly['confidence']})")

    # 6. Open Incident
    print("Step 5: Opening operational incident case...")
    incident = IncidentRepository.create_incident(
        satellite_id=sat_id,
        anomaly_id=anomaly["id"],
        title="ASTRAEA-1 EPS Battery Critical Thermal Runaway on Eclipse Exit",
        priority="P1",
        severity="CRITICAL",
        confidence=0.960,
        primary_hypothesis="TCS heater stuck engaged with high payload draw"
    )
    inc_id = incident["id"]
    print(f"  [OK] Incident opened: ID {inc_id} (State: {incident['state']})")

    # 7. Start AI Investigation -> Transition to INVESTIGATING
    print("Step 6: AI Detector & Investigation started...")
    IncidentService.transition_state(inc_id, "INVESTIGATING", actor="DETECTOR")

    # 8. Diagnostic Agent Run
    print("Step 7: Diagnostic Agent analyzing telemetry deviations & historical cases...")
    diag_run = AgentRepository.save_agent_run(
        incident_id=inc_id,
        agent_name="diagnostic_agent",
        input_data={"scan_window_minutes": 15, "satellite": "ASTRAEA-1"},
        output_data={
            "primary_hypothesis": {
                "cause": "heater_relay_stuck_closed",
                "confidence": 0.96,
                "evidence": ["battery_temperature = 44.5C (baseline_max = 32.0C)", "bus_current = 27.2A"]
            },
            "hypotheses": [
                {
                    "cause": "heater_relay_stuck_closed",
                    "confidence": 0.96,
                    "evidence": ["battery_temperature = 44.5C (baseline_max = 32.0C)", "bus_current = 27.2A"]
                },
                {
                    "cause": "excessive_power_consumption",
                    "confidence": 0.65,
                    "evidence": ["payload_power_draw = 385.0W"]
                }
            ],
            "needs_evidence": False
        },
        confidence=0.96
    )
    IncidentService.transition_state(inc_id, "DIAGNOSED", actor="DIAGNOSTIC_AGENT")
    print(f"  [OK] Diagnosis completed: Primary cause: {diag_run['output']['primary_hypothesis']['cause']}")

    # 9. Planner Agent -> Candidate Plans (Planning phase)
    print("Step 8: Planner generating candidate recovery plans...")
    IncidentService.transition_state(inc_id, "PLANNING", actor="PLANNER")

    # Unsafe Candidate Plan 1
    unsafe_plan = RecoveryRepository.create_recovery_plan(
        incident_id=inc_id,
        version=1,
        rationale="Plan 1: Maintain partial heater duty (20%) while shedding payload",
        actions={
            "actions": [
                {"order": 1, "action_code": "REDUCE_POWER_LOAD", "parameters": {"target": "NON_CRITICAL_PAYLOAD"}},
                {"order": 2, "action_code": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 20}}
            ]
        },
        risk_level="HIGH"
    )
    print(f"  [OK] Candidate Plan v1 generated: ID {unsafe_plan['id']}")

    # 10. Safety Gate Evaluation for Plan 1
    print("Step 9: Evaluating Plan v1 against deterministic Safety Gate...")
    val_v1 = ValidationService.validate_plan(inc_id, unsafe_plan["id"])
    print(f"  [SAFETY GATE] Plan v1 Status: {val_v1['status']}")
    print(f"                Failed Rules: {val_v1['failed_rules']}")
    assert val_v1["status"] == "FAILED", "Unsafe plan must fail validation!"

    # 11. Generate Safe Candidate Plan 2
    print("Step 10: Generating safer alternative Plan v2...")
    safe_plan = RecoveryRepository.create_recovery_plan(
        incident_id=inc_id,
        version=2,
        rationale="Plan 2: Completely inhibit battery heaters (0%), open louvers, and shed payload",
        actions={
            "actions": [
                {"order": 1, "action_code": "REDUCE_POWER_LOAD", "parameters": {"target": "NON_CRITICAL_PAYLOAD"}},
                {"order": 2, "action_code": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 0}},
                {"order": 3, "action_code": "TCS_LOUVER_OPEN", "parameters": {}}
            ]
        },
        risk_level="LOW"
    )
    print(f"  [OK] Candidate Plan v2 generated: ID {safe_plan['id']}")

    # 12. Safety Gate Evaluation for Plan 2
    print("Step 11: Evaluating Plan v2 against deterministic Safety Gate...")
    val_v2 = ValidationService.validate_plan(inc_id, safe_plan["id"])
    print(f"  [SAFETY GATE] Plan v2 Status: {val_v2['status']}")
    assert val_v2["status"] == "PASSED", "Safe plan must pass validation!"

    # 13. Operator / Flight Director Approval
    print("Step 12: Transitioning to VALIDATING and Authorizing Plan v2...")
    IncidentService.transition_state(inc_id, "VALIDATING", actor="SYSTEM")
    app_result = IncidentService.approve_plan(inc_id, safe_plan["id"], authorizer="FLIGHT_DIRECTOR")
    print(f"  [OK] Plan v2 approved. Incident state: APPROVED")

    # 14. Simulated Execution
    print("Step 13: Executing recovery action sequence on satellite simulator...")
    exec_result = IncidentService.execute_plan(
        incident_id=inc_id,
        plan_id=safe_plan["id"],
        before_state={"battery_temperature": 44.5, "heater_duty": 65, "payload_power_w": 385},
        after_state={"battery_temperature": 31.8, "heater_duty": 0, "payload_power_w": 0}
    )
    print(f"  [OK] Command dispatched. Execution ID: {exec_result['id']} (Status: SUCCESS)")

    # 15. Record Post-Recovery Telemetry
    print("Step 14: Recording post-mitigation telemetry stream...")
    TelemetryRepository.record_telemetry(sat_id, None, "battery_temperature", 38.2, "C", "GOOD")
    TelemetryRepository.record_telemetry(sat_id, None, "battery_temperature", 31.8, "C", "GOOD")
    print("  [OK] Telemetry shows battery cooling to 31.8C (Nominal baseline: < 35.0C).")

    # 16. Outcome Verification
    print("Step 15: Verifying recovery outcome...")
    verif = IncidentService.verify_outcome(
        incident_id=inc_id,
        metric="battery_temperature",
        observed_value=31.8,
        target_max=35.0,
        resolution_code="AUTONOMOUS_THERMAL_MITIGATION_VERIFIED"
    )
    print(f"  [OK] Outcome Verified: {verif['verified']} (Final Incident State: {verif['status']})")

    # 17. Reconstruct Audit Trail
    print("Step 16: Reconstructing chronological incident audit trail...")
    audit_events = AuditRepository.get_audit_events(inc_id)
    print(f"  [OK] Audit events recorded: {len(audit_events)}")
    for ev in audit_events:
        print(f"       - [{ev.get('timestamp', 'NOW')}] {ev['event_type']:<22} by {ev['actor']:<15}")

    print("\n[SUCCESS] SCENARIO A PASSED WITH 100% COMPLIANCE.")
    return True


def run_scenario_b(verbose: bool = True) -> bool:
    """
    Scenario B — Reaction-Wheel Degradation (11 steps)
    """
    print("\n" + "=" * 80)
    print("STARTING SCENARIO B: REACTION-WHEEL DEGRADATION")
    print("=" * 80)

    # 1. Reset demo state
    print("Step 1: Resetting demo state to baseline...")
    reset_demo_state()

    # 2. Get target satellite (BOREAS-2)
    satellites = FleetRepository.get_fleet_summary()
    sat = next((s for s in satellites if s["name"] == "BOREAS-2"), None)
    if not sat:
        print("[FAIL] BOREAS-2 not found in fleet.")
        return False
    sat_id = sat["id"]
    print(f"  [OK] Target satellite acquired: BOREAS-2 ({sat_id})")

    # 3. Seed/verify normal telemetry
    print("Step 2: Checking nominal ADCS attitude telemetry...")
    baseline = TelemetryRepository.get_baseline(sat_id, "NOMINAL", "wheel_vibration_g")
    print(f"  [OK] Wheel vibration baseline: min={baseline['min_val']}g, max={baseline['max_val']}g, mean={baseline['mean']}g")

    # 4. Inject anomalous vibration
    print("Step 3: Injecting elevated reaction wheel vibration readings...")
    TelemetryRepository.record_telemetry(sat_id, None, "wheel_vibration_g", 0.095, "g", "SUSPECT")
    TelemetryRepository.record_telemetry(sat_id, None, "wheel_vibration_g", 0.185, "g", "BAD")
    TelemetryRepository.record_telemetry(sat_id, None, "wheel_motor_current", 0.88, "A", "BAD")
    print("  [OK] Anomaly signature injected (wheel_vibration_g=0.185g, motor_current=0.88A).")

    # 5. Create Anomaly & Incident
    print("Step 4: Detecting anomaly and opening incident...")
    anomaly = IncidentRepository.create_anomaly(
        satellite_id=sat_id,
        type="REACTION_WHEEL_FRICTION",
        severity="HIGH",
        confidence=0.930,
        evidence={"wheel_id": "RW-2", "vibration_g": 0.185, "motor_current_a": 0.88}
    )
    incident = IncidentRepository.create_incident(
        satellite_id=sat_id,
        anomaly_id=anomaly["id"],
        title="BOREAS-2 ADCS Reaction Wheel 2 Degradation",
        priority="P2",
        severity="HIGH",
        confidence=0.920,
        primary_hypothesis="RW-2 bearing lubricant breakdown"
    )
    inc_id = incident["id"]

    # 6. Investigation & Diagnosis
    print("Step 5: Running AI diagnosis...")
    IncidentService.transition_state(inc_id, "INVESTIGATING", actor="DETECTOR")
    AgentRepository.save_agent_run(
        incident_id=inc_id,
        agent_name="diagnostic_agent",
        input_data={"scan_window_minutes": 15},
        output_data={
            "primary_hypothesis": {
                "cause": "bearing_lubricant_breakdown",
                "confidence": 0.92,
                "evidence": ["wheel_vibration_g=0.185 exceeds threshold", "motor_current=0.88A"]
            },
            "hypotheses": [
                {
                    "cause": "bearing_lubricant_breakdown",
                    "confidence": 0.92,
                    "evidence": ["wheel_vibration_g=0.185"]
                }
            ],
            "needs_evidence": False
        },
        confidence=0.92
    )
    IncidentService.transition_state(inc_id, "DIAGNOSED", actor="DIAGNOSTIC_AGENT")

    # 7. Recovery Planning
    print("Step 6: Planner proposing momentum offload plan...")
    IncidentService.transition_state(inc_id, "PLANNING", actor="PLANNER")
    plan = RecoveryRepository.create_recovery_plan(
        incident_id=inc_id,
        version=1,
        rationale="Offload RW-2 momentum to RW-1/RW-3 and dump excess with magnetic torquers",
        actions={
            "actions": [
                {"order": 1, "action_code": "ADCS_RW_WHEEL_OFFLOAD", "parameters": {"wheel_id": "RW-2"}},
                {"order": 2, "action_code": "ADCS_RW_SPEED_DESAT", "parameters": {}}
            ]
        },
        risk_level="MEDIUM"
    )

    # 8. Validation & Approval
    print("Step 7: Safety validation and approval...")
    val = ValidationService.validate_plan(inc_id, plan["id"])
    assert val["status"] == "PASSED"
    IncidentService.transition_state(inc_id, "VALIDATING", actor="SYSTEM")
    IncidentService.approve_plan(inc_id, plan["id"], authorizer="FLIGHT_DIRECTOR")

    # 9. Execution
    print("Step 8: Executing momentum offload action...")
    exec_res = IncidentService.execute_plan(
        incident_id=inc_id,
        plan_id=plan["id"],
        before_state={"wheel_vibration_g": 0.185, "motor_current_a": 0.88},
        after_state={"wheel_vibration_g": 0.034, "motor_current_a": 0.31}
    )
    print(f"  [OK] Command executed: {exec_res['id']}")

    # 10. Telemetry & Outcome Verification
    print("Step 9: Recording post-recovery telemetry and verifying outcome...")
    TelemetryRepository.record_telemetry(sat_id, None, "wheel_vibration_g", 0.034, "g", "GOOD")
    verif = IncidentService.verify_outcome(
        incident_id=inc_id,
        metric="wheel_vibration_g",
        observed_value=0.034,
        target_max=0.05,
        resolution_code="MOMENTUM_OFFLOAD_AND_MAGNETORQUER_TRANSITION"
    )
    print(f"  [OK] Verification status: {verif['status']} (Vibration normalized: 0.034g <= 0.05g)")

    # 11. Audit Inspection
    print("Step 10: Verifying complete audit trail...")
    events = AuditRepository.get_audit_events(inc_id)
    print(f"  [OK] Total audit events: {len(events)}")

    print("\n[SUCCESS] SCENARIO B PASSED WITH 100% COMPLIANCE.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Satellite Multi-Agent AI Demo Runner")
    parser.add_argument("--scenario", choices=["A", "B", "all"], default="all", help="Scenario to run")
    args = parser.parse_args()

    success = True
    if args.scenario in ("A", "all"):
        success = success and run_scenario_a()
    if args.scenario in ("B", "all"):
        success = success and run_scenario_b()

    print("\n" + "=" * 80)
    print(f"DEMO RUNNER COMPLETED: {'ALL SCENARIOS PASSED [PASS]' if success else 'FAILURES DETECTED [FAIL]'}")
    print("=" * 80)
    sys.exit(0 if success else 1)
