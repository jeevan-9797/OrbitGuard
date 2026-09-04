"""
Database Connection & Session Management
Module: app.database
Provides unified cursor access for PostgreSQL and SQLite fallback testing.
"""

import os
import re
import sqlite3
import json
from contextlib import contextmanager
from typing import Generator, Any
from app.config import settings
from database.connection import DatabaseManager, DatabaseConfig, PSYCOPG2_AVAILABLE
from database.test_core_migrations import convert_pg_ddl_to_sqlite

_SQLITE_CONN = None


def clean_sql_for_sqlite(sql_text: str) -> str:
    # Strip line comments first so statements don't start with --
    s = re.sub(r'--[^\n]*', '', sql_text)
    s = s.replace("::jsonb", "")
    s = re.sub(r'system_config\.version \+ 1', '1', s)
    s = re.sub(r"NOW\(\)\s*-\s*INTERVAL\s*'[^']+'", "datetime('now')", s, flags=re.IGNORECASE)
    s = re.sub(r"NOW\(\)\s*-\s*\([^)]+\)::interval", "datetime('now')", s, flags=re.IGNORECASE)
    s = re.sub(r"NOW\(\)", "datetime('now')", s, flags=re.IGNORECASE)
    s = re.sub(r"::numeric", "", s, flags=re.IGNORECASE)
    s = re.sub(r"::uuid", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\bTRUE\b", "1", s, flags=re.IGNORECASE)
    s = re.sub(r"\bFALSE\b", "0", s, flags=re.IGNORECASE)
    return s


def get_sqlite_fallback():
    """Initializes an in-memory SQLite database initialized with the core schema and seed data."""
    global _SQLITE_CONN
    if _SQLITE_CONN is None:
        _SQLITE_CONN = sqlite3.connect(":memory:", check_same_thread=False)
        _SQLITE_CONN.execute("PRAGMA foreign_keys = ON;")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        m1 = os.path.join(base_dir, "database", "migrations", "001_initial_core_schema.sql")
        m2 = os.path.join(base_dir, "database", "migrations", "002_knowledge_and_config.sql")
        sk = os.path.join(base_dir, "database", "seed", "knowledge.sql")
        ss = os.path.join(base_dir, "database", "seed", "satellites.sql")
        st = os.path.join(base_dir, "database", "seed", "telemetry.sql")
        
        for m in [m1, m2]:
            if os.path.exists(m):
                with open(m, "r", encoding="utf-8") as f:
                    ddl = convert_pg_ddl_to_sqlite(f.read())
                    _SQLITE_CONN.executescript(ddl)

        for s in [sk, ss, st]:
            if os.path.exists(s):
                with open(s, "r", encoding="utf-8") as f:
                    seed_sql = clean_sql_for_sqlite(f.read())
                    # Split on semicolon at end of line to preserve internal semicolons in strings
                    for stmt in re.split(r';\s*\n', seed_sql):
                        stmt_clean = stmt.strip()
                        if stmt_clean and "generate_series" not in stmt_clean:
                            try:
                                _SQLITE_CONN.execute(stmt_clean)
                            except Exception:
                                pass
        _SQLITE_CONN.commit()
    return _SQLITE_CONN


class DictCursorWrapper:
    """Wraps sqlite3 cursor to return dictionary rows similar to psycopg2 RealDictCursor."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query: str, params: Any = None):
        # Translate Postgres %s placeholders to SQLite ?
        q = query.replace("%s", "?")
        if params is None:
            return self._cursor.execute(q)
        # Handle dict or json serialization for parameters
        clean_params = []
        for p in params:
            if isinstance(p, (dict, list)):
                clean_params.append(json.dumps(p))
            else:
                clean_params.append(p)
        return self._cursor.execute(q, clean_params)

    def fetchone(self):
        row = self._cursor.fetchone()
        if not row:
            return None
        col_names = [col[0] for col in self._cursor.description]
        return dict(zip(col_names, row))

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows:
            return []
        col_names = [col[0] for col in self._cursor.description]
        return [dict(zip(col_names, r)) for r in rows]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


@contextmanager
def get_db():
    """
    Context manager yielding a cursor.
    Uses PostgreSQL pool if healthy; falls back to SQLite mock engine for local testing.
    """
    health = DatabaseManager.check_health()
    if health.get("status") == "HEALTHY" and PSYCOPG2_AVAILABLE:
        with DatabaseManager.get_connection() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    else:
        conn = get_sqlite_fallback()
        cursor = conn.cursor()
        wrapper = DictCursorWrapper(cursor)
        try:
            yield wrapper
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            wrapper.close()
