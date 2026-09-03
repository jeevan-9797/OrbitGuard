"""Pydantic models for anomaly diagnosis results."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DiagnosisResult(BaseModel):
    """Result of an AI-driven anomaly diagnosis."""

    diagnosis_id: str = Field(..., description="Unique diagnosis identifier")
    anomaly_id: str = Field(..., description="Related anomaly identifier")
    satellite_id: str = Field(..., description="Affected satellite identifier")
    primary_hypothesis: str = Field(..., description="Primary diagnostic hypothesis / root cause")
    root_cause: Optional[str] = Field(default=None, description="Identified root cause (alias/summary)")
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative hypotheses considered"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Observed evidence supporting hypothesis"
    )
    checks: list[str] = Field(
        default_factory=list, description="Diagnostic verification checks performed"
    )
    contributing_factors: list[str] = Field(
        default_factory=list, description="Additional contributing factors"
    )
    affected_subsystems: list[str] = Field(
        default_factory=list, description="Subsystems impacted by the anomaly"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Diagnosis confidence score"
    )
    reasoning: Optional[str] = Field(
        default=None, description="LLM reasoning chain / explanation"
    )
    diagnosed_at: datetime = Field(..., description="UTC timestamp of diagnosis")

