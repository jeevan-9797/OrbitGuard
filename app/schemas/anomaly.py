"""Pydantic models for anomaly detection events."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Anomaly severity classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyEvent(BaseModel):
    """An anomaly detected in satellite telemetry."""

    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    satellite_id: str = Field(..., description="Affected satellite identifier")
    detected_at: datetime = Field(..., description="UTC detection timestamp")
    subsystem: str = Field(..., description="Affected subsystem")
    severity: SeverityLevel = Field(..., description="Severity classification")
    description: str = Field(..., description="Human-readable anomaly description")
    telemetry_snapshot: Optional[dict] = Field(
        default=None, description="Relevant telemetry values at detection time"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score"
    )
