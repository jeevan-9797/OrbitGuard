"""Fleet & Subsystem Repository."""

import uuid
from typing import List, Dict, Any, Optional
from app.database import get_db


class FleetRepository:

    @staticmethod
    def get_fleet_summary() -> List[Dict[str, Any]]:
        query = """
        SELECT 
            s.id,
            s.name,
            s.mode,
            s.status,
            s.risk_score,
            COUNT(i.id) AS active_incident_count
        FROM satellites s
        LEFT JOIN incidents i 
            ON i.satellite_id = s.id 
           AND i.state NOT IN ('RESOLVED', 'FAILED')
        GROUP BY s.id, s.name, s.mode, s.status, s.risk_score
        ORDER BY s.name ASC;
        """
        with get_db() as cur:
            cur.execute(query)
            return cur.fetchall()

    @staticmethod
    def get_satellite_by_id(satellite_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM satellites WHERE id = %s;", (satellite_id,))
            sat = cur.fetchone()
            if not sat:
                return None
            cur.execute("SELECT * FROM subsystems WHERE satellite_id = %s ORDER BY name ASC;", (satellite_id,))
            sat["subsystems"] = cur.fetchall()
            return sat

    @staticmethod
    def create_satellite(name: str, mode: str = "NOMINAL", status: str = "ONLINE", risk_score: float = 0.0) -> Dict[str, Any]:
        sat_id = str(uuid.uuid4())
        query = """
        INSERT INTO satellites (id, name, mode, status, risk_score)
        VALUES (%s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (sat_id, name, mode, status, risk_score))
            cur.execute("SELECT * FROM satellites WHERE id = %s;", (sat_id,))
            return cur.fetchone()

    @staticmethod
    def create_subsystem(satellite_id: str, name: str, status: str = "HEALTHY", health_score: float = 100.0) -> Dict[str, Any]:
        sub_id = str(uuid.uuid4())
        query = """
        INSERT INTO subsystems (id, satellite_id, name, status, health_score)
        VALUES (%s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (sub_id, satellite_id, name, status, health_score))
            cur.execute("SELECT * FROM subsystems WHERE id = %s;", (sub_id,))
            return cur.fetchone()
