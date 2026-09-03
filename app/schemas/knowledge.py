"""Knowledge & Configuration Pydantic Schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ActionCatalogItem(BaseModel):
    action_code: str
    description: str
    preconditions: Dict[str, Any] = {}
    effects: Dict[str, Any] = {}
    rollback: Dict[str, Any] = {}
    risk_level: str = "LOW"
    enabled: bool = True


class SafetyRule(BaseModel):
    rule_code: str
    name: str
    condition: str
    severity: str = "CRITICAL_BLOCKER"
    enabled: bool = True
