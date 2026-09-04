"""Anomaly & Incident Repository."""

import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database import get_db


class IncidentRepository:

    @staticmethod
    def create_anomaly(
        satellite_id: str,
        type: str,
        severity: str,
        confidence: float,
        evidence: Dict[str, Any],
        subsystem_id: Optional[str] = None
    ) -> Dict[str, Any]:
        anom_id = str(uuid.uuid4())
        query = """
        INSERT INTO anomalies (id, satellite_id, subsystem_id, type, severity, confidence, evidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (anom_id, satellite_id, subsystem_id, type, severity, confidence, json.dumps(evidence)))
            cur.execute("SELECT * FROM anomalies WHERE id = %s;", (anom_id,))
            row = cur.fetchone()
            if isinstance(row.get("evidence"), str):
                try:
                    row["evidence"] = json.loads(row["evidence"])
                except Exception:
                    pass
            return row

    @staticmethod
    def create_incident(
        satellite_id: str,
        title: str,
        priority: str = "P2",
        severity: str = "MEDIUM",
        confidence: Optional[float] = None,
        primary_hypothesis: Optional[str] = None,
        anomaly_id: Optional[str] = None
    ) -> Dict[str, Any]:
        inc_id = str(uuid.uuid4())
        query = """
        INSERT INTO incidents (id, satellite_id, anomaly_id, title, state, priority, severity, confidence, primary_hypothesis)
        VALUES (%s, %s, %s, %s, 'DETECTED', %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(query, (inc_id, satellite_id, anomaly_id, title, priority, severity, confidence, primary_hypothesis))
            cur.execute("SELECT * FROM incidents WHERE id = %s;", (inc_id,))
            return cur.fetchone()

    @staticmethod
    def get_incident(incident_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM incidents WHERE id = %s;", (incident_id,))
            return cur.fetchone()

    @staticmethod
    def update_incident_state(incident_id: str, target_state: str, resolution_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            if target_state in ('RESOLVED', 'FAILED'):
                cur.execute(
                    """
                    UPDATE incidents 
                    SET state = %s, resolution_code = %s, resolved_at = datetime('now')
                    WHERE id = %s;
                    """,
                    (target_state, resolution_code, incident_id)
                )
            else:
                cur.execute(
                    "UPDATE incidents SET state = %s WHERE id = %s;",
                    (target_state, incident_id)
                )
            cur.execute("SELECT * FROM incidents WHERE id = %s;", (incident_id,))
            return cur.fetchone()

    @staticmethod
    def set_current_plan(incident_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("UPDATE incidents SET current_plan_id = %s WHERE id = %s;", (plan_id, incident_id))
            cur.execute("SELECT * FROM incidents WHERE id = %s;", (incident_id,))
            return cur.fetchone()

    @staticmethod
    def build_incident_context(incident_id: str) -> Dict[str, Any]:
        """
        Returns pre-aggregated, token-efficient incident context for AI/ML agents.
        Includes current deviations from baseline and 15m trend stats instead of raw bulk telemetry.
        """
        with get_db() as cur:
            # 1. Fetch Incident
            cur.execute("SELECT * FROM incidents WHERE id = %s;", (incident_id,))
            incident = cur.fetchone()
            if not incident:
                return {"error": "Incident not found", "incident_id": incident_id}

            # 2. Fetch Satellite
            cur.execute("SELECT * FROM satellites WHERE id = %s;", (incident["satellite_id"],))
            satellite = cur.fetchone()

            # 3. Fetch Anomaly
            anomaly = None
            if incident.get("anomaly_id"):
                cur.execute("SELECT * FROM anomalies WHERE id = %s;", (incident["anomaly_id"],))
                anomaly = cur.fetchone()
                if anomaly and isinstance(anomaly.get("evidence"), str):
                    try:
                        anomaly["evidence"] = json.loads(anomaly["evidence"])
                    except Exception:
                        pass

            # 4. Fetch Subsystem
            subsystem = None
            if anomaly and anomaly.get("subsystem_id"):
                cur.execute("SELECT * FROM subsystems WHERE id = %s;", (anomaly["subsystem_id"],))
                subsystem = cur.fetchone()

            # 5. Calculate Telemetry Deviations vs Baselines
            cur.execute(
                """
                SELECT metric, value, unit, quality, timestamp
                FROM telemetry
                WHERE satellite_id = %s
                ORDER BY timestamp DESC
                LIMIT 50;
                """,
                (incident["satellite_id"],)
            )
            raw_readings = cur.fetchall()

            # Get distinct latest per metric
            latest_by_metric = {}
            for r in raw_readings:
                m = r["metric"]
                if m not in latest_by_metric:
                    latest_by_metric[m] = r

            deviations = []
            for metric, reading in latest_by_metric.items():
                cur.execute(
                    """
                    SELECT min_val, max_val, mean, stddev
                    FROM telemetry_baselines
                    WHERE (satellite_id = %s OR satellite_id IS NULL)
                      AND mode_code = %s
                      AND metric = %s
                    LIMIT 1;
                    """,
                    (incident["satellite_id"], satellite["mode"], metric)
                )
                b = cur.fetchone()
                if b:
                    z_score = round((reading["value"] - b["mean"]) / b["stddev"], 2) if b["stddev"] > 0 else 0.0
                    range_status = "ELEVATED" if reading["value"] > b["max_val"] else ("DEPRESSED" if reading["value"] < b["min_val"] else "NOMINAL")
                    deviations.append({
                        "metric": metric,
                        "current_value": reading["value"],
                        "unit": reading["unit"],
                        "quality": reading["quality"],
                        "range_status": range_status,
                        "baseline": {"min": b["min_val"], "max": b["max_val"], "mean": b["mean"]},
                        "z_score": z_score
                    })
                else:
                    deviations.append({
                        "metric": metric,
                        "current_value": reading["value"],
                        "unit": reading["unit"],
                        "quality": reading["quality"],
                        "range_status": "UNKNOWN_BASELINE",
                        "z_score": 0.0
                    })

            # 6. Fetch Allowed Actions from Catalog
            cur.execute("SELECT action_code, description, risk_level, enabled FROM action_catalog WHERE enabled = 1 OR enabled = true;")
            allowed_actions = cur.fetchall()

            # 7. Assemble Structured Context Object
            return {
                "incident": {
                    "id": incident["id"],
                    "title": incident["title"],
                    "state": incident["state"],
                    "priority": incident["priority"],
                    "severity": incident["severity"],
                    "opened_at": incident.get("opened_at")
                },
                "satellite": {
                    "id": satellite["id"],
                    "name": satellite["name"],
                    "mode": satellite["mode"],
                    "risk_score": satellite["risk_score"]
                },
                "subsystem": {
                    "name": subsystem["name"],
                    "status": subsystem["status"],
                    "health_score": subsystem["health_score"]
                } if subsystem else None,
                "anomaly": {
                    "type": anomaly["type"],
                    "severity": anomaly["severity"],
                    "confidence": anomaly["confidence"],
                    "evidence": anomaly.get("evidence")
                } if anomaly else None,
                "metric_deviations": deviations,
                "action_catalog": allowed_actions
            }
