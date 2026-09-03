"""Pydantic models for recovery simulation results."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SimulationOutcome(str, Enum):
    """Possible simulation outcomes."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


class SimulationResult(BaseModel):
    """Result of simulating a recovery plan before execution."""

    simulation_id: str = Field(..., description="Unique simulation identifier")
    plan_id: str = Field(..., description="Recovery plan that was simulated")
    satellite_id: str = Field(..., description="Target satellite identifier")
    outcome: SimulationOutcome = Field(default=SimulationOutcome.SUCCESS, description="Simulation outcome")
    success_probability: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Predicted success probability"
    )
    side_effects: list[str] = Field(
        default_factory=list, description="Potential side effects identified"
    )
    recommended_adjustments: list[str] = Field(
        default_factory=list, description="Suggested plan modifications"
    )
    simulated_telemetry: list[dict] = Field(
        default_factory=list,
        description="Forward-simulated telemetry time-series points (before, during, after)",
    )
    steps_executed: list[dict] = Field(
        default_factory=list,
        description="Step-by-step digital twin simulation execution checkpoints",
    )
    logs: Optional[str] = Field(
        default=None, description="Detailed simulation log output"
    )
    simulated_at: datetime = Field(..., description="UTC simulation timestamp")

