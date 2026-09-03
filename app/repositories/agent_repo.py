"""Agent Run Repository."""

import uuid
import json
from typing import List, Dict, Any, Optional
from app.database import get_db


class AgentRepository:

    @staticmethod
    def save_agent_run(
        incident_id: str,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence: Optional[float] = None,
        status: str = "COMPLETED"
    ) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        query = """
        INSERT INTO agent_runs (id, incident_id, agent_name, status, input, output, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(
                query,
                (run_id, incident_id, agent_name, status, json.dumps(input_data), json.dumps(output_data), confidence)
            )
            cur.execute("SELECT * FROM agent_runs WHERE id = %s;", (run_id,))
            row = cur.fetchone()
            for k in ("input", "output"):
                if isinstance(row.get(k), str):
                    try:
                        row[k] = json.loads(row[k])
                    except Exception:
                        pass
            return row

    @staticmethod
    def get_agent_runs(incident_id: str) -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                "SELECT * FROM agent_runs WHERE incident_id = %s ORDER BY started_at ASC;",
                (incident_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                for k in ("input", "output"):
                    if isinstance(r.get(k), str):
                        try:
                            r[k] = json.loads(r[k])
                        except Exception:
                            pass
            return rows

    @staticmethod
    def get_latest_diagnosis(incident_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                """
                SELECT * FROM agent_runs 
                WHERE incident_id = %s AND agent_name IN ('diagnostic_agent', 'diagnostician', 'diagnosis')
                ORDER BY started_at DESC LIMIT 1;
                """,
                (incident_id,)
            )
            row = cur.fetchone()
            if row:
                for k in ("input", "output"):
                    if isinstance(row.get(k), str):
                        try:
                            row[k] = json.loads(row[k])
                        except Exception:
                            pass
            return row
