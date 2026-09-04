"""Audit Event Repository."""

import json
from typing import List, Dict, Any
from app.database import get_db


class AuditRepository:

    @staticmethod
    def log_audit_event(
        incident_id: str,
        event_type: str,
        actor: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO audit_events (incident_id, event_type, actor, payload)
        VALUES (%s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (incident_id, event_type, actor, json.dumps(payload)))
            cur.execute("SELECT * FROM audit_events WHERE incident_id = %s ORDER BY id DESC LIMIT 1;", (incident_id,))
            row = cur.fetchone()
            if isinstance(row.get("payload"), str):
                try:
                    row["payload"] = json.loads(row["payload"])
                except Exception:
                    pass
            return row

    @staticmethod
    def get_audit_events(incident_id: str) -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                "SELECT * FROM audit_events WHERE incident_id = %s ORDER BY timestamp ASC;",
                (incident_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                if isinstance(r.get("payload"), str):
                    try:
                        r["payload"] = json.loads(r["payload"])
                    except Exception:
                        pass
            return rows
