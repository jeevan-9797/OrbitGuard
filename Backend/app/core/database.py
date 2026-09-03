"""Supabase Database Client integration with in-memory fallback resilience.

Initializes Supabase connection using SUPABASE_URL and SUPABASE_KEY.
If credentials are missing or network calls fail, gracefully diverts data to
local in-memory collections so backend workflows never crash.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Local In-Memory Fallback Tables ──────────────────────────────────────────
_in_memory_db: dict[str, list[dict[str, Any]]] = {
    "telemetry_snapshots": [],
    "incidents": [],
    "audit_events": [],
    "recovery_plans": [],
}


class DatabaseManager:
    """Manages Supabase connectivity with transparent in-memory fallback."""

    def __init__(self) -> None:
        self._client = None
        self._initialized = False
        self._is_connected = False
        self._init_client()

    def _init_client(self) -> None:
        """Attempt to instantiate the official Supabase client."""
        url = settings.SUPABASE_URL.strip()
        key = settings.SUPABASE_KEY.strip()

        if not url or not key:
            logger.info("Supabase credentials not configured. Using in-memory fallback storage.")
            self._client = None
            self._is_connected = False
            self._initialized = True
            return

        try:
            from supabase import Client, create_client
            self._client: Client | None = create_client(url, key)
            self._is_connected = True
            logger.info("Supabase client successfully initialized for %s", url)
        except Exception as exc:
            logger.warning(
                "Failed to initialize Supabase client (%s). Operating in local in-memory fallback mode.",
                exc,
            )
            self._client = None
            self._is_connected = False
        self._initialized = True

    @property
    def is_connected(self) -> bool:
        """Return True if active Supabase connection is established."""
        return self._is_connected and self._client is not None

    def get_client(self):
        """Return raw Supabase client or None."""
        return self._client

    def get_status(self) -> str:
        """Return status string for health endpoints."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            return "not_configured"
        return "connected" if self.is_connected else "fallback_active"

    async def insert(self, table: str, record: dict[str, Any]) -> dict[str, Any]:
        """Insert a record into Supabase or fallback to in-memory store."""
        # Always record in in-memory table for fast local retrieval
        if table not in _in_memory_db:
            _in_memory_db[table] = []
        _in_memory_db[table].append(record)

        if self.is_connected:
            try:
                res = self._client.table(table).insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as exc:
                logger.warning("Supabase insert to '%s' failed (%s). Saved in local fallback.", table, exc)

        return record

    async def upsert(self, table: str, record: dict[str, Any], on_conflict: str = "incident_id") -> dict[str, Any]:
        """Upsert a record into Supabase or in-memory store."""
        if table not in _in_memory_db:
            _in_memory_db[table] = []

        # In-memory upsert replacement
        replaced = False
        for idx, existing in enumerate(_in_memory_db[table]):
            if existing.get(on_conflict) == record.get(on_conflict):
                _in_memory_db[table][idx] = record
                replaced = True
                break
        if not replaced:
            _in_memory_db[table].append(record)

        if self.is_connected:
            try:
                res = self._client.table(table).upsert(record, on_conflict=on_conflict).execute()
                if res.data:
                    return res.data[0]
            except Exception as exc:
                logger.warning("Supabase upsert to '%s' failed (%s). Saved in local fallback.", table, exc)

        return record

    async def query(self, table: str, limit: int = 50) -> list[dict[str, Any]]:
        """Query records from Supabase with in-memory fallback."""
        if self.is_connected:
            try:
                res = self._client.table(table).select("*").limit(limit).execute()
                if res.data:
                    return res.data
            except Exception as exc:
                logger.warning("Supabase query on '%s' failed (%s). Returning in-memory records.", table, exc)

        records = _in_memory_db.get(table, [])
        return records[-limit:]

    def clear_local_db(self) -> None:
        """Clear all local in-memory fallback tables (used on simulator reset)."""
        for k in _in_memory_db:
            _in_memory_db[k].clear()


db = DatabaseManager()
