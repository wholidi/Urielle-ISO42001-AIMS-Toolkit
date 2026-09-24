"""Immutable values that serialize exactly to the frozen v2 contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LifecycleRecord:
    lifecycle_id: str
    assessment_id: str
    evidence_id: str
    state: str
    recorded_at: str
    recorded_by: str
    actor_type: str
    sha256: str | None = None
    comments: str | None = None
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "lifecycle_id": self.lifecycle_id,
            "assessment_id": self.assessment_id,
            "evidence_id": self.evidence_id,
            "state": self.state,
            "recorded_at": self.recorded_at,
            "recorded_by": self.recorded_by,
            "actor_type": self.actor_type,
        }
        if self.sha256 is not None:
            value["sha256"] = self.sha256
        if self.comments is not None:
            value["comments"] = self.comments
        return value


@dataclass(frozen=True)
class AcceptanceRecord:
    acceptance_id: str
    assessment_id: str
    question_id: str
    mapping_id: str
    evidence_id: str
    lifecycle_id: str
    decision: str
    reviewer_id: str
    decided_at: str
    rationale: str
    decision_maker_type: str = "HUMAN"
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "acceptance_id": self.acceptance_id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "mapping_id": self.mapping_id,
            "evidence_id": self.evidence_id,
            "lifecycle_id": self.lifecycle_id,
            "decision": self.decision,
            "decision_maker_type": self.decision_maker_type,
            "reviewer_id": self.reviewer_id,
            "decided_at": self.decided_at,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class RequirementAssessment:
    requirement_assessment_id: str
    assessment_id: str
    requirement_ref: str
    question_id: str
    outcome: str
    accepted_evidence_acceptance_ids: tuple[str, ...]
    rationale: str
    evaluated_at: str
    evaluator_type: str = "DETERMINISTIC_RULES"
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requirement_assessment_id": self.requirement_assessment_id,
            "assessment_id": self.assessment_id,
            "requirement_ref": self.requirement_ref,
            "question_id": self.question_id,
            "outcome": self.outcome,
            "accepted_evidence_acceptance_ids": list(
                self.accepted_evidence_acceptance_ids
            ),
            "rationale": self.rationale,
            "evaluated_at": self.evaluated_at,
            "evaluator_type": self.evaluator_type,
        }


@dataclass(frozen=True)
class FindingRecord:
    finding_id: str
    assessment_id: str
    requirement_assessment_id: str
    question_id: str
    status: str
    disposition: str
    condition: str
    criteria: str
    created_at: str
    reviewer_id: str | None = None
    reviewed_at: str | None = None
    review_comments: str | None = None
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "finding_id": self.finding_id,
            "assessment_id": self.assessment_id,
            "requirement_assessment_id": self.requirement_assessment_id,
            "question_id": self.question_id,
            "status": self.status,
            "disposition": self.disposition,
            "condition": self.condition,
            "criteria": self.criteria,
            "created_at": self.created_at,
        }
        if self.reviewer_id is not None:
            value["reviewer_id"] = self.reviewer_id
        if self.reviewed_at is not None:
            value["reviewed_at"] = self.reviewed_at
        if self.review_comments is not None:
            value["review_comments"] = self.review_comments
        return value


@dataclass(frozen=True)
class ReportState:
    report_id: str
    assessment_id: str
    status: str
    pending_finding_ids: tuple[str, ...]
    unresolved_requirement_assessment_ids: tuple[str, ...]
    recorded_at: str
    conclusion_type: str = "WORKFLOW_STATE_ONLY"
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "assessment_id": self.assessment_id,
            "status": self.status,
            "pending_finding_ids": list(self.pending_finding_ids),
            "unresolved_requirement_assessment_ids": list(
                self.unresolved_requirement_assessment_ids
            ),
            "conclusion_type": self.conclusion_type,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True)
class ExecutionEvent:
    event_id: str
    assessment_id: str
    sequence: int
    component_id: str
    event_type: str
    status: str
    occurred_at: str
    subject_id: str | None = None
    schema_version: str = "2.0.0"

    def to_contract(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "assessment_id": self.assessment_id,
            "sequence": self.sequence,
            "component_id": self.component_id,
            "event_type": self.event_type,
            "status": self.status,
            "occurred_at": self.occurred_at,
        }
        if self.subject_id is not None:
            value["subject_id"] = self.subject_id
        return value
