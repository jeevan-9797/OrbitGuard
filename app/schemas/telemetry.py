"""Telemetry Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TelemetryPoint(BaseModel):
    id: Optional[int] = None
    satellite_id: str
    subsystem_id: Optional[str] = None
    timestamp: Optional[str] = None
    metric: str
    value: float
    unit: str
    quality: str = Field(default="GOOD", pattern="^(GOOD|SUSPECT|BAD)$")


class TelemetryCreate(BaseModel):
    satellite_id: str
    subsystem_id: Optional[str] = None
    metric: str
    value: float
    unit: str
    quality: str = "GOOD"


class TelemetryWindowResponse(BaseModel):
    satellite_id: str
    metric: Optional[str] = None
    points_count: int
    points: List[TelemetryPoint]


class TelemetryBaseline(BaseModel):
    satellite_id: Optional[str] = None
    mode_code: str
    subsystem_id: Optional[str] = None
    metric: str
    min_val: float
    max_val: float
    mean: float
    stddev: float
