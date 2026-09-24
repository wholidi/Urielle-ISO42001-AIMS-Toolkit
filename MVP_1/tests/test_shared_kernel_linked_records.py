"""Phase 03 linked-record and requirement-evaluation tests."""

from __future__ import annotations

import pytest

from agentic_assessment.shared_kernel.requirements import evaluate_requirement
from agentic_assessment.shared_kernel.validation import SharedKernelError, validate_linked_records
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    QUESTION_ID,
    REQUIREMENT_REF,
    TIMESTAMP,
    accepted_records,
    manifest,
    mapping,
    plan,
    reviewed_lifecycle,
)


def _validated():
    terminal, acceptance = accepted_records()
    validate_linked_records(
        plan=plan(), manifest=manifest(), mappings=[mapping()],
        lifecycles=[terminal], acceptances=[acceptance]
    )
    return terminal, acceptance


def test_valid_linked_records_produce_supported_requirement() -> None:
    terminal, acceptance = _validated()
    result = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[terminal],
        acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    assert result.outcome == "SUPPORTED"
    assert result.accepted_evidence_acceptance_ids == (acceptance.acceptance_id,)


def test_missing_linked_reference_fails_closed() -> None:
    terminal, acceptance = accepted_records()
    with pytest.raises(SharedKernelError, match="missing linked record"):
        validate_linked_records(
            plan=plan(), manifest=manifest(), mappings=[mapping()],
            lifecycles=[], acceptances=[acceptance]
        )


def test_mismatched_assessment_ids_fail_closed() -> None:
    with pytest.raises(SharedKernelError, match="Manifest assessment_id"):
        validate_linked_records(
            plan=plan(), manifest=manifest(assessment_id="ASM-PHASE03-002"),
            mappings=[], lifecycles=[], acceptances=[]
        )


def test_mismatched_question_ids_fail_closed() -> None:
    with pytest.raises(SharedKernelError, match="question_id"):
        validate_linked_records(
            plan=plan(), manifest=manifest(),
            mappings=[mapping(question_id="Q-CONTROL-002")],
            lifecycles=[], acceptances=[]
        )


@pytest.mark.parametrize("field", ["mapping_id", "evidence_id", "lifecycle_id"])
def test_mismatched_mapping_evidence_or_lifecycle_ids_fail_closed(field: str) -> None:
    terminal, acceptance = accepted_records()
    invalid = acceptance.to_contract()
    invalid[field] = {
        "mapping_id": "MAP-CONTROL-999",
        "evidence_id": "EVD-CONTROL-999",
        "lifecycle_id": "LCR-" + "F" * 64,
    }[field]
    with pytest.raises(SharedKernelError):
        validate_linked_records(
            plan=plan(), manifest=manifest(), mappings=[mapping()],
            lifecycles=[terminal], acceptances=[invalid]
        )


def test_acceptance_cannot_be_reused_for_another_question() -> None:
    terminal, acceptance = accepted_records()
    other_mapping = mapping(
        mapping_id="MAP-CONTROL-002",
        question_id="Q-CONTROL-002",
        requirement_ref="1.2",
    )
    result = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref="1.2",
        question_id="Q-CONTROL-002", mappings=[mapping(), other_mapping],
        lifecycles=[terminal], acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_matching_hash_without_human_acceptance_cannot_support_requirement() -> None:
    result = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()],
        lifecycles=[reviewed_lifecycle()], acceptances=[], evaluated_at=TIMESTAMP
    )
    assert result.outcome == "UNRESOLVED"


def test_rejected_acceptance_produces_no_support() -> None:
    from agentic_assessment.shared_kernel.acceptance import record_acceptance

    terminal, acceptance = record_acceptance(
        mapping=mapping(), lifecycle=reviewed_lifecycle(), decision="REJECTED",
        reviewer_id="HUM-REVIEWER-001", decided_at=TIMESTAMP,
        rationale="The reviewed content does not support the question."
    )
    result = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[terminal],
        acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    assert result.outcome == "UNSUPPORTED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_incomplete_lifecycle_produces_no_support() -> None:
    result = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()],
        lifecycles=[reviewed_lifecycle()], acceptances=[], evaluated_at=TIMESTAMP
    )
    assert result.outcome == "UNRESOLVED"
