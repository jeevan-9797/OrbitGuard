"""AI Agent Run & Reasoning Trace Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class PrimaryHypothesis(BaseModel):
    cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]


class Hypothesis(BaseModel):
    cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]


class DiagnosisOutput(BaseModel):
    primary_hypothesis: PrimaryHypothesis
    hypotheses: List[Hypothesis]
    needs_evidence: bool = False


class AgentRunCreate(BaseModel):
    incident_id: str
    agent_name: str
    status: str = Field(default="COMPLETED", pattern="^(RUNNING|COMPLETED|FAILED)$")
    input: Dict[str, Any] = {}
    output: Dict[str, Any] = {}
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AgentRun(AgentRunCreate):
    id: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
