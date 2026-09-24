"""Phase 03 human acceptance boundary tests."""

from __future__ import annotations

import pytest

from agentic_assessment.shared_kernel.acceptance import record_acceptance
from agentic_assessment.shared_kernel.validation import SharedKernelError, require_contract
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    EVIDENCE_ID,
    MAPPING_ID,
    QUESTION_ID,
    TIMESTAMP,
    accepted_records,
    mapping,
    reviewed_lifecycle,
)


def test_human_acceptance_is_question_mapping_and_lifecycle_specific() -> None:
    terminal, acceptance = accepted_records()
    assert terminal.state == "ACCEPTED"
    assert acceptance.question_id == QUESTION_ID
    assert acceptance.mapping_id == MAPPING_ID
    assert acceptance.evidence_id == EVIDENCE_ID
    assert acceptance.lifecycle_id == terminal.lifecycle_id
    assert acceptance.decision_maker_type == "HUMAN"


def test_acceptance_requires_content_reviewed_lifecycle() -> None:
    reviewed = reviewed_lifecycle()
    incomplete = reviewed.to_contract()
    incomplete["state"] = "INTEGRITY_VERIFIED"
    incomplete["actor_type"] = "DETERMINISTIC_RULES"
    incomplete.pop("comments")
    with pytest.raises(SharedKernelError, match="CONTENT_REVIEWED"):
        record_acceptance(
            mapping=mapping(), lifecycle=incomplete, decision="ACCEPTED",
            reviewer_id="HUM-REVIEWER-001", decided_at=TIMESTAMP,
            rationale="Attempted hash-only acceptance."
        )


@pytest.mark.parametrize("actor", ["DETERMINISTIC_RULES", "LLM", "EXTERNAL_MODEL"])
def test_non_human_acceptance_actor_fails_closed(actor: str) -> None:
    _, acceptance = accepted_records()
    invalid = acceptance.to_contract()
    invalid["decision_maker_type"] = actor
    with pytest.raises(SharedKernelError, match="contract validation"):
        require_contract("evidence_acceptance_record", invalid)


def test_mapping_lifecycle_identity_mismatch_fails_closed() -> None:
    different = mapping(
        mapping_id="MAP-CONTROL-002",
        evidence_id="EVD-CONTROL-002",
    )
    with pytest.raises(SharedKernelError, match="evidence IDs do not match"):
        record_acceptance(
            mapping=different, lifecycle=reviewed_lifecycle(), decision="ACCEPTED",
            reviewer_id="HUM-REVIEWER-001", decided_at=TIMESTAMP,
            rationale="Invalid linkage."
        )


def test_acceptance_identity_is_deterministic() -> None:
    first = accepted_records()[1]
    second = accepted_records()[1]
    assert first == second
    assert first.acceptance_id == second.acceptance_id
    assert first.assessment_id == ASSESSMENT_ID
