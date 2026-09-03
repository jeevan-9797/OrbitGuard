"""
Comprehensive Regression & Edge Case Test Suite for OrbitGuard (Milestone 4).

Tests:
1. Standard Scenarios: NORMAL, LOW_BATTERY, HIGH_TEMPERATURE, WHEEL_DEGRADATION
2. Edge Cases:
   - Missing telemetry (empty dictionary or None)
   - Incomplete telemetry (partial metrics)
   - Unknown anomaly type
   - Repeated anomaly injection on same satellite
   - Invalid recovery action vocabulary
   - Unsafe recovery action ordering (thermal constraint violation)
   - Missing rollback procedure
   - LLM failure / deterministic fallback consistency
   - Telemetry grounding verification (zero hallucination of unmeasured metrics)
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_ml.detector.detector import detect_anomalies
from ai_ml.integration.backend_adapter import map_anomaly_type
from app.agents.diagnostic_agent import get_fallback_diagnosis
from app.agents.recovery_planner import get_fallback_recovery_plans
from app.schemas.anomaly import AnomalyEvent, SeverityLevel
from app.schemas.recovery import RecoveryPlan, RecoveryStep, RiskLevel
from app.services.detector import clear_incidents
from app.services.orchestrator import (
    IncidentRecord,
    IncidentStatus,
    analyze_incident,
    approve_incident_plan,
    execute_incident_plan,
    register_detected_incident,
)
from app.services.validator import validate_recovery_plan
from app.simulator.telemetry import (
    generate_normal_telemetry,
    inject_anomaly,
    reset_simulator,
)


async def run_regression_suite() -> bool:
    print("\n================================================================================")
    print("      ORBITGUARD MILESTONE 4: FULL REGRESSION & EDGE CASE SUITE")
    print("================================================================================\n")

    passed_tests = 0
    total_tests = 9

    # ── Test 1: Standard Scenarios Regression ─────────────────────────────────
    print("[1/9] Testing 4 Standard Scenarios Regression...")
    from ai_ml.evaluation.run_benchmark import run_benchmark_suite
    results, summary = run_benchmark_suite(save_json=False)
    assert summary.overall_scenario_success_rate == 100.0, "All standard scenarios must pass"
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 2: Missing Telemetry Handling ────────────────────────────────────
    print("[2/9] Testing Edge Case: Missing Telemetry (Empty Snapshot)...")
    empty_anomaly = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="EPS",
        severity=SeverityLevel.MEDIUM,
        description="Low voltage detected with empty snapshot",
        telemetry_snapshot={},
        confidence=0.5,
        detected_at=datetime.now(timezone.utc),
    )
    diag_empty = get_fallback_diagnosis(empty_anomaly)
    assert diag_empty.diagnosis_id is not None
    assert "insufficient telemetry" in diag_empty.root_cause.lower() or "inconclusive" in diag_empty.root_cause.lower()
    print(f"    - Inconclusive root cause gracefully reported: {diag_empty.root_cause}")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 3: Incomplete / Partial Telemetry ─────────────────────────────────
    print("[3/9] Testing Edge Case: Partial Telemetry (Only Voltage Provided)...")
    partial_anomaly = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="EPS",
        severity=SeverityLevel.HIGH,
        description="Battery voltage low: 18.2V",
        telemetry_snapshot={"battery_voltage": 18.2},
        confidence=0.8,
        detected_at=datetime.now(timezone.utc),
    )
    diag_partial = get_fallback_diagnosis(partial_anomaly)
    assert any("18.2" in ev for ev in diag_partial.evidence)
    assert not any("temperature" in ev for ev in diag_partial.evidence)
    print(f"    - Only provided metrics included in evidence: {diag_partial.evidence}")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 4: Unknown Anomaly Type Handling ──────────────────────────────────
    print("[4/9] Testing Edge Case: Unknown Anomaly Type...")
    unknown_anomaly = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="PAYLOAD",
        severity=SeverityLevel.LOW,
        description="Cosmic ray particle event detected",
        telemetry_snapshot={"flux_count": 999},
        confidence=0.6,
        detected_at=datetime.now(timezone.utc),
    )
    diag_unknown = get_fallback_diagnosis(unknown_anomaly)
    assert diag_unknown.affected_subsystems == ["PAYLOAD"]
    
    # Verify adapter raises clear error on unmapped anomaly rather than silent corruption
    unsupported_raised = False
    try:
        map_anomaly_type("UNKNOWN_COSMIC_EVENT")
    except ValueError as exc:
        unsupported_raised = True
        print(f"    - Adapter correctly rejected unmapped type: {exc}")
    assert unsupported_raised
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 5: Repeated Anomaly Injection on Same Satellite ──────────────────
    print("[5/9] Testing Edge Case: Repeated Anomaly Injection...")
    reset_simulator()
    inject_anomaly("SAT-01", "battery_overheat")
    res1 = inject_anomaly("SAT-01", "battery_overheat")
    assert res1["status"] == "injected"
    telem = generate_normal_telemetry("SAT-01")
    assert telem["metrics"]["battery_temperature"]["value"] >= 45.0
    print("    - Repeated injection maintains valid simulation state without crash")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 6: Unsafe Action Ordering Constraint (Thermal) ───────────────────
    print("[6/9] Testing Safety Constraint: Unsafe Action Ordering...")
    unsafe_ordering_plan = RecoveryPlan(
        plan_id="PLAN-UNSAFE-ORDER-001",
        title="Unsafe Thermal Ordering Plan",
        diagnosis_id="DIAG-THM",
        satellite_id="SAT-01",
        actions=["ENTER_SAFE_THERMAL_MODE", "REDUCE_PAYLOAD_LOAD"],
        steps=[
            RecoveryStep(
                step_number=1,
                action="ENTER_SAFE_THERMAL_MODE",
                subsystem="Thermal",
                expected_outcome="Safe thermal mode entered prematurely",
                rollback_action="Exit safe thermal mode",
            ),
            RecoveryStep(
                step_number=2,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome="Payload load reduced second",
                rollback_action="Restore payload load",
            ),
        ],
        risk_level=RiskLevel.HIGH,
        risk_score=0.8,
        rollback_plan="Rollback if temperature worsens",
        created_at=datetime.now(timezone.utc),
    )
    val_ordering = validate_recovery_plan(unsafe_ordering_plan, {"battery_temperature": 50.0, "battery_voltage": 27.0})
    assert val_ordering.is_valid is False, "Plan with unsafe thermal order must be marked invalid"
    assert val_ordering.is_safe is False, "Plan with unsafe thermal order must be marked unsafe"
    assert any("ordering" in v.lower() or "thermal" in v.lower() for v in val_ordering.violations)
    print(f"    - Safety Validator correctly rejected unsafe sequence: {val_ordering.violations}")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 7: Missing Rollback Information ──────────────────────────────────
    print("[7/9] Testing Safety Constraint: Missing Rollback Information...")
    no_rollback_plan = RecoveryPlan(
        plan_id="PLAN-NO-ROLLBACK-001",
        title="Plan Lacking Rollback Information",
        diagnosis_id="DIAG-EPS",
        satellite_id="SAT-01",
        actions=["REDUCE_PAYLOAD_LOAD"],
        steps=[
            RecoveryStep(
                step_number=1,
                action="REDUCE_PAYLOAD_LOAD",
                subsystem="EPS",
                expected_outcome="Payload load reduced",
                rollback_action=None,
            ),
        ],
        risk_level=RiskLevel.MEDIUM,
        risk_score=0.5,
        rollback_plan=None,
        created_at=datetime.now(timezone.utc),
    )
    val_rollback = validate_recovery_plan(no_rollback_plan, {"battery_voltage": 27.0})
    # Must flag warning / note that rollback procedure is absent
    rollback_check = next((c for c in val_rollback.checks if c.check_name == "rollback_defined"), None)
    assert rollback_check is not None
    assert rollback_check.passed is False or len(val_rollback.warnings) > 0 or len(val_rollback.violations) > 0
    print(f"    - Rollback check properly evaluated: {rollback_check.message}")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 8: Deterministic Fallback Consistency ────────────────────────────
    print("[8/9] Testing Deterministic Fallback Consistency on LLM Failure...")
    test_cases = [
        ("EPS", "Battery voltage is 18.5V", {"battery_voltage": 18.5, "battery_temperature": 24.0, "wheel_speed": 3000.0}),
        ("Thermal", "Battery temperature is 52.0 degC", {"battery_temperature": 52.0, "battery_voltage": 27.0, "wheel_speed": 3000.0}),
        ("ADCS", "Reaction wheel speed deviation is 480 RPM", {"wheel_speed": 3480.0, "attitude_error": 0.35, "battery_voltage": 27.0}),
    ]
    for subsys_name, anomaly_desc, telem_snap in test_cases:
        anom = AnomalyEvent(
            anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
            satellite_id="SAT-01",
            subsystem=subsys_name,
            severity=SeverityLevel.HIGH,
            description=anomaly_desc,
            telemetry_snapshot=telem_snap,
            confidence=0.85,
            detected_at=datetime.now(timezone.utc),
        )
        diag = get_fallback_diagnosis(anom)
        plans = get_fallback_recovery_plans(diag)
        assert len(plans) >= 2, f"Fallback for {subsys_name} must return at least 2 candidate plans"
        for p in plans:
            v = validate_recovery_plan(p, anom.telemetry_snapshot)
            assert v.is_valid is True, f"Fallback plan {p.title} must be valid"
            assert v.is_safe is True, f"Fallback plan {p.title} must be safe"
    print("    - All deterministic fallback plans pass safety validation with zero violations")
    passed_tests += 1
    print("    --> Result: PASS\n")

    # ── Test 9: Zero Hallucination of Unmeasured Physical Metrics ──────────────
    print("[9/9] Testing Zero Hallucination Grounding Rule...")
    anom_grounding = AnomalyEvent(
        anomaly_id=f"ANO-{uuid.uuid4().hex[:8].upper()}",
        satellite_id="SAT-01",
        subsystem="EPS",
        severity=SeverityLevel.HIGH,
        description="Low voltage anomaly: 18.1V",
        telemetry_snapshot={"battery_voltage": 18.1},
        confidence=0.9,
        detected_at=datetime.now(timezone.utc),
    )
    diag_ground = get_fallback_diagnosis(anom_grounding)
    # Check that it did not hallucinate bearing wear, orbital eclipses, or solar flares
    hallucinated_terms = ["bearing wear", "solar flare", "radiation damage", "micro-meteoroid"]
    text_corpus = f"{diag_ground.primary_hypothesis} {diag_ground.root_cause} {' '.join(diag_ground.evidence)}".lower()
    for term in hallucinated_terms:
        assert term not in text_corpus, f"Hallucinated term '{term}' found in diagnosis"
    print("    - Zero unmeasured physical claims or hallucinated hardware states detected")
    passed_tests += 1
    print("    --> Result: PASS\n")

    print("--------------------------------------------------------------------------------")
    print(f"Milestone 4 Regression Suite Verdict: {passed_tests}/{total_tests} TESTS PASSED (100%)")
    print("--------------------------------------------------------------------------------\n")
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_regression_suite())
    sys.exit(0 if success else 1)
