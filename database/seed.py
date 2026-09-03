"""
Database Seeding Script
Module: database.seed
Executes deterministic seed datasets in order: knowledge -> satellites -> telemetry -> scenarios.
"""

import os
import sys
import time
from database.connection import DatabaseManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "database", "seed")

SEED_SEQUENCE = [
    ("knowledge.sql", "Operating modes, action catalog, safety rules, runbook templates, and system config"),
    ("satellites.sql", "6 Fleet satellites (ASTRAEA-1 to FORNAX-6) and 36 subsystems"),
    ("telemetry.sql", "Telemetry baselines and nominal 30-minute operational time-series readings"),
    ("scenarios.sql", "Deterministic scenarios: Scenario A (Battery Overheat) & Scenario B (Reaction Wheel)")
]


def run_seeds():
    health = DatabaseManager.check_health()
    if health.get("status") != "HEALTHY":
        print(f"[ERROR] Cannot run seed scripts: Database is unreachable.")
        print(f"Details: {health.get('error') or health.get('message')}")
        return False

    print("\n" + "=" * 80)
    print("DATABASE SEEDING SEQUENCE")
    print("=" * 80)

    total_start = time.time()
    with DatabaseManager.get_connection() as conn:
        for filename, description in SEED_SEQUENCE:
            filepath = os.path.join(SEED_DIR, filename)
            if not os.path.exists(filepath):
                print(f"[ERROR] Missing seed file: {filepath}")
                return False

            print(f"Executing {filename} ({description})...", end=" ", flush=True)
            step_start = time.time()
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()

            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_content)
                conn.commit()
                elapsed = round((time.time() - step_start) * 1000, 2)
                print(f"DONE [{elapsed} ms]")
            except Exception as e:
                conn.rollback()
                print("FAILED [ERROR]")
                print(f"[ERROR] Seeding failed in {filename}:\n{e}")
                return False

    total_elapsed = round((time.time() - total_start) * 1000, 2)
    print("=" * 80)
    print(f"[SUCCESS] All seed datasets loaded successfully in {total_elapsed} ms.\n")
    return True


if __name__ == "__main__":
    success = run_seeds()
    sys.exit(0 if success else 1)
