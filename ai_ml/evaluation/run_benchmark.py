"""
OrbitGuard Scenario-Based Evaluation & Benchmarking Harness.

Runs all major supported spacecraft telemetry scenarios against the AIML
anomaly detection, backend incident orchestration, diagnostic agent,
recovery planner, and deterministic safety validation pipeline.

Computes quantitative metrics including detection accuracy, false-positive
rate, diagnosis success, recovery generation success, and safety compliance.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_ml.detector.detector import detect_anomalies
from ai_ml.integration.backend_adapter import (
    analyze_incident,
    check_backend,
    find_latest_incident,
    generate_telemetry,
    get_incidents,
    inject_anomaly,
    load_telemetry,
    map_anomaly_type,
    reset_backend,
)


# ============================================================
# BENCHMARK SCENARIO DEFINITIONS
# ============================================================

BENCHMARK_SCENARIOS = [
    {
        "name": "NORMAL",
        "file": "telemetry_sample.json",
        "expected_anomaly": None,
        "expected_subsystem": None,
        "is_anomalous": False,
        "description": "Nominal spacecraft bus telemetry with all parameters within limits",
    },
    {
        "name": "LOW_BATTERY",
        "file": "low_battery.json",
        "expected_anomaly": "LOW_BATTERY",
        "expected_subsystem": "EPS",
        "is_anomalous": True,
        "description": "Battery bus voltage excursion below configured detection threshold (< 20V)",
    },
    {
        "name": "HIGH_TEMPERATURE",
        "file": "high_temperature.json",
        "expected_anomaly": "HIGH_TEMPERATURE",
        "expected_subsystem": "EPS",
        "is_anomalous": True,
        "description": "Battery thermal runaway / overheating condition (> 80°C / 45°C backend)",
    },
    {
        "name": "WHEEL_DEGRADATION",
        "file": "wheel_degradation.json",
        "expected_anomaly": "REACTION_WHEEL_OVERLOAD",
        "expected_subsystem": "ADCS",
        "is_anomalous": True,
        "description": "Reaction wheel momentum/jitter degradation and attitude control excursion",
    },
]


# ============================================================
# METRICS DATA STRUCTURES
# ============================================================

@dataclass
class ScenarioMetrics:
    scenario: str
    file_name: str
    is_anomalous: bool
    expected_anomaly: str | None
    detected_anomaly: str | None
    detection_correct: bool
    severity: str | None
    confidence: float | None
    incident_created: bool | None
    incident_id: str | None
    diagnosis_success: bool | None
    diagnosis_hypothesis: str | None
    recovery_success: bool | None
    recovery_plan_count: int
    safety_success: bool | None
    all_plans_safe: bool | None
    scenario_verdict: str  # PASS / FAIL
    details: list[str] = field(default_factory=list)


@dataclass
class BenchmarkSummary:
    total_scenarios: int
    anomalous_scenarios: int
    nominal_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    detection_accuracy: float
    false_positives: int
    false_positive_rate: float
    diagnosis_success_rate: float
    recovery_success_rate: float
    safety_validation_success_rate: float
    overall_scenario_success_rate: float
    executed_at: str
    mode: str


# ============================================================
# EVALUATION LOGIC PER SCENARIO
# ============================================================

def evaluate_scenario(scenario_def: dict[str, Any]) -> ScenarioMetrics:
    name = scenario_def["name"]
    file_name = scenario_def["file"]
    expected_anomaly = scenario_def["expected_anomaly"]
    is_anomalous = scenario_def["is_anomalous"]

    details: list[str] = []

    # --------------------------------------------------------
    # 1. Load telemetry & run AIML detector
    # --------------------------------------------------------
    telemetry_data = load_telemetry(file_name)
    anomalies = detect_anomalies(telemetry_data)

    detected_anomaly = anomalies[0]["type"] if anomalies else None
    severity = anomalies[0]["severity"] if anomalies else "NONE"
    confidence = float(anomalies[0].get("confidence", 1.0)) if anomalies else 1.0

    if is_anomalous:
        detection_correct = (detected_anomaly == expected_anomaly)
    else:
        detection_correct = (detected_anomaly is None)

    if detection_correct:
        details.append(f"AIML Detection: PASS (Detected: {detected_anomaly})")
    else:
        details.append(
            f"AIML Detection: FAIL (Expected: {expected_anomaly}, Got: {detected_anomaly})"
        )

    # --------------------------------------------------------
    # Handle Nominal (Non-anomalous) Scenario
    # --------------------------------------------------------
    if not is_anomalous:
        # Verify backend simulator does not produce spurious anomalies
        reset_backend()
        telemetry_result = generate_telemetry()
        backend_detected = len(telemetry_result.get("anomalies_detected", []))
        incidents = get_incidents()
        backend_clean = (backend_detected == 0 and len(incidents) == 0)

        if backend_clean:
            details.append("Backend Nominal Check: PASS (0 spurious anomalies, 0 incidents)")
        else:
            details.append(
                f"Backend Nominal Check: FAIL ({backend_detected} anomalies, {len(incidents)} incidents)"
            )

        verdict = "PASS" if (detection_correct and backend_clean) else "FAIL"

        return ScenarioMetrics(
            scenario=name,
            file_name=file_name,
            is_anomalous=False,
            expected_anomaly=None,
            detected_anomaly=detected_anomaly,
            detection_correct=detection_correct and backend_clean,
            severity="NONE",
            confidence=1.0,
            incident_created=None,
            incident_id=None,
            diagnosis_success=None,
            diagnosis_hypothesis=None,
            recovery_success=None,
            recovery_plan_count=0,
            safety_success=None,
            all_plans_safe=None,
            scenario_verdict=verdict,
            details=details,
        )

    # --------------------------------------------------------
    # 2. Reset backend and inject anomaly
    # --------------------------------------------------------
    reset_backend()
    aiml_type = detected_anomaly or expected_anomaly
    inject_anomaly(aiml_type)
    generate_telemetry()

    # --------------------------------------------------------
    # 3. Retrieve backend incident
    # --------------------------------------------------------
    incidents = get_incidents()
    incident = find_latest_incident(incidents)

    if incident is None:
        details.append("Backend Incident Creation: FAIL (No incident created)")
        return ScenarioMetrics(
            scenario=name,
            file_name=file_name,
            is_anomalous=True,
            expected_anomaly=expected_anomaly,
            detected_anomaly=detected_anomaly,
            detection_correct=detection_correct,
            severity=severity,
            confidence=confidence,
            incident_created=False,
            incident_id=None,
            diagnosis_success=False,
            diagnosis_hypothesis=None,
            recovery_success=False,
            recovery_plan_count=0,
            safety_success=False,
            all_plans_safe=False,
            scenario_verdict="FAIL",
            details=details,
        )

    incident_id = incident["incident_id"]
    details.append(f"Backend Incident: PASS (ID: {incident_id})")

    # --------------------------------------------------------
    # 4. Analyze incident (Diagnostic Agent + Recovery + Safety)
    # --------------------------------------------------------
    analysis = analyze_incident(incident_id)

    # Evaluate Diagnosis
    diag = analysis.get("diagnosis")
    diagnosis_success = False
    diagnosis_hypothesis = None

    if diag:
        primary_hypo = diag.get("primary_hypothesis", "")
        diagnosis_hypothesis = primary_hypo
        evidence = diag.get("evidence", [])
        affected = diag.get("affected_subsystems", [])

        if name == "LOW_BATTERY":
            # Must ground on voltage/power, not misclassify as thermal
            is_not_thermal = "thermal" not in primary_hypo.lower()
            has_voltage_evidence = any("voltage" in ev.lower() for ev in evidence)
            diagnosis_success = is_not_thermal and has_voltage_evidence
        elif name == "HIGH_TEMPERATURE":
            # Must ground on thermal/temperature
            has_thermal_hypo = "thermal" in primary_hypo.lower() or "temperature" in primary_hypo.lower()
            has_temp_evidence = any("temperature" in ev.lower() for ev in evidence)
            diagnosis_success = has_thermal_hypo and has_temp_evidence
        elif name == "WHEEL_DEGRADATION":
            # Must ground on ADCS / wheel
            has_adcs = "adcs" in [s.lower() for s in affected] or "wheel" in primary_hypo.lower() or "adcs" in primary_hypo.lower()
            has_wheel_evidence = any("wheel" in ev.lower() or "attitude" in ev.lower() for ev in evidence)
            diagnosis_success = has_adcs and has_wheel_evidence
        else:
            diagnosis_success = bool(primary_hypo)

    details.append(
        f"Diagnostic Agent: {'PASS' if diagnosis_success else 'FAIL'} "
        f"({(diagnosis_hypothesis or 'No hypothesis')[:60]}...)"
    )

    # Evaluate Recovery Planner
    plans = analysis.get("recovery_plans", [])
    recovery_plan_count = len(plans)
    recovery_success = recovery_plan_count >= 2
    details.append(
        f"Recovery Planner: {'PASS' if recovery_success else 'FAIL'} "
        f"({recovery_plan_count} candidate plans generated)"
    )

    # Evaluate Safety Validator
    safety_success = False
    all_plans_safe = False

    if plans:
        valid_flags = []
        safe_flags = []
        rollback_flags = []

        for p in plans:
            vr = p.get("validation_result", {})
            valid_flags.append(vr.get("is_valid", False))
            safe_flags.append(vr.get("is_safe", False))

            # Check rollback check explicitly
            for chk in vr.get("checks", []):
                if chk.get("check_name") == "rollback_defined":
                    rollback_flags.append(chk.get("passed", False))

        all_valid = all(valid_flags) and len(valid_flags) > 0
        all_safe = all(safe_flags) and len(safe_flags) > 0
        all_rollback = all(rollback_flags) and len(rollback_flags) > 0

        safety_success = all_valid and all_safe and all_rollback
        all_plans_safe = all_safe

    details.append(
        f"Safety Validator: {'PASS' if safety_success else 'FAIL'} "
        f"(all_valid={all_valid}, all_safe={all_safe})"
    )

    # Overall Scenario Verdict
    overall_pass = (
        detection_correct
        and bool(incident_id)
        and diagnosis_success
        and recovery_success
        and safety_success
    )

    return ScenarioMetrics(
        scenario=name,
        file_name=file_name,
        is_anomalous=True,
        expected_anomaly=expected_anomaly,
        detected_anomaly=detected_anomaly,
        detection_correct=detection_correct,
        severity=severity,
        confidence=confidence,
        incident_created=True,
        incident_id=incident_id,
        diagnosis_success=diagnosis_success,
        diagnosis_hypothesis=diagnosis_hypothesis,
        recovery_success=recovery_success,
        recovery_plan_count=recovery_plan_count,
        safety_success=safety_success,
        all_plans_safe=all_plans_safe,
        scenario_verdict="PASS" if overall_pass else "FAIL",
        details=details,
    )


# ============================================================
# BENCHMARK SUITE RUNNER
# ============================================================

def run_benchmark_suite(save_json: bool = True) -> tuple[list[ScenarioMetrics], BenchmarkSummary]:
    print("\n================================================================================")
    print("           ORBITGUARD SCENARIO-BASED BENCHMARK EVALUATION")
    print("   [Grounding Rule: AI recommends; deterministic code decides]")
    print("   [Note: Scenario-based benchmark results, not real-world statistical accuracy]")
    print("================================================================================\n")

    # Verify backend connectivity
    try:
        health = check_backend()
        print(f"Backend Server: CONNECTED ({health.get('status', 'ok')})")
    except Exception as exc:
        print(f"ERROR: Cannot connect to backend server: {exc}")
        print("Please ensure the OrbitGuard backend is running on http://127.0.0.1:8001")
        sys.exit(1)

    results: list[ScenarioMetrics] = []

    for index, sc_def in enumerate(BENCHMARK_SCENARIOS, start=1):
        print(f"\n[{index}/{len(BENCHMARK_SCENARIOS)}] Running Scenario: {sc_def['name']} ({sc_def['file']})...")
        time.sleep(0.5)

        res = evaluate_scenario(sc_def)
        results.append(res)

        for detail in res.details:
            print(f"    - {detail}")
        print(f"    --> Verdict: {res.scenario_verdict}")

    # Compute Summary Statistics
    total = len(results)
    anomalous = [r for r in results if r.is_anomalous]
    nominal = [r for r in results if not r.is_anomalous]

    det_correct_count = sum(1 for r in results if r.detection_correct)
    detection_accuracy = (det_correct_count / total) * 100.0

    false_positives = sum(
        1 for r in nominal if (r.detected_anomaly is not None or r.incident_created is True)
    )
    false_positive_rate = (false_positives / len(nominal)) * 100.0 if nominal else 0.0

    diag_success_count = sum(1 for r in anomalous if r.diagnosis_success)
    diag_success_rate = (diag_success_count / len(anomalous)) * 100.0 if anomalous else 100.0

    rec_success_count = sum(1 for r in anomalous if r.recovery_success)
    rec_success_rate = (rec_success_count / len(anomalous)) * 100.0 if anomalous else 100.0

    safe_success_count = sum(1 for r in anomalous if r.safety_success)
    safe_success_rate = (safe_success_count / len(anomalous)) * 100.0 if anomalous else 100.0

    passed_count = sum(1 for r in results if r.scenario_verdict == "PASS")
    overall_success_rate = (passed_count / total) * 100.0

    summary = BenchmarkSummary(
        total_scenarios=total,
        anomalous_scenarios=len(anomalous),
        nominal_scenarios=len(nominal),
        passed_scenarios=passed_count,
        failed_scenarios=total - passed_count,
        detection_accuracy=round(detection_accuracy, 1),
        false_positives=false_positives,
        false_positive_rate=round(false_positive_rate, 1),
        diagnosis_success_rate=round(diag_success_rate, 1),
        recovery_success_rate=round(rec_success_rate, 1),
        safety_validation_success_rate=round(safe_success_rate, 1),
        overall_scenario_success_rate=round(overall_success_rate, 1),
        executed_at=datetime.now(timezone.utc).isoformat(),
        mode="HTTP_LIVE_BACKEND",
    )

    # --------------------------------------------------------
    # Display Formatted Benchmark Summary Table
    # --------------------------------------------------------
    print("\n")
    print("ORBITGUARD BENCHMARK")
    print("================================")
    print("")
    print(f"{'Scenario':<22} {'Detection':<11} {'Diagnosis':<11} {'Recovery':<10} {'Safety':<10}")

    for r in results:
        det_str = "PASS" if r.detection_correct else "FAIL"
        if not r.is_anomalous:
            diag_str = "N/A"
            rec_str = "N/A"
            safe_str = "N/A"
        else:
            diag_str = "PASS" if r.diagnosis_success else "FAIL"
            rec_str = "PASS" if r.recovery_success else "FAIL"
            safe_str = "PASS" if r.safety_success else "FAIL"

        print(f"{r.scenario:<22} {det_str:<11} {diag_str:<11} {rec_str:<10} {safe_str:<10}")

    print("\nSummary")
    print("--------------------------------")
    print(f"Detection accuracy: {summary.detection_accuracy}%")
    print(f"False positives: {summary.false_positives} ({summary.false_positive_rate}%)")
    print(f"Diagnosis success: {summary.diagnosis_success_rate}%")
    print(f"Recovery success: {summary.recovery_success_rate}%")
    print(f"Safety validation success: {summary.safety_validation_success_rate}%")
    print(f"Overall scenario success: {summary.overall_scenario_success_rate}%")
    print("--------------------------------\n")

    # Save JSON Report
    if save_json:
        report_data = {
            "title": "OrbitGuard Scenario Benchmark Results",
            "evaluation_type": "scenario_based_simulation",
            "notice": "Deterministic scenario-based benchmark results, not statistical real-world model accuracy.",
            "summary": asdict(summary),
            "scenarios": [asdict(r) for r in results],
        }

        output_path = Path("data/benchmark_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        print(f"Benchmark artifact written to: {output_path.resolve()}\n")

    return results, summary


# ============================================================
# COMMAND LINE ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_benchmark_suite(save_json=True)
