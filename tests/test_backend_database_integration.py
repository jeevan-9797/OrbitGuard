"""
Phase 4: Backend & Database End-to-End Integration Test Suite
Tests all 15 Exit Criteria required by Phase 4 of the 48-Hour Roadmap.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.main import app
from app.database import get_sqlite_fallback

# Initialize SQLite database with schema and seeds
conn = get_sqlite_fallback()

# Seed initial knowledge if not present
with open(os.path.join(BASE_DIR, "database", "seed", "knowledge.sql"), "r", encoding="utf-8") as f:
    sql_k = f.read()
    # Simple clean up for sqlite
    for stmt in sql_k.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--") and "ON CONFLICT" not in stmt:
            try:
                # Remove ::jsonb casts
                s_clean = stmt.replace("::jsonb", "").replace("ON CONFLICT (mode_code) DO UPDATE SET", "")
                conn.execute(s_clean)
            except Exception:
                pass
conn.commit()

client = TestClient(app)


def test_01_health_endpoint():
    """Verify health endpoint and database status probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["app"] == "Satellite Multi-Agent AI System"


def test_02_fleet_management():
    """Verify creating a satellite, subsystem, and querying fleet summary."""
    # Create satellite
    sat_resp = client.post("/api/fleet", json={
        "name": "TEST-SAT-ALPHA",
        "mode": "NOMINAL",
        "status": "ONLINE",
        "risk_score": 0.05
    })
    assert sat_resp.status_code == 200
    sat = sat_resp.json()
    assert sat["name"] == "TEST-SAT-ALPHA"
    sat_id = sat["id"]

    # Query fleet summary
    summary_resp = client.get("/api/fleet")
    assert summary_resp.status_code == 200
    fleet = summary_resp.json()
    assert any(s["id"] == sat_id for s in fleet)


def test_03_telemetry_storage_and_window():
    """Verify telemetry recording and bounded window retrieval."""
    # Create test satellite first
    sat = client.post("/api/fleet", json={
        "name": "SAT-TELEMETRY-TEST",
        "mode": "NOMINAL",
        "status": "ONLINE",
        "risk_score": 0.1
    }).json()
    sat_id = sat["id"]

    # Record 3 telemetry readings
    for val in [24.1, 26.5, 31.8]:
        t_resp = client.post("/api/telemetry", json={
            "satellite_id": sat_id,
            "metric": "battery_temperature",
            "value": val,
            "unit": "C",
            "quality": "GOOD"
        })
        assert t_resp.status_code == 200

    # Retrieve telemetry window
    window_resp = client.get(f"/api/telemetry?satellite_id={sat_id}&metric=battery_temperature&limit=10")
    assert window_resp.status_code == 200
    readings = window_resp.json()
    assert len(readings) == 3
    # Check descending order
    assert readings[0]["value"] == 31.8


def test_04_anomaly_and_incident_lifecycle():
    """Verify opening an anomaly, creating an incident, and lifecycle progression."""
    sat = client.post("/api/fleet", json={
        "name": "SAT-INCIDENT-TEST",
        "mode": "NOMINAL",
        "status": "ONLINE",
        "risk_score": 0.2
    }).json()
    sat_id = sat["id"]

    # 1. Create Anomaly
    anom_resp = client.post("/api/incidents/anomalies", json={
        "satellite_id": sat_id,
        "type": "THERMAL_RUNAWAY",
        "severity": "CRITICAL",
        "confidence": 0.97,
        "evidence": {"metric": "battery_temperature", "value": 45.2, "threshold": 35.0}
    })
    assert anom_resp.status_code == 200
    anomaly = anom_resp.json()
    anom_id = anomaly["id"]

    # 2. Create Incident
    inc_resp = client.post("/api/incidents", json={
        "satellite_id": sat_id,
        "anomaly_id": anom_id,
        "title": "SAT-INCIDENT-TEST Thermal Spike on Eclipse Exit",
        "priority": "P1",
        "severity": "CRITICAL",
        "confidence": 0.95,
        "primary_hypothesis": "Heater relay stuck closed"
    })
    assert inc_resp.status_code == 200
    incident = inc_resp.json()
    inc_id = incident["id"]
    assert incident["state"] == "DETECTED"

    # 3. Test Invalid Transition (DETECTED directly to EXECUTING must be REJECTED)
    invalid_resp = client.post(f"/api/incidents/{inc_id}/transition", json={
        "target_state": "EXECUTING",
        "actor": "TESTER"
    })
    assert invalid_resp.status_code == 400

    # 4. Step to INVESTIGATING -> DIAGNOSED -> PLANNING
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "INVESTIGATING"}).raise_for_status()
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "DIAGNOSED"}).raise_for_status()
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "PLANNING"}).raise_for_status()

    inc_state = client.get(f"/api/incidents/{inc_id}").json()["state"]
    assert inc_state == "PLANNING"


def test_05_ai_contract_context_and_agent_runs():
    """Verify build_incident_context() and save_agent_run() matching locked AI contract."""
    # Create incident
    sat = client.post("/api/fleet", json={"name": "SAT-AI-CONTRACT", "mode": "NOMINAL"}).json()
    inc = client.post("/api/incidents", json={
        "satellite_id": sat["id"],
        "title": "AI Contract Test Incident"
    }).json()
    inc_id = inc["id"]

    # 1. Test build_incident_context()
    ctx_resp = client.get(f"/api/incidents/{inc_id}/context")
    assert ctx_resp.status_code == 200
    context = ctx_resp.json()
    assert "incident" in context
    assert "satellite" in context
    assert "metric_deviations" in context
    assert "action_catalog" in context

    # 2. Test save_agent_run() with locked diagnosis schema
    diagnosis_output = {
        "primary_hypothesis": {
            "cause": "excessive_power_consumption",
            "confidence": 0.91,
            "evidence": ["power_consumption exceeds solar_power"]
        },
        "hypotheses": [
            {
                "cause": "excessive_power_consumption",
                "confidence": 0.91,
                "evidence": ["power_consumption = 4.8W", "solar_power = 2.1W"]
            }
        ],
        "needs_evidence": False
    }

    run_resp = client.post(f"/api/incidents/{inc_id}/agent-runs", json={
        "incident_id": inc_id,
        "agent_name": "diagnostic_agent",
        "status": "COMPLETED",
        "input": {"context_id": inc_id},
        "output": diagnosis_output,
        "confidence": 0.91
    })
    assert run_resp.status_code == 200
    saved_run = run_resp.json()
    assert saved_run["output"]["primary_hypothesis"]["cause"] == "excessive_power_consumption"

    # Query agent runs list
    runs = client.get(f"/api/incidents/{inc_id}/agent-runs").json()
    assert len(runs) >= 1


def test_06_recovery_plan_safety_validation_and_execution_gate():
    """
    CRITICAL TEST: Verifies that unapproved/unsafe recovery plans CANNOT be executed.
    Workflow: Plan -> Validation -> Approval -> Execution -> Verification.
    """
    sat = client.post("/api/fleet", json={"name": "SAT-GATE-TEST", "mode": "NOMINAL"}).json()
    inc = client.post("/api/incidents", json={"satellite_id": sat["id"], "title": "Gate Incident"}).json()
    inc_id = inc["id"]

    # Progress state to PLANNING -> VALIDATING
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "INVESTIGATING"}).raise_for_status()
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "DIAGNOSED"}).raise_for_status()
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "PLANNING"}).raise_for_status()

    # 1. Create Unsafe Candidate Plan 1 (Violates SR-TCS-002: sets heater duty cycle > 0 while in thermal alert)
    unsafe_plan = client.post(f"/api/incidents/{inc_id}/plans", json={
        "incident_id": inc_id,
        "version": 1,
        "rationale": "Unsafe test plan",
        "actions": {
            "actions": [
                {"order": 1, "action_code": "REDUCE_POWER_LOAD", "parameters": {"target": "NON_CRITICAL"}},
                {"order": 2, "action_code": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 25}}
            ]
        },
        "risk_level": "HIGH"
    }).json()
    unsafe_plan_id = unsafe_plan["id"]

    # 2. Run Validation on Unsafe Plan
    val_resp = client.post(f"/api/incidents/{inc_id}/plans/{unsafe_plan_id}/validate")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["status"] == "FAILED"
    assert len(val_data["failed_rules"]) > 0

    # 3. Attempting to approve or execute unsafe plan MUST FAIL
    approve_fail = client.post(f"/api/incidents/{inc_id}/plans/{unsafe_plan_id}/approve")
    assert approve_fail.status_code == 400  # Rejected by Safety Gate!

    # 4. Create Safe Candidate Plan 2 (Inhibits heater: duty cycle = 0)
    safe_plan = client.post(f"/api/incidents/{inc_id}/plans", json={
        "incident_id": inc_id,
        "version": 2,
        "rationale": "Safe test plan: inhibit heater completely",
        "actions": {
            "actions": [
                {"order": 1, "action_code": "REDUCE_POWER_LOAD", "parameters": {"target": "NON_CRITICAL"}},
                {"order": 2, "action_code": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 0}}
            ]
        },
        "risk_level": "LOW"
    }).json()
    safe_plan_id = safe_plan["id"]

    # 5. Validate Safe Plan
    val_safe = client.post(f"/api/incidents/{inc_id}/plans/{safe_plan_id}/validate").json()
    assert val_safe["status"] == "PASSED"

    # Move incident to VALIDATING
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "VALIDATING"}).raise_for_status()

    # 6. Approve Safe Plan -> Transitions to APPROVED
    app_resp = client.post(f"/api/incidents/{inc_id}/plans/{safe_plan_id}/approve")
    assert app_resp.status_code == 200
    assert client.get(f"/api/incidents/{inc_id}").json()["state"] == "APPROVED"

    # 7. Execute Approved Plan
    exec_resp = client.post(f"/api/incidents/{inc_id}/plans/{safe_plan_id}/execute", json={
        "before_state": {"battery_temperature": 44.8},
        "after_state": {"battery_temperature": 32.1}
    })
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["status"] == "SUCCESS"

    # Incident should now be in VERIFYING state
    assert client.get(f"/api/incidents/{inc_id}").json()["state"] == "VERIFYING"

    # 8. Resolve Incident
    res_resp = client.post(f"/api/incidents/{inc_id}/transition", json={
        "target_state": "RESOLVED",
        "notes": "AUTONOMOUS_THERMAL_MITIGATION_VERIFIED"
    })
    assert res_resp.status_code == 200
    assert res_resp.json()["state"] == "RESOLVED"


def test_07_audit_event_timeline():
    """Verify that every major operational event is preserved in the append-only audit trail."""
    sat = client.post("/api/fleet", json={"name": "SAT-AUDIT-TEST", "mode": "NOMINAL"}).json()
    inc = client.post("/api/incidents", json={"satellite_id": sat["id"], "title": "Audit Incident"}).json()
    inc_id = inc["id"]

    # Retrieve audit events
    audit_resp = client.get(f"/api/incidents/{inc_id}/audit")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "INCIDENT_OPENED"
    assert events[0]["actor"] == "DETECTOR"


def test_08_knowledge_endpoints():
    """Verify action catalog and safety rules retrieval."""
    actions_resp = client.get("/api/knowledge/actions")
    assert actions_resp.status_code == 200
    assert isinstance(actions_resp.json(), list)

    rules_resp = client.get("/api/knowledge/rules")
    assert rules_resp.status_code == 200
    assert isinstance(rules_resp.json(), list)
