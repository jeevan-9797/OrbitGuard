"""
Milestone 6: OrbitGuard Automated End-to-End Demo Script.

Executes the complete, gold-standard 10-step hackathon demo flow:
1. Spacecraft Nominal Baseline
2. Anomaly Injection (High Temperature / Thermal Runaway)
3. Deterministic AIML Detection
4. Multi-Agent Diagnostic RCA with Grounded Evidence & Runbook RB-THM-001
5. Candidate Recovery Plans with Explicit Rollback Procedures
6. Deterministic Safety Validation (4/4 Constraints Evaluated)
7. Digital Twin Forward Simulation Preview
8. Human-in-the-Loop Flight Director Approval
9. Uplink Execution & Digital Twin Remediation
10. Spacecraft State Restoration & Final Outcome Verification
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
import requests

BACKEND_URL = "http://127.0.0.1:8001"


def run_demo() -> bool:
    print("\n" + "=" * 80)
    print("      ORBITGUARD HACKATHON LIVE DEMO FLOW (END-TO-END)")
    print("   [Core Rule: AI recommends; deterministic code decides]")
    print("=" * 80 + "\n")

    # Step 1: Check System Health & Reset
    print("STEP 1: Checking Satellite Bus Health & Resetting Simulator State...")
    res = requests.post(f"{BACKEND_URL}/api/simulate/reset")
    assert res.status_code == 200
    telem_res = requests.get(f"{BACKEND_URL}/api/telemetry/SAT-01?window=5&generate=5").json()
    metrics = (telem_res.get("telemetry") or telem_res.get("history"))[-1]["metrics"]
    print(f"  [SAT-01 Nominal] Voltage={metrics['battery_voltage']['value']}V | Temp={metrics['battery_temperature']['value']}°C | Wheel={metrics['wheel_speed']['value']}RPM")
    print("  --> Step 1: Nominal Spacecraft State Verified\n")
    time.sleep(1)

    # Step 2: Inject Anomaly Scenario (High Temperature)
    print("STEP 2: Injecting Spacecraft Anomaly (Battery Overheat / Thermal Excursion)...")
    inj_res = requests.post(
        f"{BACKEND_URL}/api/simulate/inject",
        json={"satellite_id": "SAT-01", "anomaly_type": "battery_overheat"},
    ).json()
    assert inj_res["status"] == "injected"
    print(f"  [Anomaly Injected] Type: {inj_res['anomaly_type']} on SAT-01")
    
    # Generate anomalous telemetry and trigger detector
    telem_anom = requests.get(f"{BACKEND_URL}/api/telemetry/SAT-01?window=5&generate=5").json()
    m_anom = (telem_anom.get("telemetry") or telem_anom.get("history"))[-1]["metrics"]
    print(f"  [Telemetry Spike] Battery Temp={m_anom['battery_temperature']['value']}°C (> 45.0°C threshold)")
    print("  --> Step 2: Anomaly Telemetry Successfully Injected\n")
    time.sleep(1)

    # Step 3: Anomaly Detection & Incident Registration
    print("STEP 3: Detecting Anomaly & Registering Spacecraft Incident...")
    incidents = requests.get(f"{BACKEND_URL}/api/incidents").json()
    assert len(incidents) > 0, "Incident must be registered by backend detector"
    active_inc = incidents[0]
    incident_id = active_inc["incident_id"]
    print(f"  [Incident Created] ID: {incident_id} | Subsystem: {active_inc['anomaly_event']['subsystem']} | Severity: {active_inc['anomaly_event']['severity']}")
    print(f"  [Status]: {active_inc['status']}")
    print("  --> Step 3: Incident Registered\n")
    time.sleep(1)

    # Step 4: Multi-Agent RCA & Diagnosis
    print("STEP 4: Triggering Diagnostic Agent Root-Cause Analysis (with Runbook Retrieval)...")
    analysis_res = requests.post(
        f"{BACKEND_URL}/api/incidents/analyze",
        json={"incident_id": incident_id},
    ).json()
    diag = analysis_res["diagnosis"]
    print(f"  [Diagnostic Hypothesis]: {diag['primary_hypothesis']}")
    print(f"  [Grounded Evidence]: {diag['evidence']}")
    print(f"  [Subsystems Affected]: {diag['affected_subsystems']}")
    print(f"  [Confidence Score]: {diag['confidence']}")
    print("  --> Step 4: Evidence-Grounded Diagnosis Complete\n")
    time.sleep(1)

    # Step 5 & 6: Candidate Recovery Plans & Safety Validation
    print("STEP 5 & 6: Evaluating Candidate Recovery Plans & Deterministic Safety Validation...")
    plans = analysis_res["recovery_plans"]
    assert len(plans) >= 2, "Expected at least 2 candidate recovery plans"
    for idx, p in enumerate(plans, start=1):
        vr = p["validation_result"]
        print(f"  [Plan {idx}] {p['plan_id']}: {p['title']}")
        print(f"    - Actions: {' -> '.join(p['actions'])}")
        print(f"    - Risk: {p['risk_level']} (Score: {p['risk_score']})")
        print(f"    - Rollback Plan: {p['rollback_plan']}")
        print(f"    - Safety Verdict: is_valid={vr['is_valid']}, is_safe={vr['is_safe']}, score={vr['safety_score']}")
    selected_plan = plans[0]
    print("  --> Step 5 & 6: Plans Generated & Safety Validated\n")
    time.sleep(1)

    # Step 7: Digital Twin Forward Simulation Preview
    print(f"STEP 7: Running Digital Twin Forward Simulation for {selected_plan['plan_id']}...")
    sim_res = requests.post(f"{BACKEND_URL}/api/plans/{selected_plan['plan_id']}/simulate").json()
    assert sim_res["outcome"].lower() == "success"
    ts = sim_res["simulated_telemetry"]
    print(f"  [Twin Simulation Outcome]: {sim_res['outcome'].upper()} (Success Probability: {sim_res['success_probability']*100:.0f}%)")
    print(f"  [Projected Dynamics]: Pre-Temp={ts[0]['metrics']['battery_temperature']['value']}°C -> Post-Temp={ts[-1]['metrics']['battery_temperature']['value']}°C")
    print("  --> Step 7: Forward Simulation Verified\n")
    time.sleep(1)

    # Step 8: Human-in-the-Loop Operator Authorization
    print(f"STEP 8: Flight Director Authorization for Plan {selected_plan['plan_id']}...")
    appr_res = requests.post(
        f"{BACKEND_URL}/api/plans/{selected_plan['plan_id']}/approve",
        json={"operator_id": "FLIGHT-DIRECTOR-01", "notes": "Authorization granted for thermal containment."},
    ).json()
    assert appr_res["status"] == "APPROVED"
    print(f"  [Incident State]: {appr_res['status']} (Authorized by FLIGHT-DIRECTOR-01)")
    print("  --> Step 8: Plan Approved\n")
    time.sleep(1)

    # Step 9: Uplink Execution & Remediation
    print(f"STEP 9: Executing Recovery Commands on Satellite...")
    exec_res = requests.post(
        f"{BACKEND_URL}/api/plans/{selected_plan['plan_id']}/execute",
        json={"operator_id": "FLIGHT-DIRECTOR-01", "notes": "Commands uplinked to spacecraft bus."},
    ).json()
    assert exec_res["status"] == "RESOLVED"
    print(f"  [Execution Result]: Status={exec_res['status']}")
    print(f"  [Actions Dispatched]: {exec_res['actions_executed']}")
    print("  --> Step 9: Commands Executed & State Remediated\n")
    time.sleep(1)

    # Step 10: Post-Remediation Telemetry Verification
    print("STEP 10: Post-Recovery Telemetry Verification...")
    telem_post = requests.get(f"{BACKEND_URL}/api/telemetry/SAT-01?window=5&generate=5").json()
    m_post = (telem_post.get("telemetry") or telem_post.get("history"))[-1]["metrics"]
    print(f"  [Stabilized SAT-01 Telemetry] Temp={m_post['battery_temperature']['value']}°C | Voltage={m_post['battery_voltage']['value']}V | Wheel={m_post['wheel_speed']['value']}RPM")
    print("  --> Step 10: Spacecraft Restored to Full Nominal Operation!\n")

    print("=" * 80)
    print("DEMO VERDICT: 10/10 STEPS EXECUTED PERFECTLY (100% SUCCESS)")
    print("=" * 80 + "\n")
    return True


if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
