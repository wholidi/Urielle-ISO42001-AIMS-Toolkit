"""Phase 03 deterministic finding tests."""

from __future__ import annotations

from agentic_assessment.shared_kernel.findings import derive_findings
from agentic_assessment.shared_kernel.requirements import evaluate_requirement
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    QUESTION_ID,
    REQUIREMENT_REF,
    TIMESTAMP,
    mapping,
)


def _unresolved(question_id=QUESTION_ID, requirement_ref=REQUIREMENT_REF):
    return evaluate_requirement(
        assessment_id=ASSESSMENT_ID,
        requirement_ref=requirement_ref,
        question_id=question_id,
        mappings=[mapping(question_id=question_id, requirement_ref=requirement_ref)],
        lifecycles=[],
        acceptances=[],
        evaluated_at=TIMESTAMP,
    )


def test_finding_ids_and_order_are_stable() -> None:
    first_requirement = _unresolved("Q-CONTROL-002", "1.2")
    second_requirement = _unresolved("Q-CONTROL-001", "1.1")
    first = derive_findings([first_requirement, second_requirement])
    second = derive_findings([second_requirement, first_requirement])
    assert first == second
    assert [item.question_id for item in first] == ["Q-CONTROL-001", "Q-CONTROL-002"]
    assert all(item.finding_id.startswith("FND-") for item in first)


def test_repeated_evaluation_does_not_duplicate_findings() -> None:
    requirement = _unresolved()
    first = derive_findings([requirement])
    second = derive_findings([requirement, requirement], existing_findings=first)
    assert second == first


def test_evidence_acceptance_does_not_dispose_finding() -> None:
    finding = derive_findings([_unresolved()])[0]
    assert finding.status == "DRAFT"
    assert finding.disposition == "PENDING"
    assert finding.reviewer_id is None


def test_supported_requirement_creates_no_finding() -> None:
    from tests._shared_kernel_fixtures import accepted_records

    terminal, acceptance = accepted_records()
    supported = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[terminal],
        acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    assert derive_findings([supported]) == ()
