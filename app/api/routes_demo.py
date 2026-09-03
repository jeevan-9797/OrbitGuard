"""Demo Management & Knowledge API Routes."""

from fastapi import APIRouter, Query
from typing import List, Dict, Any
from app.repositories.knowledge_repo import KnowledgeRepository
from database.reset import reset_demo_state

router = APIRouter(prefix="/api", tags=["Demo & Knowledge"])


@router.post("/demo/reset")
def reset_demo():
    """Resets demo database back to clean baseline state in < 100ms."""
    success = reset_demo_state()
    return {"status": "SUCCESS" if success else "FAILED", "message": "Demo fleet baseline restored"}


@router.get("/knowledge/actions")
def get_action_catalog():
    """Closed vocabulary of valid spacecraft actions for AI planner."""
    return KnowledgeRepository.get_allowed_actions()


@router.get("/knowledge/rules")
def get_safety_rules():
    """Deterministic safety guardrails."""
    return KnowledgeRepository.get_safety_rules()


@router.get("/knowledge/similar-incidents")
def get_similar_incidents(anomaly_type: str = Query(...), limit: int = Query(3, ge=1, le=10)):
    """Curated historical cases for AI few-shot retrieval."""
    return KnowledgeRepository.find_similar_incidents(anomaly_type=anomaly_type, limit=limit)
