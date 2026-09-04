"""
Frontend Contract & Dashboard Performance Test Suite
Steps 12 & 13: Verifies that API provides all UI payload fields and responds in < 50ms.
"""

import os
import sys
import time
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.main import app
from database.reset import reset_demo_state
from app.demo_runner import run_scenario_a

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def populate_demo_incident():
    """Run Scenario A to populate realistic incident data for contract checks."""
    run_scenario_a(verbose=False)


def test_frontend_contract_fleet_cards():
    """Verify fleet cards deliver name, mode, status, risk, active_incident_count."""
    t0 = time.time()
    resp = client.get("/api/fleet")
    latency_ms = (time.time() - t0) * 1000
    assert resp.status_code == 200
    assert latency_ms < 50.0  # Performance target < 50ms

    fleet = resp.json()
    assert len(fleet) >= 6
    sat = fleet[0]
    for field in ("id", "name", "mode", "status", "risk_score", "active_incident_count"):
        assert field in sat, f"Missing required field {field} in fleet card"


def test_frontend_contract_telemetry_window():
    """Verify telemetry window delivers timestamp, metric, value, unit, quality."""
    t0 = time.time()
    resp = client.get("/api/telemetry?satellite_id=a0000000-0000-0000-0000-000000000001&limit=50")
    latency_ms = (time.time() - t0) * 1000
    assert resp.status_code == 200
    assert latency_ms < 50.0

    points = resp.json()
    assert len(points) > 0
    p = points[0]
    for field in ("satellite_id", "metric", "value", "unit", "quality", "timestamp"):
        assert field in p, f"Missing required field {field} in telemetry point"


def test_frontend_contract_incident_and_timeline():
    """Verify incident details and agent timeline contracts."""
    # Find the incident from Scenario A
    from app.repositories.fleet_repo import FleetRepository
    from app.database import get_db
    with get_db() as cur:
        cur.execute("SELECT id FROM incidents ORDER BY opened_at DESC LIMIT 1;")
        inc = cur.fetchone()
    inc_id = inc["id"]

    # 1. Incident Details
    t0 = time.time()
    inc_resp = client.get(f"/api/incidents/{inc_id}")
    assert inc_resp.status_code == 200
    assert (time.time() - t0) * 1000 < 50.0
    inc_data = inc_resp.json()
    for field in ("id", "satellite_id", "state", "title", "priority", "severity", "opened_at"):
        assert field in inc_data

    # 2. Agent Timeline
    t0 = time.time()
    runs_resp = client.get(f"/api/incidents/{inc_id}/agent-runs")
    assert runs_resp.status_code == 200
    assert (time.time() - t0) * 1000 < 50.0
    runs = runs_resp.json()
    assert len(runs) > 0
    r = runs[0]
    for field in ("agent_name", "status", "input", "output", "confidence", "started_at"):
        assert field in r

    # 3. Diagnosis Details
    diag_resp = client.get(f"/api/incidents/{inc_id}/diagnosis")
    assert diag_resp.status_code == 200
    diag = diag_resp.json()
    assert "output" in diag
    assert "primary_hypothesis" in diag["output"]

    # 4. Recovery Plans
    plans_resp = client.get(f"/api/incidents/{inc_id}/plans")
    assert plans_resp.status_code == 200
    plans = plans_resp.json()
    assert len(plans) >= 2
    pl = plans[0]
    for field in ("version", "rationale", "actions", "risk_level"):
        assert field in pl

    # 5. Audit Trail
    t0 = time.time()
    audit_resp = client.get(f"/api/incidents/{inc_id}/audit")
    assert audit_resp.status_code == 200
    assert (time.time() - t0) * 1000 < 50.0
    events = audit_resp.json()
    assert len(events) >= 10
    ev = events[0]
    for field in ("incident_id", "event_type", "actor", "payload", "timestamp"):
        assert field in ev
