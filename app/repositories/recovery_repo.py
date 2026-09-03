"""Recovery Plan, Safety Validation & Command Execution Repository."""

import uuid
import json
from typing import List, Dict, Any, Optional
from app.database import get_db


class RecoveryRepository:

    @staticmethod
    def create_recovery_plan(
        incident_id: str,
        version: int,
        rationale: str,
        actions: Dict[str, Any],
        risk_level: str = "LOW",
        selected: bool = False
    ) -> Dict[str, Any]:
        plan_id = str(uuid.uuid4())
        query = """
        INSERT INTO recovery_plans (id, incident_id, version, rationale, actions, risk_level, selected)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(
                query,
                (plan_id, incident_id, version, rationale, json.dumps(actions), risk_level, selected)
            )
            cur.execute("SELECT * FROM recovery_plans WHERE id = %s;", (plan_id,))
            row = cur.fetchone()
            if isinstance(row.get("actions"), str):
                try:
                    row["actions"] = json.loads(row["actions"])
                except Exception:
                    pass
            return row

    @staticmethod
    def get_recovery_plans(incident_id: str) -> List[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute(
                "SELECT * FROM recovery_plans WHERE incident_id = %s ORDER BY version ASC;",
                (incident_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                if isinstance(r.get("actions"), str):
                    try:
                        r["actions"] = json.loads(r["actions"])
                    except Exception:
                        pass
            return rows

    @staticmethod
    def get_recovery_plan(plan_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM recovery_plans WHERE id = %s;", (plan_id,))
            row = cur.fetchone()
            if row and isinstance(row.get("actions"), str):
                try:
                    row["actions"] = json.loads(row["actions"])
                except Exception:
                    pass
            return row

    @staticmethod
    def save_validation(
        plan_id: str,
        status: str,
        passed_rules: List[str],
        failed_rules: List[Dict[str, Any]],
        validator_version: str = "v1.2.0-deterministic"
    ) -> Dict[str, Any]:
        val_id = str(uuid.uuid4())
        query = """
        INSERT INTO validations (id, plan_id, status, passed_rules, failed_rules, validator_version)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(
                query,
                (val_id, plan_id, status, json.dumps(passed_rules), json.dumps(failed_rules), validator_version)
            )
            cur.execute("SELECT * FROM validations WHERE id = %s;", (val_id,))
            row = cur.fetchone()
            for k in ("passed_rules", "failed_rules"):
                if isinstance(row.get(k), str):
                    try:
                        row[k] = json.loads(row[k])
                    except Exception:
                        pass
            return row

    @staticmethod
    def get_validation(plan_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM validations WHERE plan_id = %s ORDER BY validated_at DESC LIMIT 1;", (plan_id,))
            row = cur.fetchone()
            if row:
                for k in ("passed_rules", "failed_rules"):
                    if isinstance(row.get(k), str):
                        try:
                            row[k] = json.loads(row[k])
                        except Exception:
                            pass
            return row

    @staticmethod
    def save_command_execution(
        plan_id: str,
        status: str,
        command: Dict[str, Any],
        before_state: Dict[str, Any],
        after_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        exec_id = str(uuid.uuid4())
        query = """
        INSERT INTO command_executions (id, plan_id, status, command, before_state, after_state)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        with get_db() as cur:
            cur.execute(
                query,
                (exec_id, plan_id, status, json.dumps(command), json.dumps(before_state), json.dumps(after_state))
            )
            cur.execute("SELECT * FROM command_executions WHERE id = %s;", (exec_id,))
            row = cur.fetchone()
            for k in ("command", "before_state", "after_state"):
                if isinstance(row.get(k), str):
                    try:
                        row[k] = json.loads(row[k])
                    except Exception:
                        pass
            return row

    @staticmethod
    def get_execution(plan_id: str) -> Optional[Dict[str, Any]]:
        with get_db() as cur:
            cur.execute("SELECT * FROM command_executions WHERE plan_id = %s ORDER BY executed_at DESC LIMIT 1;", (plan_id,))
            row = cur.fetchone()
            if row:
                for k in ("command", "before_state", "after_state"):
                    if isinstance(row.get(k), str):
                        try:
                            row[k] = json.loads(row[k])
                        except Exception:
                            pass
            return row
