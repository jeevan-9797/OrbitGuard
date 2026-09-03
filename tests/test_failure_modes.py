"""
Negative & Failure Modes Integration Test Suite
Step 10: Validates robust rejection and clean error handling for all invalid operational states.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.main import app
from app.services.incident_service import IncidentService, InvalidStateTransitionError, SafetyGateError
from app.repositories.recovery_repo import RecoveryRepository
from database.reset import reset_demo_state

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_clean_db():
    reset_demo_state()


def test_invalid_satellite_id():
    """Querying a non-existent satellite UUID returns 404."""
    resp = client.get("/api/fleet/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Satellite not found"


def test_invalid_foreign_key_telemetry():
    """Attempting to log telemetry for a non-existent satellite triggers foreign key violation."""
    resp = client.post("/api/telemetry", json={
        "satellite_id": "00000000-0000-0000-0000-000000000000",
        "metric": "temperature",
        "value": 20.0,
        "unit": "C"
    })
    # Either database constraint error handled or HTTP error
    assert resp.status_code in (400, 422, 500)


def test_missing_required_telemetry_fields():
    """Omitting required fields (e.g. value, metric) is caught by Pydantic validation."""
    resp = client.post("/api/telemetry", json={
        "satellite_id": "a0000000-0000-0000-0000-000000000001"
        # missing metric, value, unit
    })
    assert resp.status_code == 422  # Unprocessable Entity


def test_invalid_incident_transition_rejection():
    """State machine strictly prevents illegal transitions (e.g. DETECTED directly to EXECUTING or RESOLVED)."""
    # 1. Create Incident
    inc = client.post("/api/incidents", json={
        "satellite_id": "a0000000-0000-0000-0000-000000000001",
        "title": "Illegal Transition Test"
    }).json()
    inc_id = inc["id"]

    # 2. Try DETECTED -> EXECUTING (Illegal bypass)
    resp = client.post(f"/api/incidents/{inc_id}/transition", json={
        "target_state": "EXECUTING"
    })
    assert resp.status_code == 400
    assert "Invalid transition" in resp.json()["detail"]

    # 3. Try DETECTED -> RESOLVED (Illegal bypass)
    resp2 = client.post(f"/api/incidents/{inc_id}/transition", json={
        "target_state": "RESOLVED"
    })
    assert resp2.status_code == 400
    assert "Invalid transition" in resp2.json()["detail"]


def test_unvalidated_recovery_plan_execution_rejection():
    """An unvalidated candidate plan CANNOT be approved or executed."""
    inc = client.post("/api/incidents", json={
        "satellite_id": "a0000000-0000-0000-0000-000000000001",
        "title": "Unvalidated Execution Test"
    }).json()
    inc_id = inc["id"]

    # Move to PLANNING
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "INVESTIGATING"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "DIAGNOSED"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "PLANNING"})

    # Create unvalidated plan
    plan = client.post(f"/api/incidents/{inc_id}/plans", json={
        "incident_id": inc_id,
        "version": 1,
        "rationale": "Unvalidated plan",
        "actions": {"actions": [{"order": 1, "action_code": "REDUCE_POWER_LOAD"}]}
    }).json()
    plan_id = plan["id"]

    # Attempt to approve without validation
    app_resp = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/approve")
    assert app_resp.status_code == 400
    assert "Safety validation not passed" in app_resp.json()["detail"]

    # Attempt to execute directly without approval
    exec_resp = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/execute", json={
        "before_state": {},
        "after_state": {}
    })
    assert exec_resp.status_code == 400
    assert "expected APPROVED" in exec_resp.json()["detail"]


def test_rejected_plan_execution_rejection():
    """A failed/rejected plan cannot be approved or executed."""
    inc = client.post("/api/incidents", json={
        "satellite_id": "a0000000-0000-0000-0000-000000000001",
        "title": "Rejected Plan Test"
    }).json()
    inc_id = inc["id"]

    # Advance state
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "INVESTIGATING"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "DIAGNOSED"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "PLANNING"})

    # Create plan with heater duty > 0 (violates SR-TCS-002)
    plan = client.post(f"/api/incidents/{inc_id}/plans", json={
        "incident_id": inc_id,
        "version": 1,
        "rationale": "Thermal violation plan",
        "actions": {"actions": [{"order": 1, "action_code": "PWR_HEATER_DUTY_CYCLE_SET", "parameters": {"duty_cycle": 50}}]}
    }).json()
    plan_id = plan["id"]

    # Validate -> FAILED
    val_resp = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/validate")
    assert val_resp.json()["status"] == "FAILED"

    # Attempt approve -> Rejected
    app_resp = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/approve")
    assert app_resp.status_code == 400


def test_duplicate_command_execution_prevention():
    """Idempotency check: executing the same plan twice must be blocked."""
    inc = client.post("/api/incidents", json={
        "satellite_id": "a0000000-0000-0000-0000-000000000001",
        "title": "Duplicate Execution Test"
    }).json()
    inc_id = inc["id"]

    # Advance state to APPROVED with safe plan
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "INVESTIGATING"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "DIAGNOSED"})
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "PLANNING"})

    plan = client.post(f"/api/incidents/{inc_id}/plans", json={
        "incident_id": inc_id,
        "version": 1,
        "rationale": "Safe idempotent plan",
        "actions": {"actions": [{"order": 1, "action_code": "REDUCE_POWER_LOAD"}]}
    }).json()
    plan_id = plan["id"]

    # Validate and approve
    client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/validate")
    client.post(f"/api/incidents/{inc_id}/transition", json={"target_state": "VALIDATING"})
    client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/approve")

    # First execution succeeds
    exec1 = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/execute", json={
        "before_state": {},
        "after_state": {}
    })
    assert exec1.status_code == 200

    # Second execution must fail (Idempotency safety gate)
    exec2 = client.post(f"/api/incidents/{inc_id}/plans/{plan_id}/execute", json={
        "before_state": {},
        "after_state": {}
    })
    assert exec2.status_code == 400
