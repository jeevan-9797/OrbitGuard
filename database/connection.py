"""
Database Connection & Health Management
Module: database.connection
Handles environment loading, PostgreSQL / Supabase connection pooling, health checks, and permission verification.
"""

import os
import sys
import time
from contextlib import contextmanager
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env file from project root if present
load_dotenv()

try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class DatabaseConfig:
    """Extracts and validates database configuration from environment variables."""

    @classmethod
    def get_database_url(cls) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url.strip()

        # Fallback to discrete parameters
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "satellite_ai")
        sslmode = os.getenv("DB_SSLMODE", "prefer")

        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
        return f"postgresql://{user}@{host}:{port}/{dbname}?sslmode={sslmode}"

    @classmethod
    def get_safe_summary(cls) -> dict:
        """Returns connection target details without exposing secrets."""
        url = cls.get_database_url()
        try:
            parsed = urlparse(url)
            return {
                "scheme": parsed.scheme,
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip("/"),
                "user": parsed.username or "unspecified",
                "password_configured": bool(parsed.password),
                "sslmode": parsed.query or "default"
            }
        except Exception:
            return {"error": "Invalid connection URL format"}


class DatabaseManager:
    """Manages database connections, health checks, and permissions."""

    _pool = None

    @classmethod
    def get_pool(cls):
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2-binary is not installed in the current environment.")

        if cls._pool is None:
            db_url = DatabaseConfig.get_database_url()
            minconn = int(os.getenv("DB_POOL_MIN_CONNECTIONS", 1))
            maxconn = int(os.getenv("DB_POOL_MAX_CONNECTIONS", 10))
            cls._pool = psycopg2.pool.SimpleConnectionPool(minconn, maxconn, db_url)
        return cls._pool

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Context manager yielding a connection, ensuring commit or rollback."""
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2-binary is not installed.")

        conn = None
        try:
            pool_instance = cls.get_pool()
            conn = pool_instance.getconn()
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and cls._pool:
                cls._pool.putconn(conn)

    @classmethod
    def check_health(cls) -> dict:
        """Verifies database connectivity with a ping query."""
        if not PSYCOPG2_AVAILABLE:
            return {"status": "ERROR", "message": "psycopg2-binary driver missing"}

        start_time = time.time()
        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 AS ping, version();")
                    row = cursor.fetchone()
                    elapsed_ms = round((time.time() - start_time) * 1000, 2)
                    return {
                        "status": "HEALTHY",
                        "ping": row[0] if row else 1,
                        "server_version": row[1] if row and len(row) > 1 else "PostgreSQL",
                        "latency_ms": elapsed_ms,
                        "target": DatabaseConfig.get_safe_summary()
                    }
        except Exception as e:
            return {
                "status": "UNREACHABLE",
                "error": str(e),
                "target": DatabaseConfig.get_safe_summary(),
                "hint": "Ensure PostgreSQL/Supabase is running and DATABASE_URL is configured in .env"
            }

    @classmethod
    def check_permissions(cls) -> dict:
        """
        Validates DDL (CREATE, DROP) and DML (INSERT, SELECT, DELETE) permissions.
        Creates and tears down a temporary verification table.
        """
        table_name = "_permission_test_probe"
        results = {
            "CREATE_TABLE": False,
            "INSERT": False,
            "SELECT": False,
            "DELETE": False,
            "DROP_TABLE": False
        }

        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. CREATE
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INT, note TEXT);")
                    results["CREATE_TABLE"] = True

                    # 2. INSERT
                    cursor.execute(f"INSERT INTO {table_name} (id, note) VALUES (1, 'probe');")
                    results["INSERT"] = True

                    # 3. SELECT
                    cursor.execute(f"SELECT note FROM {table_name} WHERE id = 1;")
                    val = cursor.fetchone()
                    if val and val[0] == 'probe':
                        results["SELECT"] = True

                    # 4. DELETE
                    cursor.execute(f"DELETE FROM {table_name} WHERE id = 1;")
                    results["DELETE"] = True

                    # 5. DROP
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                    results["DROP_TABLE"] = True

            all_passed = all(results.values())
            return {
                "status": "PASSED" if all_passed else "FAILED",
                "permissions": results
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "permissions": results
            }


if __name__ == "__main__":
    print("Database Configuration Summary:")
    for k, v in DatabaseConfig.get_safe_summary().items():
        print(f"  {k}: {v}")

    print("\nRunning Health Check...")
    health = DatabaseManager.check_health()
    print(f"  Status: {health.get('status')}")
    if health.get("status") == "HEALTHY":
        print(f"  Latency: {health.get('latency_ms')} ms")
        print("\nChecking Permissions...")
        perms = DatabaseManager.check_permissions()
        print(f"  Permission Check: {perms.get('status')}")
        for op, granted in perms.get("permissions", {}).items():
            print(f"    {op}: {'GRANTED' if granted else 'DENIED'}")
    else:
        print(f"  Details: {health.get('error') or health.get('message')}")
        print(f"  Hint: {health.get('hint')}")
