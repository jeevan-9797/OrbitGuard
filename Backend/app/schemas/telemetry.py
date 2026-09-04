"""Pydantic models for satellite telemetry data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """A single telemetry reading from a satellite."""

    satellite_id: str = Field(..., description="Unique identifier of the satellite")
    timestamp: datetime = Field(..., description="UTC timestamp of the reading")
    subsystem: str = Field(
        ..., description="Subsystem name (e.g. 'EPS', 'ADCS', 'COMMS')"
    )
    metric: str = Field(..., description="Metric name (e.g. 'battery_voltage')")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement (e.g. 'V', '°C')")
    metadata: Optional[dict] = Field(
        default=None, description="Optional extra context"
    )
