"""Fleet & Subsystem Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SubsystemBase(BaseModel):
    name: str
    status: str = "HEALTHY"
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)


class Subsystem(SubsystemBase):
    id: str
    satellite_id: str
    created_at: Optional[str] = None


class SatelliteBase(BaseModel):
    name: str
    mode: str = "NOMINAL"
    status: str = "ONLINE"
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)


class Satellite(SatelliteBase):
    id: str
    created_at: Optional[str] = None
    subsystems: List[Subsystem] = []


class FleetSummaryItem(BaseModel):
    id: str
    name: str
    mode: str
    status: str
    risk_score: float
    active_incident_count: int = 0
