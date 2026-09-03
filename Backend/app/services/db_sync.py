"""Supabase and Local Persistence Synchronization Service for OrbitGuard.

Syncs telemetry time-series, incident state machine transitions, and audit logs
to Supabase with seamless local in-memory fallback.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.core.database import db

logger = logging.getLogger(__name__)


async def persist_telemetry_snapshot(telemetry: dict[str, Any]) -> dict[str, Any]:
    """Persist a single telemetry reading snapshot into the `telemetry_snapshots` table."""
    try:
        record = {
            "satellite_id": telemetry.get("satellite_id", "UNKNOWN"),
            "timestamp": telemetry.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "metrics": telemetry.get("metrics", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return await db.insert("telemetry_snapshots", record)
    except Exception as exc:
        logger.warning("persist_telemetry_snapshot failed: %s", exc)
        return telemetry


async def persist_incident_state(incident: Any) -> dict[str, Any]:
    """Persist or update an incident's full state into the `incidents` table."""
    try:
        if hasattr(incident, "model_dump"):
            data = incident.model_dump(mode="json")
        elif isinstance(incident, dict):
            data = incident
        else:
            data = dict(incident)

        record = {
            "incident_id": data.get("incident_id"),
            "satellite_id": data.get("satellite_id"),
            "status": data.get("status"),
            "anomaly_event": data.get("anomaly_event"),
            "diagnosis": data.get("diagnosis"),
            "recovery_plans": data.get("recovery_plans", []),
            "selected_plan_id": data.get("selected_plan_id"),
            "simulation_result": data.get("simulation_result"),
            "execution_result": data.get("execution_result"),
            "operator_notes": data.get("operator_notes"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return await db.upsert("incidents", record, on_conflict="incident_id")
    except Exception as exc:
        logger.warning("persist_incident_state failed: %s", exc)
        return data if isinstance(data, dict) else {}


async def persist_audit_event(event: Any, incident_id: str | None = None) -> dict[str, Any]:
    """Persist an audit log event or state transition into the `audit_events` table."""
    try:
        if hasattr(event, "model_dump"):
            data = event.model_dump(mode="json")
        elif isinstance(event, dict):
            data = event
        else:
            data = dict(event)

        record = {
            "incident_id": incident_id or data.get("incident_id", "GLOBAL"),
            "from_state": data.get("from_state"),
            "to_state": data.get("to_state"),
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "notes": data.get("notes"),
        }
        return await db.insert("audit_events", record)
    except Exception as exc:
        logger.warning("persist_audit_event failed: %s", exc)
        return data if isinstance(data, dict) else {}
