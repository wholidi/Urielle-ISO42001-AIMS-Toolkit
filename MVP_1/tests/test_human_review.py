"""Tests for governed Agentic Clause 04 human review."""

from __future__ import annotations

import pytest

from agentic_assessment.evidence_assessor import (
    EvidenceDecision,
)
from agentic_assessment.finding_generator import (
    Finding,
    FindingGenerator,
)
from agentic_assessment.human_review import (
    HumanReviewError,
    HumanReviewService,
)


def build_pending_finding() -> Finding:
    decision = EvidenceDecision(
        schema_version="1.0.0",
        decision_id="ED-CLAUSE04-001-001",
        assessment_id="CLAUSE04-001",
        question_id="C4-Q01",
        evidence_ids=(),
        deterministic_checks=(
            {
                "check_id": "CHK-C4-Q01-MAP",
                "check_type": "QUESTION_MAPPING_VALID",
                "status": "PASSED",
                "observation": (
                    "Evidence record is mapped to C4-Q01."
                ),
            },
        ),
        semantic_observations=(),
        decision="NOT_EVIDENCED",
        confidence=1.0,
        human_review_required=False,
        provenance={
            "created_at": "2026-07-12T14:47:40+00:00",
            "created_by": "agentic.evidence_assessor",
            "generator": "DETERMINISTIC_RULES",
            "generator_version": "0.1.0",
            "source_refs": [
                "assessment:CLAUSE04-001",
                "question:C4-Q01",
            ],
        },
    )

    generator = FindingGenerator()

    return generator.generate(
        decisions=(decision,)
    )[0]


def test_accept_pending_finding() -> None:
    service = HumanReviewService()

    reviewed = service.review(
        finding=build_pending_finding(),
        reviewer_id="reviewer-001",
        disposition="ACCEPTED",
    )

    assert reviewed.human_disposition == "ACCEPTED"
    assert reviewed.review_record is not None

    assert (
        reviewed.review_record["reviewer_id"]
        == "reviewer-001"
    )

    assert (
        reviewed.review_record["disposition"]
        == "ACCEPTED"
    )


def test_modified_requires_comments() -> None:
    service = HumanReviewService()

    with pytest.raises(
        HumanReviewError,
        match="MODIFIED review requires comments",
    ):
        service.review(
            finding=build_pending_finding(),
            reviewer_id="reviewer-002",
            disposition="MODIFIED",
        )


def test_rejected_requires_comments() -> None:
    service = HumanReviewService()

    with pytest.raises(
        HumanReviewError,
        match="REJECTED review requires comments",
    ):
        service.review(
            finding=build_pending_finding(),
            reviewer_id="reviewer-003",
            disposition="REJECTED",
        )


def test_modified_with_comments_is_valid() -> None:
    service = HumanReviewService()

    reviewed = service.review(
        finding=build_pending_finding(),
        reviewer_id="reviewer-004",
        disposition="MODIFIED",
        comments="Finding wording requires revision.",
    )

    assert reviewed.human_disposition == "MODIFIED"

    assert (
        reviewed.review_record["comments"]
        == "Finding wording requires revision."
    )


def test_rejected_with_comments_is_valid() -> None:
    service = HumanReviewService()

    reviewed = service.review(
        finding=build_pending_finding(),
        reviewer_id="reviewer-005",
        disposition="REJECTED",
        comments="Evidence does not support this finding.",
    )

    assert reviewed.human_disposition == "REJECTED"


def test_invalid_reviewer_id_fails_closed() -> None:
    service = HumanReviewService()

    with pytest.raises(
        HumanReviewError,
        match="reviewer_id is missing or invalid",
    ):
        service.review(
            finding=build_pending_finding(),
            reviewer_id="",
            disposition="ACCEPTED",
        )


def test_pending_is_not_valid_review_disposition() -> None:
    service = HumanReviewService()

    with pytest.raises(
        HumanReviewError,
        match="disposition is invalid",
    ):
        service.review(
            finding=build_pending_finding(),
            reviewer_id="reviewer-006",
            disposition="PENDING",
        )


def test_reviewed_finding_satisfies_phase1_contract() -> None:
    service = HumanReviewService()

    reviewed = service.review(
        finding=build_pending_finding(),
        reviewer_id="reviewer-007",
        disposition="ACCEPTED",
    )

    service.contract_validator.require_valid(
        contract_name="finding",
        instance=reviewed.to_contract(),
    )


def test_cannot_review_finding_twice() -> None:
    service = HumanReviewService()

    reviewed = service.review(
        finding=build_pending_finding(),
        reviewer_id="reviewer-008",
        disposition="ACCEPTED",
    )

    with pytest.raises(
        HumanReviewError,
        match="already been reviewed",
    ):
        service.review(
            finding=reviewed,
            reviewer_id="reviewer-009",
            disposition="REJECTED",
            comments="Attempted second review.",
        )


def test_review_preserves_finding_identity() -> None:
    service = HumanReviewService()

    finding = build_pending_finding()

    reviewed = service.review(
        finding=finding,
        reviewer_id="reviewer-010",
        disposition="ACCEPTED",
    )

    assert reviewed.finding_id == finding.finding_id
    assert reviewed.assessment_id == finding.assessment_id
    assert reviewed.question_id == finding.question_id
    assert reviewed.requirement_ref == finding.requirement_ref


def test_review_preserves_finding_provenance() -> None:
    service = HumanReviewService()

    finding = build_pending_finding()

    reviewed = service.review(
        finding=finding,
        reviewer_id="reviewer-011",
        disposition="ACCEPTED",
    )

    assert reviewed.provenance == finding.provenance


def test_original_finding_remains_pending() -> None:
    service = HumanReviewService()

    finding = build_pending_finding()

    reviewed = service.review(
        finding=finding,
        reviewer_id="reviewer-012",
        disposition="ACCEPTED",
    )

    assert finding.human_disposition == "PENDING"
    assert finding.review_record is None
    assert reviewed.human_disposition == "ACCEPTED"