"""Pydantic models for recovery plans."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk classification for a recovery plan."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecoveryStep(BaseModel):
    """A single step within a recovery plan."""

    step_number: int = Field(..., description="Execution order")
    action: str = Field(..., description="Action to perform")
    subsystem: str = Field(..., description="Target subsystem")
    expected_outcome: str = Field(..., description="Expected result of this step")
    rollback_action: Optional[str] = Field(
        default=None, description="Rollback procedure if this step fails"
    )


class RecoveryPlan(BaseModel):
    """A structured recovery plan for resolving a diagnosed anomaly."""

    plan_id: str = Field(..., description="Unique plan identifier")
    title: Optional[str] = Field(default=None, description="Descriptive title of the recovery strategy")
    diagnosis_id: str = Field(..., description="Related diagnosis identifier")
    satellite_id: str = Field(..., description="Target satellite identifier")
    actions: list[str] = Field(
        default_factory=list,
        description="Approved action commands (e.g. REDUCE_PAYLOAD_LOAD, ENTER_SAFE_THERMAL_MODE)",
    )
    preconditions: list[str] = Field(
        default_factory=list, description="Required state prerequisites before execution"
    )
    expected_effects: list[str] = Field(
        default_factory=list, description="Predicted outcome effects on satellite metrics"
    )
    steps: list[RecoveryStep] = Field(
        default_factory=list, description="Ordered recovery execution steps"
    )
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Overall risk assessment")
    risk_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Numerical risk score (0.0 to 1.0)")
    rollback_plan: Optional[str] = Field(
        default=None, description="Contingency rollback strategy if execution fails"
    )
    estimated_duration_seconds: int = Field(
        default=60, description="Estimated total recovery time"
    )
    requires_ground_approval: bool = Field(
        default=True, description="Whether ground control must approve execution"
    )
    validation_result: Optional[dict] = Field(
        default=None, description="Safety validator results and verdict"
    )
    created_at: datetime = Field(..., description="UTC plan creation timestamp")


