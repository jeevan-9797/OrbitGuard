"""
Test suite for OrbitGuard Runbook & Historical Knowledge Retrieval Engine.

Tests retrieval across all supported spacecraft anomaly scenarios:
1. NORMAL (No runbook expected)
2. LOW_BATTERY (RB-EPS-001 expected)
3. HIGH_TEMPERATURE (RB-THM-001 expected)
4. WHEEL_DEGRADATION (RB-ADCS-001 expected)
"""

from __future__ import annotations

import sys
from ai_ml.retrieval.retriever import retrieve_anomaly_knowledge


def test_retrieval_suite() -> bool:
    print("\n================================================================================")
    print("           ORBITGUARD RETRIEVAL & RUNBOOK INTEGRATION TEST")
    print("   [Grounding: Advisory runbooks separated from live telemetry facts]")
    print("================================================================================\n")

    scenarios = [
        {
            "name": "NORMAL",
            "anomaly_type": None,
            "subsystem": None,
            "expected_runbook_id": None,
            "description": "Nominal spacecraft telemetry",
        },
        {
            "name": "LOW_BATTERY",
            "anomaly_type": "LOW_BATTERY",
            "subsystem": "EPS",
            "expected_runbook_id": "RB-EPS-001",
            "description": "Battery bus voltage excursion below threshold",
        },
        {
            "name": "HIGH_TEMPERATURE",
            "anomaly_type": "HIGH_TEMPERATURE",
            "subsystem": "Thermal",
            "expected_runbook_id": "RB-THM-001",
            "description": "Battery overheating / thermal runaway",
        },
        {
            "name": "WHEEL_DEGRADATION",
            "anomaly_type": "REACTION_WHEEL_OVERLOAD",
            "subsystem": "ADCS",
            "expected_runbook_id": "RB-ADCS-001",
            "description": "Reaction wheel jitter / attitude control error",
        },
    ]

    all_passed = True

    for i, sc in enumerate(scenarios, start=1):
        print(f"[{i}/{len(scenarios)}] Testing Scenario: {sc['name']}")
        knowledge = retrieve_anomaly_knowledge(
            anomaly_type=sc["anomaly_type"],
            subsystem=sc["subsystem"],
        )

        matched_rbs = [rb.runbook_id for rb in knowledge.runbooks]
        matched_cases = [c.case_id for c in knowledge.historical_cases]

        print(f"    - Matched Runbooks: {matched_rbs or 'None'}")
        print(f"    - Matched Historical Cases: {matched_cases or 'None'}")
        print(f"    - Recommended Actions: {knowledge.get_recommended_actions() or 'None'}")

        if sc["expected_runbook_id"] is None:
            passed = len(matched_rbs) == 0
        else:
            passed = sc["expected_runbook_id"] in matched_rbs

        if passed:
            print("    --> Result: PASS\n")
        else:
            print(f"    --> Result: FAIL (Expected: {sc['expected_runbook_id']}, Got: {matched_rbs})\n")
            all_passed = False

    print("--------------------------------------------------------------------------------")
    print(f"Retrieval Test Suite Verdict: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("--------------------------------------------------------------------------------\n")

    return all_passed


if __name__ == "__main__":
    success = test_retrieval_suite()
    sys.exit(0 if success else 1)
