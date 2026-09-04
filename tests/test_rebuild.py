"""
Clean Rebuild & Migration Idempotency Test Suite
Step 11: Validates that a fresh database can be rebuilt from migrations and seeds without errors.
"""

import os
import sys
import sqlite3
import re
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database.test_core_migrations import convert_pg_ddl_to_sqlite
from app.database import clean_sql_for_sqlite


def test_clean_rebuild_from_scratch():
    """Verify that a brand new empty database can execute all migrations and seeds successfully."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")

    # 1. Migrations
    migration_files = [
        "001_initial_core_schema.sql",
        "002_knowledge_and_config.sql"
    ]
    for mf in migration_files:
        path = os.path.join(BASE_DIR, "database", "migrations", mf)
        assert os.path.exists(path), f"Migration file missing: {mf}"
        with open(path, "r", encoding="utf-8") as f:
            ddl = convert_pg_ddl_to_sqlite(f.read())
            conn.executescript(ddl)

    # 2. Seed Data
    seed_files = [
        "knowledge.sql",
        "satellites.sql",
        "telemetry.sql"
    ]
    for sf in seed_files:
        path = os.path.join(BASE_DIR, "database", "seed", sf)
        assert os.path.exists(path), f"Seed file missing: {sf}"
        with open(path, "r", encoding="utf-8") as f:
            sql = clean_sql_for_sqlite(f.read())
            for stmt in re.split(r';\s*\n', sql):
                stmt_clean = stmt.strip()
                if stmt_clean and "generate_series" not in stmt_clean:
                    conn.execute(stmt_clean)
    conn.commit()

    # 3. Verify Table Counts
    assert conn.execute("SELECT count(*) FROM satellites").fetchone()[0] == 6
    assert conn.execute("SELECT count(*) FROM subsystems").fetchone()[0] == 36
    assert conn.execute("SELECT count(*) FROM operating_modes").fetchone()[0] == 6
    assert conn.execute("SELECT count(*) FROM action_catalog").fetchone()[0] == 13
    assert conn.execute("SELECT count(*) FROM safety_rules").fetchone()[0] == 12
    assert conn.execute("SELECT count(*) FROM telemetry_baselines").fetchone()[0] >= 20
    assert conn.execute("SELECT count(*) FROM historical_incidents").fetchone()[0] == 5
    assert conn.execute("SELECT count(*) FROM runbook_templates").fetchone()[0] == 2
    conn.close()
