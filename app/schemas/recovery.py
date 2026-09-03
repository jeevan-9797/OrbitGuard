"""Recovery Plan, Safety Validation & Execution Pydantic Schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RecoveryAction(BaseModel):
    order: int
    action_code: str
    parameters: Dict[str, Any] = {}


class RecoveryPlanActions(BaseModel):
    actions: List[RecoveryAction]


class RecoveryPlanCreate(BaseModel):
    incident_id: str
    version: int = 1
    rationale: str
    actions: RecoveryPlanActions
    risk_level: str = Field(default="LOW", pattern="^(LOW|MEDIUM|HIGH|EXTREME)$")


class RecoveryPlan(BaseModel):
    id: str
    incident_id: str
    version: int
    rationale: str
    actions: Dict[str, Any]
    risk_level: str
    selected: bool = False
    created_at: Optional[str] = None


class ValidationCreate(BaseModel):
    plan_id: str
    status: str = Field(pattern="^(PASSED|FAILED|WARNING)$")
    passed_rules: List[str] = []
    failed_rules: List[Dict[str, Any]] = []
    validator_version: str = "v1.2.0-deterministic"


class Validation(ValidationCreate):
    id: str
    validated_at: Optional[str] = None


class CommandExecutionCreate(BaseModel):
    plan_id: str
    status: str = Field(default="PENDING", pattern="^(PENDING|EXECUTING|SUCCESS|FAILED|ROLLED_BACK)$")
    command: Dict[str, Any] = {}
    before_state: Dict[str, Any] = {}
    after_state: Dict[str, Any] = {}


class CommandExecution(CommandExecutionCreate):
    id: str
    executed_at: Optional[str] = None
