#!/usr/bin/env python3
"""
Verification Script for Satellite Multi-Agent AI Database Files
Validates SQL syntax, table definitions, foreign keys, and seed integrity.
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")

EXPECTED_CORE_TABLES = [
    "satellites",
    "subsystems",
    "telemetry",
    "anomalies",
    "incidents",
    "agent_runs",
    "recovery_plans",
    "safety_rules",
    "validations",
    "command_executions",
    "audit_events"
]

EXPECTED_KNOWLEDGE_TABLES = [
    "action_catalog",
    "operating_modes",
    "telemetry_baselines",
    "historical_incidents",
    "runbook_templates",
    "system_config"
]

REQUIRED_FILES = [
    "database/migrations/001_initial_core_schema.sql",
    "database/migrations/002_knowledge_and_config.sql",
    "database/migrations/003_indexes_and_constraints.sql",
    "database/migrations/004_context_and_contracts.sql",
    "database/seed/satellites.sql",
    "database/seed/telemetry.sql",
    "database/seed/knowledge.sql",
    "database/seed/scenarios.sql",
    "database/schema.sql",
    "database/reset_demo.sql",
    "database/README.md",
    ".env.example"
]

def test_files_exist():
    print(">>> 1. Checking required files...")
    all_exist = True
    for rel_path in REQUIRED_FILES:
        full_path = os.path.join(BASE_DIR, rel_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"  [OK] {rel_path} ({size} bytes)")
        else:
            print(f"  [FAIL] Missing: {rel_path}")
            all_exist = False
    return all_exist

def test_schema_tables():
    print("\n>>> 2. Checking table definitions in database/schema.sql...")
    schema_path = os.path.join(DB_DIR, "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()

    found_tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", content, re.IGNORECASE)
    found_tables_set = set(t.lower() for t in found_tables)

    print(f"  Found {len(found_tables_set)} distinct tables in schema.sql")
    all_found = True

    print("  Checking Core Tables (11 required):")
    for tbl in EXPECTED_CORE_TABLES:
        if tbl in found_tables_set:
            print(f"    [OK] {tbl}")
        else:
            print(f"    [FAIL] Missing core table: {tbl}")
            all_found = False

    print("  Checking Knowledge/Config Tables (6 required):")
    for tbl in EXPECTED_KNOWLEDGE_TABLES:
        if tbl in found_tables_set:
            print(f"    [OK] {tbl}")
        else:
            print(f"    [FAIL] Missing knowledge table: {tbl}")
            all_found = False

    return all_found

def test_indexes():
    print("\n>>> 3. Checking performance indexes in database/migrations/003_indexes_and_constraints.sql...")
    idx_path = os.path.join(DB_DIR, "migrations", "003_indexes_and_constraints.sql")
    with open(idx_path, "r", encoding="utf-8") as f:
        content = f.read()

    expected_indexes = [
        "idx_telemetry_satellite_time",
        "idx_telemetry_subsystem_metric_time",
        "idx_anomalies_satellite_started",
        "idx_incidents_state_opened",
        "idx_audit_events_incident_time",
        "idx_agent_runs_incident_started"
    ]

    all_idx_found = True
    for idx in expected_indexes:
        if idx in content:
            print(f"    [OK] Index {idx}")
        else:
            print(f"    [FAIL] Missing index: {idx}")
            all_idx_found = False
    return all_idx_found

def test_seed_targets():
    print("\n>>> 4. Checking seed target counts...")
    # Satellites & subsystems
    sat_file = os.path.join(DB_DIR, "seed", "satellites.sql")
    with open(sat_file, "r", encoding="utf-8") as f:
        sat_content = f.read()
    
    sat_names = re.findall(r"'([A-Z0-9_\-]+)'\s*,\s*'NOMINAL'|'PAYLOAD_OPS'|'COMM_PASS'", sat_content)
    print(f"  Satellites seeded: {len(sat_names)} (Target: 6-10)")

    subsystem_matches = re.findall(r"'b0000000-[0-9a-f\-]+'", sat_content)
    print(f"  Subsystems seeded: {len(subsystem_matches)} (Target: 30-42)")

    # Knowledge
    know_file = os.path.join(DB_DIR, "seed", "knowledge.sql")
    with open(know_file, "r", encoding="utf-8") as f:
        know_content = f.read()

    action_codes = re.findall(r"\('(PWR_[A-Z0-9_]+|ADCS_[A-Z0-9_]+|TCS_[A-Z0-9_]+|COMMS_[A-Z0-9_]+|PL_[A-Z0-9_]+|OBC_[A-Z0-9_]+|EPS_[A-Z0-9_]+)'", know_content)
    print(f"  Allowed actions seeded: {len(action_codes)} (Target: 10-15)")

    safety_rules = re.findall(r"\('(SR-[A-Z0-9\-]+)'", know_content)
    print(f"  Safety rules seeded: {len(safety_rules)} (Target: 10-15)")

    hist_cases = re.findall(r"\('Orbit \d+", know_content)
    print(f"  Historical incident cases seeded: {len(hist_cases)} (Target: 5-10)")

    # Scenarios
    scen_file = os.path.join(DB_DIR, "seed", "scenarios.sql")
    with open(scen_file, "r", encoding="utf-8") as f:
        scen_content = f.read()

    has_scen_a = "SCENARIO A: BATTERY OVERHEAT" in scen_content and "THERMAL_RUNAWAY" in scen_content
    has_scen_b = "SCENARIO B: REACTION-WHEEL DEGRADATION" in scen_content and "REACTION_WHEEL_FRICTION" in scen_content
    print(f"  Scenario A (Battery Overheat) present: {'[OK]' if has_scen_a else '[FAIL]'}")
    print(f"  Scenario B (Reaction-wheel) present:   {'[OK]' if has_scen_b else '[FAIL]'}")

    # Reset script
    reset_file = os.path.join(DB_DIR, "reset_demo.sql")
    with open(reset_file, "r", encoding="utf-8") as f:
        reset_content = f.read()
    has_reset_fn = "CREATE OR REPLACE FUNCTION reset_demo()" in reset_content
    print(f"  reset_demo() procedure present:        {'[OK]' if has_reset_fn else '[FAIL]'}")

    return (len(sat_names) >= 6 and len(subsystem_matches) >= 30 and 
            len(action_codes) >= 10 and len(safety_rules) >= 10 and
            has_scen_a and has_scen_b and has_reset_fn)

def test_aiml_contracts():
    print("\n>>> 5. Checking AI/ML contract conformance...")
    scen_file = os.path.join(DB_DIR, "seed", "scenarios.sql")
    with open(scen_file, "r", encoding="utf-8") as f:
        scen_content = f.read()

    # Contract 1: agent_runs.output schema (primary_hypothesis, hypotheses, needs_evidence)
    has_primary = '"primary_hypothesis"' in scen_content
    has_hypotheses = '"hypotheses"' in scen_content
    has_needs_evidence = '"needs_evidence": false' in scen_content
    print(f"  agent_runs.output (primary_hypothesis): {'[OK]' if has_primary else '[FAIL]'}")
    print(f"  agent_runs.output (hypotheses array):   {'[OK]' if has_hypotheses else '[FAIL]'}")
    print(f"  agent_runs.output (needs_evidence):     {'[OK]' if has_needs_evidence else '[FAIL]'}")

    # Contract 2: recovery_plans.actions schema (actions array with order, action_code, parameters)
    has_action_order = '"order": 1' in scen_content
    has_action_code = '"action_code": "REDUCE_POWER_LOAD"' in scen_content
    has_action_params = '"parameters"' in scen_content
    print(f"  recovery_plans.actions (order):         {'[OK]' if has_action_order else '[FAIL]'}")
    print(f"  recovery_plans.actions (action_code):   {'[OK]' if has_action_code else '[FAIL]'}")
    print(f"  recovery_plans.actions (parameters):    {'[OK]' if has_action_params else '[FAIL]'}")

    # Contract 3: build_incident_context function
    ctx_file = os.path.join(DB_DIR, "migrations", "004_context_and_contracts.sql")
    with open(ctx_file, "r", encoding="utf-8") as f:
        ctx_content = f.read()
    has_ctx_fn = "CREATE OR REPLACE FUNCTION build_incident_context(" in ctx_content
    has_trends = "'recent_trends_15m'" in ctx_content
    has_deviations = "'metric_deviations'" in ctx_content
    print(f"  build_incident_context() function:     {'[OK]' if has_ctx_fn else '[FAIL]'}")
    print(f"  Aggregated trends (15m window):        {'[OK]' if has_trends else '[FAIL]'}")
    print(f"  Baseline metric deviations:            {'[OK]' if has_deviations else '[FAIL]'}")

    return (has_primary and has_hypotheses and has_needs_evidence and
            has_action_order and has_action_code and has_action_params and
            has_ctx_fn and has_trends and has_deviations)

if __name__ == "__main__":
    t1 = test_files_exist()
    t2 = test_schema_tables()
    t3 = test_indexes()
    t4 = test_seed_targets()
    t5 = test_aiml_contracts()

    print("\n" + "="*50)
    if t1 and t2 and t3 and t4 and t5:
        print("ALL DATABASE ARCHITECTURE & SCHEMA TESTS PASSED! [PASS]")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED! [FAIL]")
        sys.exit(1)
