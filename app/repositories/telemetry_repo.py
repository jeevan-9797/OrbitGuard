"""Telemetry Repository."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_db


class TelemetryRepository:

    @staticmethod
    def record_telemetry(
        satellite_id: str,
        subsystem_id: Optional[str],
        metric: str,
        value: float,
        unit: str,
        quality: str = "GOOD",
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO telemetry (satellite_id, subsystem_id, metric, value, unit, quality)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (satellite_id, subsystem_id, metric, value, unit, quality))
            cur.execute("SELECT * FROM telemetry WHERE satellite_id = %s ORDER BY id DESC LIMIT 1;", (satellite_id,))
            return cur.fetchone()

    @staticmethod
    def get_telemetry_window(
        satellite_id: str,
        metric: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        with get_db() as cur:
            if metric:
                cur.execute(
                    """
                    SELECT id, satellite_id, subsystem_id, timestamp, metric, value, unit, quality
                    FROM telemetry
                    WHERE satellite_id = %s AND metric = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (satellite_id, metric, limit)
                )
            else:
                cur.execute(
                    """
                    SELECT id, satellite_id, subsystem_id, timestamp, metric, value, unit, quality
                    FROM telemetry
                    WHERE satellite_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                    """,
                    (satellite_id, limit)
                )
            return cur.fetchall()

    @staticmethod
    def get_baseline(satellite_id: str, mode_code: str, metric: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                """
                SELECT * FROM telemetry_baselines
                WHERE (satellite_id = %s OR satellite_id IS NULL)
                  AND mode_code = %s
                  AND metric = %s
                LIMIT 1;
                """,
                (satellite_id, mode_code, metric)
            )
            return cur.fetchone()
