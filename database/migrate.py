"""
Migration Runner & Version Management
Module: database.migrate
Tracks schema migrations via the schema_migrations table, detects pending files, and applies migrations sequentially.
"""

import os
import sys
import hashlib
import glob
from datetime import datetime
from database.connection import DatabaseManager, DatabaseConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "database", "migrations")

SCHEMA_MIGRATIONS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    checksum VARCHAR(64) NOT NULL
);
"""


def compute_checksum(filepath: str) -> str:
    """Computes SHA-256 hash of a migration file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_available_migrations():
    """Returns sorted list of available migration files."""
    pattern = os.path.join(MIGRATIONS_DIR, "*.sql")
    files = sorted(glob.glob(pattern))
    migrations = []
    for f in files:
        basename = os.path.basename(f)
        parts = basename.split("_", 1)
        version = parts[0]
        name = parts[1].replace(".sql", "") if len(parts) > 1 else basename
        migrations.append({
            "version": version,
            "name": name,
            "filename": basename,
            "filepath": f,
            "checksum": compute_checksum(f)
        })
    return migrations


def ensure_migration_table(conn):
    """Creates the schema_migrations table if not already present."""
    with conn.cursor() as cursor:
        cursor.execute(SCHEMA_MIGRATIONS_TABLE_DDL)


def get_applied_migrations(conn):
    """Fetches applied migrations map from database."""
    ensure_migration_table(conn)
    with conn.cursor() as cursor:
        cursor.execute("SELECT version, name, applied_at, checksum FROM schema_migrations ORDER BY id ASC;")
        rows = cursor.fetchall()
        applied = {}
        for r in rows:
            applied[r[0]] = {
                "version": r[0],
                "name": r[1],
                "applied_at": r[2],
                "checksum": r[3]
            }
        return applied


def migration_status():
    """Prints migration status comparison between disk and database."""
    available = get_available_migrations()
    health = DatabaseManager.check_health()

    print("\n" + "=" * 80)
    print("DATABASE MIGRATION STATUS")
    print("=" * 80)
    print(f"Migrations Directory: {MIGRATIONS_DIR}")
    print(f"Database Target:      {DatabaseConfig.get_safe_summary().get('host')}:{DatabaseConfig.get_safe_summary().get('port')}/{DatabaseConfig.get_safe_summary().get('database')}")
    print(f"Connection Status:    {health.get('status')}")
    print("-" * 80)

    if health.get("status") != "HEALTHY":
        print("[NOTICE] Database offline or unreachable. Listing files discovered on disk:\n")
        print(f"{'Version':<10} {'Name':<35} {'Checksum (prefix)':<20} {'Status'}")
        print("-" * 80)
        for m in available:
            print(f"{m['version']:<10} {m['name']:<35} {m['checksum'][:16]:<20} PENDING (Offline)")
        print("-" * 80)
        return False

    with DatabaseManager.get_connection() as conn:
        applied = get_applied_migrations(conn)

    print(f"{'Version':<10} {'Name':<35} {'Status':<12} {'Applied At'}")
    print("-" * 80)

    pending_count = 0
    for m in available:
        v = m["version"]
        if v in applied:
            app = applied[v]
            match_status = "OK" if app["checksum"] == m["checksum"] else "MODIFIED!"
            applied_str = app["applied_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(app["applied_at"], datetime) else str(app["applied_at"])
            print(f"{v:<10} {m['name']:<35} {'APPLIED (' + match_status + ')':<12} {applied_str}")
        else:
            pending_count += 1
            print(f"{v:<10} {m['name']:<35} {'PENDING':<12} -")

    print("-" * 80)
    print(f"Total Available: {len(available)} | Applied: {len(applied)} | Pending: {pending_count}\n")
    return True


def apply_migrations(dry_run: bool = False):
    """Executes all pending migrations in sequential order."""
    available = get_available_migrations()
    health = DatabaseManager.check_health()

    if dry_run:
        print("\n[DRY-RUN MODE] Inspecting pending migrations without applying:")
        for m in available:
            print(f"  -> Would execute: {m['filename']} (checksum: {m['checksum'][:16]}...)")
        return True

    if health.get("status") != "HEALTHY":
        print(f"[ERROR] Cannot run migrations: Database is unreachable.")
        print(f"Details: {health.get('error') or health.get('message')}")
        return False

    with DatabaseManager.get_connection() as conn:
        applied = get_applied_migrations(conn)
        pending = [m for m in available if m["version"] not in applied]

        if not pending:
            print("[INFO] Database is up to date. No pending migrations.")
            return True

        print(f"\n[INFO] Found {len(pending)} pending migration(s). Applying sequentially...")

        for m in pending:
            print(f"  Applying {m['filename']}...", end=" ", flush=True)
            with open(m["filepath"], "r", encoding="utf-8") as f:
                sql_script = f.read()

            try:
                with conn.cursor() as cursor:
                    # Execute migration SQL
                    cursor.execute(sql_script)
                    # Record in schema_migrations
                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (version, name, checksum, applied_at)
                        VALUES (%s, %s, %s, NOW());
                        """,
                        (m["version"], m["name"], m["checksum"])
                    )
                conn.commit()
                print("DONE [SUCCESS]")
            except Exception as e:
                conn.rollback()
                print("FAILED [ERROR]")
                print(f"[ERROR] Migration failed in {m['filename']}:\n{e}")
                return False

    print("\n[SUCCESS] All pending migrations applied successfully.")
    return True


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "status":
        migration_status()
    elif action == "up":
        apply_migrations(dry_run=False)
    elif action == "dry-run":
        apply_migrations(dry_run=True)
    else:
        print(f"Unknown action: {action}")
        print("Usage: python -m database.migrate [status|up|dry-run]")
