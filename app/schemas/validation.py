"""Pydantic models for recovery plan validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class ValidationCheck(BaseModel):
    """Result of an individual validation check."""

    check_name: str = Field(..., description="Name of the validation check")
    passed: bool = Field(..., description="Whether the check passed")
    message: str = Field(..., description="Detail or failure reason")


class ValidationResult(BaseModel):
    """Aggregated result of validating a recovery plan."""

    validation_id: str = Field(..., description="Unique validation identifier")
    plan_id: str = Field(..., description="Related recovery plan identifier")
    is_valid: bool = Field(default=True, description="Overall pass/fail validity verdict")
    is_safe: bool = Field(default=True, description="Deterministic safety compliance flag")
    violations: list[str] = Field(
        default_factory=list, description="Non-negotiable safety constraint violations"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Operational advisory warnings"
    )
    checks: list[ValidationCheck] = Field(
        default_factory=list, description="Individual check results"
    )
    safety_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Computed safety score (0.0 to 1.0)"
    )
    validated_at: datetime = Field(..., description="UTC validation timestamp")

