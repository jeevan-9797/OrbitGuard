"""Audit Trail Event Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AuditEventCreate(BaseModel):
    incident_id: str
    event_type: str = Field(
        pattern="^(ANOMALY_DETECTED|INCIDENT_OPENED|AGENT_STARTED|AGENT_COMPLETED|PLAN_GENERATED|VALIDATION_COMPLETED|PLAN_REJECTED|PLAN_APPROVED|COMMAND_EXECUTED|OUTCOME_VERIFIED|RUNBOOK_GENERATED|INCIDENT_RESOLVED|MANUAL_OVERRIDE)$"
    )
    actor: str
    payload: Dict[str, Any] = {}


class AuditEvent(AuditEventCreate):
    id: int
    timestamp: Optional[str] = None
