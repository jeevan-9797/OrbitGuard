"""
Demo Reset Execution Script
Module: database.reset
Executes reset_demo() procedure to wipe operational incident history and restore nominal fleet baseline.
"""

import os
import sys
import json
import time
from database.connection import DatabaseManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESET_SQL_PATH = os.path.join(BASE_DIR, "database", "reset_demo.sql")


def reset_demo_state():
    health = DatabaseManager.check_health()
    if health.get("status") != "HEALTHY":
        # Reset local SQLite fallback engine
        try:
            from app.database import get_sqlite_fallback
            c = get_sqlite_fallback()
            c.execute("DELETE FROM audit_events;")
            c.execute("DELETE FROM command_executions;")
            c.execute("DELETE FROM validations;")
            c.execute("DELETE FROM recovery_plans;")
            c.execute("DELETE FROM agent_runs;")
            c.execute("DELETE FROM incidents;")
            c.execute("DELETE FROM anomalies;")
            c.execute("DELETE FROM telemetry WHERE quality IN ('BAD', 'SUSPECT');")
            c.execute("UPDATE satellites SET mode = 'NOMINAL', status = 'ONLINE', risk_score = 0.050;")
            c.execute("UPDATE subsystems SET status = 'HEALTHY', health_score = 100.0;")
            c.commit()
            print("[SUCCESS] Local demo state successfully reset to nominal baseline.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to reset local database: {e}")
            return False

    print("\n" + "=" * 80)
    print("EXECUTING DEMO STATE RESET")
    print("=" * 80)

    start_time = time.time()
    with DatabaseManager.get_connection() as conn:
        try:
            with conn.cursor() as cursor:
                # Try calling stored function reset_demo()
                cursor.execute("SELECT reset_demo();")
                row = cursor.fetchone()
                result = row[0] if row else {}
            conn.commit()

            elapsed = round((time.time() - start_time) * 1000, 2)
            print(f"[SUCCESS] Demo reset completed in {elapsed} ms.")
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except Exception:
                    pass
            print(f"Result: {json.dumps(result, indent=2)}")
            return True
        except Exception as e:
            # Fallback to direct script execution if function doesn't exist yet
            print(f"[NOTICE] Direct procedure call failed ({e}). Attempting full script execution...")
            conn.rollback()
            try:
                with open(RESET_SQL_PATH, "r", encoding="utf-8") as f:
                    script = f.read()
                with conn.cursor() as cursor:
                    cursor.execute(script)
                conn.commit()
                elapsed = round((time.time() - start_time) * 1000, 2)
                print(f"[SUCCESS] Demo reset script executed in {elapsed} ms.")
                return True
            except Exception as script_err:
                conn.rollback()
                print(f"[ERROR] Failed to execute reset script:\n{script_err}")
                return False


if __name__ == "__main__":
    success = reset_demo_state()
    sys.exit(0 if success else 1)
