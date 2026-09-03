"""Anomaly & Incident Lifecycle Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AnomalyCreate(BaseModel):
    satellite_id: str
    subsystem_id: Optional[str] = None
    type: str
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: Dict[str, Any] = {}


class Anomaly(AnomalyCreate):
    id: str
    started_at: Optional[str] = None
    resolved_at: Optional[str] = None


class IncidentCreate(BaseModel):
    satellite_id: str
    anomaly_id: Optional[str] = None
    title: str
    priority: str = Field(default="P2", pattern="^(P1|P2|P3|P4)$")
    severity: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    primary_hypothesis: Optional[str] = None


class IncidentStateTransition(BaseModel):
    target_state: str = Field(
        pattern="^(DETECTED|INVESTIGATING|DIAGNOSED|PLANNING|VALIDATING|APPROVED|REJECTED|EXECUTING|VERIFYING|RESOLVED|FAILED)$"
    )
    actor: str = "SYSTEM"
    notes: Optional[str] = None


class Incident(BaseModel):
    id: str
    anomaly_id: Optional[str] = None
    satellite_id: str
    state: str
    title: str
    priority: str
    severity: str
    confidence: Optional[float] = None
    primary_hypothesis: Optional[str] = None
    current_plan_id: Optional[str] = None
    resolution_code: Optional[str] = None
    opened_at: Optional[str] = None
    resolved_at: Optional[str] = None
