"""Pydantic models for satellite telemetry data."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============================================================
# Backend telemetry schemas
# ============================================================

class TelemetryPoint(BaseModel):
    id: Optional[int] = None
    satellite_id: str
    subsystem_id: Optional[str] = None
    timestamp: Optional[str] = None
    metric: str
    value: float
    unit: str
    quality: str = Field(
        default="GOOD",
        pattern="^(GOOD|SUSPECT|BAD)$"
    )


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


# ============================================================
# AI/ML telemetry schema
# ============================================================

class TelemetryEvent(BaseModel):
    """A single telemetry reading from a satellite."""

    satellite_id: str = Field(
        ...,
        description="Unique identifier of the satellite"
    )

    timestamp: datetime = Field(
        ...,
        description="UTC timestamp of the reading"
    )

    subsystem: str = Field(
        ...,
        description="Subsystem name (e.g. 'EPS', 'ADCS', 'COMMS')"
    )

    metric: str = Field(
        ...,
        description="Metric name (e.g. 'battery_voltage')"
    )

    value: float = Field(
        ...,
        description="Measured value"
    )

    unit: str = Field(
        ...,
        description="Unit of measurement (e.g. 'V', '°C')"
    )

    metadata: Optional[dict] = Field(
        default=None,
        description="Optional extra context"
    )