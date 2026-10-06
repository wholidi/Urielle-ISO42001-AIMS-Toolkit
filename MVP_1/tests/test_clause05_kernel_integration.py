import pytest

from agentic_assessment.clause05.adapter import (
    build_evidence_mappings,
    evaluate_clause05_question,
)
from agentic_assessment.shared_kernel.lifecycle import lifecycle_id_for
from agentic_assessment.shared_kernel.records import AcceptanceRecord, LifecycleRecord
from agentic_assessment.shared_kernel.validation import SharedKernelError, canonical_identifier

ASSESSMENT_ID = "ASM-C05-TEST"
TIMESTAMP = "2026-09-29T00:00:00Z"
REVIEWER = "HUM-REVIEWER"


def _question_mappings(question_id):
    return [
        mapping
        for mapping in build_evidence_mappings(
            assessment_id=ASSESSMENT_ID,
            created_at=TIMESTAMP,
        )
        if mapping["question_id"] == question_id
    ]


def _lifecycle(mapping, state):
    human = state in {"CONTENT_REVIEWED", "ACCEPTED", "REJECTED"}
    return LifecycleRecord(
        lifecycle_id=lifecycle_id_for(
            assessment_id=ASSESSMENT_ID,
            mapping_id=mapping["mapping_id"],
            evidence_id=mapping["evidence_id"],
        ),
        assessment_id=ASSESSMENT_ID,
        evidence_id=mapping["evidence_id"],
        state=state,
        recorded_at=TIMESTAMP,
        recorded_by=REVIEWER if human else "DET-C05-P04",
        actor_type="HUMAN" if human else "DETERMINISTIC_RULES",
        comments="Human review recorded." if human else None,
    )


def _acceptance(mapping, decision):
    lifecycle = _lifecycle(mapping, decision)
    acceptance = AcceptanceRecord(
        acceptance_id=canonical_identifier(
            "ACC",
            ASSESSMENT_ID,
            mapping["mapping_id"],
            mapping["evidence_id"],
        ),
        assessment_id=ASSESSMENT_ID,
        question_id=mapping["question_id"],
        mapping_id=mapping["mapping_id"],
        evidence_id=mapping["evidence_id"],
        lifecycle_id=lifecycle.lifecycle_id,
        decision=decision,
        reviewer_id=REVIEWER,
        decided_at=TIMESTAMP,
        rationale="Question-specific human review.",
    )
    return lifecycle, acceptance


def test_all_of_requires_every_mapping_to_be_human_accepted():
    mappings = _question_mappings("Q-C05-5.2-003")
    assert len(mappings) == 2
    accepted_lifecycle, accepted = _acceptance(mappings[0], "ACCEPTED")
    unable = _lifecycle(mappings[1], "UNABLE_TO_ESTABLISH")

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.2-003",
        mappings=mappings,
        lifecycles=[accepted_lifecycle, unable],
        acceptances=[accepted],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_all_of_rejected_required_mapping_is_unsupported():
    mappings = _question_mappings("Q-C05-5.2-003")
    accepted_lifecycle, accepted = _acceptance(mappings[0], "ACCEPTED")
    rejected_lifecycle, rejected = _acceptance(mappings[1], "REJECTED")

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.2-003",
        mappings=mappings,
        lifecycles=[accepted_lifecycle, rejected_lifecycle],
        acceptances=[accepted, rejected],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNSUPPORTED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_all_of_is_supported_only_when_every_mapping_is_accepted():
    mappings = _question_mappings("Q-C05-5.2-003")
    pairs = [_acceptance(mapping, "ACCEPTED") for mapping in mappings]

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.2-003",
        mappings=mappings,
        lifecycles=[pair[0] for pair in pairs],
        acceptances=[pair[1] for pair in pairs],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "SUPPORTED"
    assert len(result.accepted_evidence_acceptance_ids) == 2


def test_any_of_accepts_one_human_accepted_mapping_and_fails_closed_on_others():
    mappings = _question_mappings("Q-C05-5.2-008")
    accepted_lifecycle, accepted = _acceptance(mappings[0], "ACCEPTED")
    other_lifecycles = [
        _lifecycle(mapping, "UNABLE_TO_ESTABLISH") for mapping in mappings[1:]
    ]

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.2-008",
        mappings=mappings,
        lifecycles=[accepted_lifecycle, *other_lifecycles],
        acceptances=[accepted],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "SUPPORTED"
    assert result.accepted_evidence_acceptance_ids == (accepted.acceptance_id,)


def test_resource_review_record_is_corroborating_only():
    mappings = _question_mappings("Q-C05-5.1-004")
    assert len(mappings) == 1
    lifecycle, accepted = _acceptance(mappings[0], "ACCEPTED")

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.1-004",
        mappings=mappings,
        lifecycles=[lifecycle],
        acceptances=[accepted],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()
    assert "corroborating only" in result.rationale


def test_reporting_schedule_without_accepted_occurrence_evidence_is_unresolved():
    mappings = _question_mappings("Q-C05-5.3-006")
    assert {mapping["evidence_id"] for mapping in mappings} == {
        "EVD-S5-05",
        "EVD-S5-14",
    }
    schedule = next(
        mapping for mapping in mappings if mapping["evidence_id"] == "EVD-S5-14"
    )
    occurrence = next(
        mapping for mapping in mappings if mapping["evidence_id"] == "EVD-S5-05"
    )
    schedule_lifecycle, schedule_acceptance = _acceptance(schedule, "ACCEPTED")
    occurrence_unreviewed = _lifecycle(occurrence, "UNABLE_TO_ESTABLISH")

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.3-006",
        mappings=mappings,
        lifecycles=[schedule_lifecycle, occurrence_unreviewed],
        acceptances=[schedule_acceptance],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_reporting_occurrence_requires_question_specific_human_acceptance():
    mappings = _question_mappings("Q-C05-5.3-006")
    pairs = [_acceptance(mapping, "ACCEPTED") for mapping in mappings]

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.3-006",
        mappings=mappings,
        lifecycles=[pair[0] for pair in pairs],
        acceptances=[pair[1] for pair in pairs],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "SUPPORTED"
    assert len(result.accepted_evidence_acceptance_ids) == 2


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("question_id", "Q-C05-5.2-001"),
        ("requirement_ref", "5.1"),
        ("evidence_id", "EVD-S5-01"),
    ],
)
def test_runtime_mapping_tuple_must_match_configured_source(field, replacement):
    mappings = _question_mappings("Q-C05-5.2-003")
    target = next(
        mapping for mapping in mappings if mapping["evidence_id"] == "EVD-S5-06"
    )
    target[field] = replacement
    pairs = [_acceptance(mapping, "ACCEPTED") for mapping in mappings]

    with pytest.raises(SharedKernelError, match="runtime mapping"):
        evaluate_clause05_question(
            assessment_id=ASSESSMENT_ID,
            question_id="Q-C05-5.2-003",
            mappings=mappings,
            lifecycles=[pair[0] for pair in pairs],
            acceptances=[pair[1] for pair in pairs],
            evaluated_at=TIMESTAMP,
        )


def test_non_human_acceptance_cannot_support_clause05():
    mappings = _question_mappings("Q-C05-5.2-001")
    lifecycle, accepted = _acceptance(mappings[0], "ACCEPTED")
    invalid = accepted.to_contract()
    invalid["decision_maker_type"] = "DETERMINISTIC_RULES"

    with pytest.raises(SharedKernelError):
        evaluate_clause05_question(
            assessment_id=ASSESSMENT_ID,
            question_id="Q-C05-5.2-001",
            mappings=mappings,
            lifecycles=[lifecycle],
            acceptances=[invalid],
            evaluated_at=TIMESTAMP,
        )


def test_unconfigured_mapping_fails_closed():
    mappings = _question_mappings("Q-C05-5.2-001")
    extra = dict(mappings[0])
    extra["mapping_id"] = canonical_identifier("MAP", "UNCONFIGURED", ASSESSMENT_ID)

    with pytest.raises(SharedKernelError):
        evaluate_clause05_question(
            assessment_id=ASSESSMENT_ID,
            question_id="Q-C05-5.2-001",
            mappings=[*mappings, extra],
            lifecycles=[],
            acceptances=[],
            evaluated_at=TIMESTAMP,
        )
