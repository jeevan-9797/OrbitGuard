"""
Knowledge Retrieval Engine for OrbitGuard.

Retrieves relevant operational runbooks and historical anomaly cases to enrich
agent diagnostics and recovery planning.

Enforces strict provenance separation: retrieved advisory knowledge is clearly
demarcated from real-time live telemetry facts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ai_ml.runbook.runbook_manager import RunbookEntry, RunbookManager


@dataclass
class HistoricalCase:
    """Historical flight anomaly record."""

    case_id: str
    mission: str
    subsystem: str
    anomaly_type: str
    observed_symptoms: str
    resolution_applied: str
    outcome: str
    lessons_learned: str
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "source": "FLIGHT_ANOMALY_DATABASE_ARCHIVE",
            "status": "HISTORICAL_REFERENCE_ONLY",
            "is_advisory": True,
        }
    )


@dataclass
class RetrievedKnowledge:
    """Aggregated retrieval context for a spacecraft anomaly."""

    query_anomaly: Optional[str]
    query_subsystem: Optional[str]
    runbooks: list[RunbookEntry] = field(default_factory=list)
    historical_cases: list[HistoricalCase] = field(default_factory=list)
    disclaimer: str = (
        "RETRIEVED ADVISORY ONLY: Historical records and runbook SOPs are reference "
        "guidance and must NOT be treated as live telemetry facts or confirmed physical states."
    )

    def has_matches(self) -> bool:
        return bool(self.runbooks or self.historical_cases)

    def get_recommended_actions(self) -> list[str]:
        """Aggregate unique recommended recovery actions from matching runbooks."""
        actions: list[str] = []
        for rb in self.runbooks:
            for act in rb.recommended_actions:
                if act not in actions:
                    actions.append(act)
        return actions

    def get_diagnostic_checks(self) -> list[str]:
        """Aggregate diagnostic verification checks from matching runbooks."""
        checks: list[str] = []
        for rb in self.runbooks:
            for chk in rb.diagnostic_checks:
                if chk not in checks:
                    checks.append(chk)
        return checks

    def get_safety_constraints(self) -> list[str]:
        """Aggregate safety constraints from matching runbooks."""
        constraints: list[str] = []
        for rb in self.runbooks:
            for c in rb.safety_constraints:
                if c not in constraints:
                    constraints.append(c)
        return constraints

    def format_for_prompt(self) -> str:
        """Format retrieved knowledge clearly tagged for LLM prompt context."""
        if not self.has_matches():
            return "No historical runbook or incident records applicable."

        sections = [
            "=== RETRIEVED ADVISORY FLIGHT RUNBOOKS & HISTORICAL OPS (REFERENCE ONLY) ===",
            f"DISCLAIMER: {self.disclaimer}\n",
        ]

        if self.runbooks:
            sections.append("--- Applicable Standard Operating Procedures (Runbooks) ---")
            for rb in self.runbooks:
                sections.append(f"• Runbook ID: {rb.runbook_id} - {rb.title}")
                sections.append(f"  Target Subsystem: {rb.subsystem}")
                sections.append(f"  Trigger Condition: {rb.trigger_condition}")
                sections.append(f"  Recommended Actions: {', '.join(rb.recommended_actions)}")
                sections.append(f"  Key Safety Constraints: {'; '.join(rb.safety_constraints)}")
                sections.append(f"  Rollback Procedure: {rb.rollback_procedure}")
            sections.append("")

        if self.historical_cases:
            sections.append("--- Verified Historical Flight Precedents ---")
            for case in self.historical_cases:
                sections.append(f"• Case ID: {case.case_id} ({case.mission})")
                sections.append(f"  Subsystem: {case.subsystem} | Anomaly: {case.anomaly_type}")
                sections.append(f"  Symptom: {case.observed_symptoms}")
                sections.append(f"  Resolution Applied: {case.resolution_applied}")
                sections.append(f"  Lessons Learned: {case.lessons_learned}")
            sections.append("")

        return "\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_anomaly": self.query_anomaly,
            "query_subsystem": self.query_subsystem,
            "disclaimer": self.disclaimer,
            "runbooks": [rb.to_dict() for rb in self.runbooks],
            "historical_cases": [
                {
                    "case_id": hc.case_id,
                    "mission": hc.mission,
                    "subsystem": hc.subsystem,
                    "anomaly_type": hc.anomaly_type,
                    "observed_symptoms": hc.observed_symptoms,
                    "resolution_applied": hc.resolution_applied,
                    "outcome": hc.outcome,
                    "lessons_learned": hc.lessons_learned,
                    "metadata": hc.metadata,
                }
                for hc in self.historical_cases
            ],
            "recommended_actions": self.get_recommended_actions(),
            "diagnostic_checks": self.get_diagnostic_checks(),
        }


class AnomalyKnowledgeRetriever:
    """Retrieves runbooks and historical cases relevant to an anomaly signature."""

    def __init__(
        self,
        runbook_path: Optional[Path] = None,
        incidents_path: Optional[Path] = None,
    ) -> None:
        self.runbook_manager = RunbookManager(data_path=runbook_path)
        self.incidents_path = incidents_path or Path("data/historical/incidents.json")
        self._historical_cases: list[HistoricalCase] = []
        self._load_historical_cases()

    def _load_historical_cases(self) -> None:
        self._historical_cases.clear()
        if self.incidents_path.exists():
            try:
                with open(self.incidents_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self._historical_cases.append(
                            HistoricalCase(
                                case_id=item["case_id"],
                                mission=item["mission"],
                                subsystem=item["subsystem"],
                                anomaly_type=item["anomaly_type"],
                                observed_symptoms=item.get("observed_symptoms", ""),
                                resolution_applied=item.get("resolution_applied", ""),
                                outcome=item.get("outcome", ""),
                                lessons_learned=item.get("lessons_learned", ""),
                                metadata=item.get("metadata", {}),
                            )
                        )
            except Exception:
                pass

    def retrieve(
        self,
        anomaly_type: Optional[str] = None,
        subsystem: Optional[str] = None,
    ) -> RetrievedKnowledge:
        """Retrieve relevant runbooks and historical cases for the given anomaly."""
        if not anomaly_type and not subsystem:
            return RetrievedKnowledge(
                query_anomaly=None,
                query_subsystem=None,
                runbooks=[],
                historical_cases=[],
            )

        matched_runbooks: list[RunbookEntry] = []
        if anomaly_type:
            matched_runbooks = self.runbook_manager.find_by_anomaly(anomaly_type)
        if not matched_runbooks and subsystem:
            matched_runbooks = self.runbook_manager.find_by_subsystem(subsystem)

        matched_cases: list[HistoricalCase] = []
        if anomaly_type:
            target = anomaly_type.strip().lower()
            for hc in self._historical_cases:
                if target == hc.anomaly_type.lower() or target in hc.anomaly_type.lower() or hc.anomaly_type.lower() in target:
                    matched_cases.append(hc)
        elif subsystem:
            target_sub = subsystem.strip().lower()
            for hc in self._historical_cases:
                if target_sub == hc.subsystem.lower():
                    matched_cases.append(hc)

        return RetrievedKnowledge(
            query_anomaly=anomaly_type,
            query_subsystem=subsystem,
            runbooks=matched_runbooks,
            historical_cases=matched_cases,
        )


# Global default retriever instance
_default_retriever: Optional[AnomalyKnowledgeRetriever] = None


def get_retriever() -> AnomalyKnowledgeRetriever:
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = AnomalyKnowledgeRetriever()
    return _default_retriever


def retrieve_anomaly_knowledge(
    anomaly_type: Optional[str] = None,
    subsystem: Optional[str] = None,
) -> RetrievedKnowledge:
    """Convenience functional interface for knowledge retrieval."""
    return get_retriever().retrieve(
        anomaly_type=anomaly_type,
        subsystem=subsystem,
    )
