"""
Core Database Migration & Integrity Verification Suite
Module: database.test_core_migrations
Verifies:
1. Migration execution and schema parsing.
2. All 11 core tables exist.
3. Foreign key relationships and cascade rules.
4. Telemetry and workflow indexes.
5. Rejection of invalid foreign keys, invalid check constraints, and duplicate unique keys.
"""

import os
import sys
import sqlite3
import re
from typing import Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATION_001_PATH = os.path.join(BASE_DIR, "database", "migrations", "001_initial_core_schema.sql")

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

EXPECTED_INDEXES = [
    "idx_telemetry_satellite_time",
    "idx_telemetry_subsystem_metric_time",
    "idx_anomalies_satellite_started",
    "idx_incidents_state_opened",
    "idx_audit_events_incident_time",
    "idx_agent_runs_incident_started"
]


def convert_pg_ddl_to_sqlite(pg_sql: str) -> str:
    """Converts PostgreSQL DDL to compatible SQLite syntax for fast local in-memory integrity testing."""
    sql = pg_sql
    # Remove extensions and alter statements
    sql = re.sub(r'CREATE EXTENSION[^;]+;', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'UUID PRIMARY KEY DEFAULT [a-zA-Z0-9_()]+', 'TEXT PRIMARY KEY', sql, flags=re.IGNORECASE)
    sql = re.sub(r'UUID', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'BIGSERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'TIMESTAMPTZ NOT NULL DEFAULT NOW\(\)', "TEXT NOT NULL DEFAULT (datetime('now'))", sql, flags=re.IGNORECASE)
    sql = re.sub(r'TIMESTAMPTZ', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'JSONB NOT NULL DEFAULT \'[^\']+\'::jsonb', "TEXT NOT NULL DEFAULT '{}'", sql, flags=re.IGNORECASE)
    sql = re.sub(r'JSONB', 'TEXT', sql, flags=re.IGNORECASE)
    sql = re.sub(r'DOUBLE PRECISION', 'REAL', sql, flags=re.IGNORECASE)
    sql = re.sub(r'NUMERIC\(\d+,\s*\d+\)', 'REAL', sql, flags=re.IGNORECASE)
    # Remove circular ALTER TABLE fk_incident_current_plan (SQLite handles this via inline or ignores)
    sql = re.sub(r'ALTER TABLE incidents\s+ADD CONSTRAINT[^\;]+\;', '', sql, flags=re.IGNORECASE)
    return sql


def test_core_migration_execution():
    print("=" * 80)
    print("PHASE 3: CORE DATABASE MIGRATIONS VERIFICATION")
    print("=" * 80)

    # 1. Read Migration 001
    print("\n>>> 1. Loading and parsing 001_initial_core_schema.sql...")
    if not os.path.exists(MIGRATION_001_PATH):
        print(f"  [FAIL] Missing file: {MIGRATION_001_PATH}")
        return False
    with open(MIGRATION_001_PATH, "r", encoding="utf-8") as f:
        pg_ddl = f.read()

    sqlite_ddl = convert_pg_ddl_to_sqlite(pg_ddl)
    print(f"  [OK] Migration 001 read successfully ({len(pg_ddl)} bytes).")

    # Connect to in-memory SQLite with full foreign keys enabled
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Execute DDL
    try:
        cursor.executescript(sqlite_ddl)
        print("  [OK] Core schema DDL executed successfully.")
    except Exception as e:
        print(f"  [FAIL] DDL execution failed: {e}")
        return False

    # 2. Verify all 11 tables exist
    print("\n>>> 2. Verifying Table Existence (11 core tables required)...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    existing_tables = set(r[0] for r in cursor.fetchall())

    all_tables_present = True
    for tbl in EXPECTED_CORE_TABLES:
        if tbl in existing_tables:
            print(f"  [OK] Table: {tbl:<22} exists.")
        else:
            print(f"  [FAIL] Table: {tbl:<22} MISSING!")
            all_tables_present = False

    if not all_tables_present:
        return False

    # 3. Verify Indexes
    print("\n>>> 3. Verifying Recommended Telemetry & Workflow Indexes...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    existing_indexes = set(r[0] for r in cursor.fetchall())

    all_indexes_present = True
    for idx in EXPECTED_INDEXES:
        if idx in existing_indexes:
            print(f"  [OK] Index: {idx} exists.")
        else:
            print(f"  [FAIL] Index: {idx} MISSING!")
            all_indexes_present = False

    if not all_indexes_present:
        return False

    # 4. Verify Foreign Key Enforcements & Cascades
    print("\n>>> 4. Testing Foreign Key Enforcements & Cascades...")

    # Insert a valid satellite
    sat_id = "a0000000-0000-0000-0000-000000000001"
    cursor.execute(
        "INSERT INTO satellites (id, name, mode, status, risk_score) VALUES (?, ?, ?, ?, ?);",
        (sat_id, "ASTRAEA-1", "NOMINAL", "ONLINE", 0.05)
    )

    # Insert a valid subsystem
    sub_id = "b0000000-0000-0000-0001-000000000001"
    cursor.execute(
        "INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES (?, ?, ?, ?, ?);",
        (sub_id, sat_id, "EPS", "HEALTHY", 100.0)
    )

    # Insert valid telemetry
    cursor.execute(
        "INSERT INTO telemetry (satellite_id, subsystem_id, metric, value, unit, quality) VALUES (?, ?, ?, ?, ?, ?);",
        (sat_id, sub_id, "battery_temperature", 24.5, "C", "GOOD")
    )
    print("  [OK] Valid parent-child insertions succeeded.")

    # 5. Test Invalid Foreign Key Reference Rejection
    print("\n>>> 5. Testing Rejection of Invalid Foreign Keys...")
    invalid_sat_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"

    # A. Subsystem pointing to non-existent satellite
    try:
        cursor.execute(
            "INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES (?, ?, ?, ?, ?);",
            ("b0000000-0000-0000-0001-999999999999", invalid_sat_id, "FAULTY_SUB", "HEALTHY", 100.0)
        )
        print("  [FAIL] Invalid subsystem satellite_id was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Subsystem with non-existent satellite_id correctly REJECTED (Foreign Key violation).")

    # B. Telemetry pointing to non-existent satellite
    try:
        cursor.execute(
            "INSERT INTO telemetry (satellite_id, subsystem_id, metric, value, unit, quality) VALUES (?, ?, ?, ?, ?, ?);",
            (invalid_sat_id, sub_id, "wheel_rpm", 2400.0, "RPM", "GOOD")
        )
        print("  [FAIL] Invalid telemetry satellite_id was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Telemetry with non-existent satellite_id correctly REJECTED (Foreign Key violation).")

    # C. Incident pointing to non-existent satellite
    try:
        cursor.execute(
            "INSERT INTO incidents (id, satellite_id, title, state, priority, severity) VALUES (?, ?, ?, ?, ?, ?);",
            ("d0000000-0000-0000-0000-999999999999", invalid_sat_id, "Ghost Incident", "DETECTED", "P1", "HIGH")
        )
        print("  [FAIL] Invalid incident satellite_id was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Incident with non-existent satellite_id correctly REJECTED (Foreign Key violation).")

    # 6. Test CHECK Constraint Rejections
    print("\n>>> 6. Testing CHECK Constraint Rejections...")

    # A. Invalid incident state
    try:
        cursor.execute(
            "INSERT INTO incidents (id, satellite_id, title, state, priority, severity) VALUES (?, ?, ?, ?, ?, ?);",
            ("d0000000-0000-0000-0000-000000000001", sat_id, "Bad State Incident", "INVALID_STATE", "P1", "HIGH")
        )
        print("  [FAIL] Invalid incident state was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Invalid incident state ('INVALID_STATE') correctly REJECTED (CHECK constraint violation).")

    # B. Invalid subsystem health score (> 100)
    try:
        cursor.execute(
            "INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES (?, ?, ?, ?, ?);",
            ("b0000000-0000-0000-0001-000000000002", sat_id, "TCS", "HEALTHY", 150.0)
        )
        print("  [FAIL] Invalid subsystem health_score was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Subsystem health_score > 100 correctly REJECTED (CHECK constraint violation).")

    # C. Invalid satellite status
    try:
        cursor.execute(
            "INSERT INTO satellites (id, name, mode, status, risk_score) VALUES (?, ?, ?, ?, ?);",
            ("a0000000-0000-0000-0000-000000000002", "TEST-SAT", "NOMINAL", "EXPLODED", 0.1)
        )
        print("  [FAIL] Invalid satellite status was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Invalid satellite status ('EXPLODED') correctly REJECTED (CHECK constraint violation).")

    # 7. Test UNIQUE Constraint Rejection
    print("\n>>> 7. Testing UNIQUE Constraint Rejections...")
    try:
        cursor.execute(
            "INSERT INTO subsystems (id, satellite_id, name, status, health_score) VALUES (?, ?, ?, ?, ?);",
            ("b0000000-0000-0000-0001-000000000003", sat_id, "EPS", "DEGRADED", 50.0)
        )
        print("  [FAIL] Duplicate subsystem name for same satellite was NOT rejected!")
        return False
    except sqlite3.IntegrityError:
        print("  [OK] Duplicate subsystem name ('EPS') for same satellite correctly REJECTED (UNIQUE constraint violation).")

    # 8. Test Cascade Delete
    print("\n>>> 8. Testing ON DELETE CASCADE...")
    cursor.execute("DELETE FROM satellites WHERE id = ?;", (sat_id,))
    cursor.execute("SELECT count(*) FROM subsystems WHERE satellite_id = ?;", (sat_id,))
    sub_count = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM telemetry WHERE satellite_id = ?;", (sat_id,))
    tel_count = cursor.fetchone()[0]

    if sub_count == 0 and tel_count == 0:
        print("  [OK] Deleting satellite successfully cascaded to subsystems and telemetry.")
    else:
        print(f"  [FAIL] Cascade delete failed! Remaining subsystems: {sub_count}, telemetry: {tel_count}")
        return False

    print("\n" + "=" * 80)
    print("ALL CORE MIGRATION & INTEGRITY TESTS PASSED! [PASS]")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_core_migration_execution()
    sys.exit(0 if success else 1)
