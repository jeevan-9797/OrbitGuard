"""Knowledge Base Repository."""

import json
from typing import List, Dict, Any
from app.database import get_db


class KnowledgeRepository:

    @staticmethod
    def get_allowed_actions() -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM action_catalog WHERE enabled = 1 OR enabled = true ORDER BY action_code ASC;")
            rows = cur.fetchall()
            for r in rows:
                for k in ("preconditions", "effects", "rollback"):
                    if isinstance(r.get(k), str):
                        try:
                            r[k] = json.loads(r[k])
                        except Exception:
                            pass
            return rows

    @staticmethod
    def get_safety_rules() -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM safety_rules WHERE enabled = 1 OR enabled = true ORDER BY rule_code ASC;")
            return cur.fetchall()

    @staticmethod
    def find_similar_incidents(anomaly_type: str, limit: int = 3) -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                """
                SELECT scenario, anomaly_type, evidence, diagnosis, resolution
                FROM historical_incidents
                WHERE anomaly_type = %s
                LIMIT %s;
                """,
                (anomaly_type, limit)
            )
            rows = cur.fetchall()
            for r in rows:
                for k in ("evidence", "diagnosis", "resolution"):
                    if isinstance(r.get(k), str):
                        try:
                            r[k] = json.loads(r[k])
                        except Exception:
                            pass
            return rows
