"""Phase 03 report-state boundary tests."""

from __future__ import annotations

from agentic_assessment.shared_kernel.findings import derive_findings
from agentic_assessment.shared_kernel.report_state import derive_report_state
from agentic_assessment.shared_kernel.requirements import evaluate_requirement
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    QUESTION_ID,
    REQUIREMENT_REF,
    TIMESTAMP,
    accepted_records,
    mapping,
)


def _requirement(*, supported: bool):
    if supported:
        lifecycle, acceptance = accepted_records()
        return evaluate_requirement(
            assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
            question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[lifecycle],
            acceptances=[acceptance], evaluated_at=TIMESTAMP
        )
    return evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[],
        acceptances=[], evaluated_at=TIMESTAMP
    )


def test_pending_findings_block_final_report_state() -> None:
    requirement = _requirement(supported=False)
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=derive_findings([requirement]),
        requirement_assessments=[requirement], recorded_at=TIMESTAMP
    )
    assert report.status == "DRAFT"
    assert report.pending_finding_ids


def test_unresolved_requirements_block_final_report_state() -> None:
    requirement = _requirement(supported=False)
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=[],
        requirement_assessments=[requirement], recorded_at=TIMESTAMP
    )
    assert report.status == "DRAFT"
    assert report.unresolved_requirement_assessment_ids == (
        requirement.requirement_assessment_id,
    )


def test_final_requires_no_pending_or_unresolved_records() -> None:
    requirement = _requirement(supported=True)
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=[],
        requirement_assessments=[requirement], recorded_at=TIMESTAMP
    )
    assert report.status == "FINAL"
    assert report.pending_finding_ids == ()
    assert report.unresolved_requirement_assessment_ids == ()


def test_final_conclusion_is_workflow_state_only() -> None:
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=[],
        requirement_assessments=[_requirement(supported=True)], recorded_at=TIMESTAMP
    )
    assert report.conclusion_type == "WORKFLOW_STATE_ONLY"
    assert "certif" not in report.to_contract()


def test_unsupported_requirement_without_finding_blocks_final() -> None:
    from agentic_assessment.shared_kernel.acceptance import record_acceptance
    from tests._shared_kernel_fixtures import reviewed_lifecycle

    lifecycle, acceptance = record_acceptance(
        mapping=mapping(), lifecycle=reviewed_lifecycle(), decision="REJECTED",
        reviewer_id="HUM-REVIEWER-001", decided_at=TIMESTAMP,
        rationale="Evidence does not support the question."
    )
    requirement = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[lifecycle],
        acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=[],
        requirement_assessments=[requirement], recorded_at=TIMESTAMP
    )
    assert requirement.outcome == "UNSUPPORTED"
    assert report.status == "DRAFT"
    assert report.unresolved_requirement_assessment_ids == (
        requirement.requirement_assessment_id,
    )
