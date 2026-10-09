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
        rationale="Synthetic test fixture: question-specific human review.",
    )
    return lifecycle, acceptance


def _evaluate_reporting(accepted_evidence_ids=(), *, reverse=False):
    mappings = _question_mappings("Q-C05-5.3-006")
    lifecycles = []
    acceptances = []
    for mapping in mappings:
        if mapping["evidence_id"] in accepted_evidence_ids:
            lifecycle, acceptance = _acceptance(mapping, "ACCEPTED")
            lifecycles.append(lifecycle)
            acceptances.append(acceptance)
        else:
            lifecycles.append(_lifecycle(mapping, "UNABLE_TO_ESTABLISH"))
    if reverse:
        mappings.reverse()
        lifecycles.reverse()
        acceptances.reverse()
    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.3-006",
        mappings=mappings,
        lifecycles=lifecycles,
        acceptances=acceptances,
        evaluated_at=TIMESTAMP,
    )
    return result


def _evaluate_resource_decision(
    accepted_evidence_ids=(),
    *,
    rejected_evidence_ids=(),
    include_other_question_acceptance=False,
    reverse=False,
):
    mappings = _question_mappings("Q-C05-5.1-004")
    lifecycles = []
    acceptances = []
    for mapping in mappings:
        if mapping["evidence_id"] in accepted_evidence_ids:
            lifecycle, acceptance = _acceptance(mapping, "ACCEPTED")
            acceptances.append(acceptance)
        elif mapping["evidence_id"] in rejected_evidence_ids:
            lifecycle, acceptance = _acceptance(mapping, "REJECTED")
            acceptances.append(acceptance)
        else:
            lifecycle = _lifecycle(mapping, "UNABLE_TO_ESTABLISH")
        lifecycles.append(lifecycle)

    if include_other_question_acceptance:
        other_mapping = next(
            mapping
            for mapping in _question_mappings("Q-C05-5.1-003")
            if mapping["evidence_id"] == "EVD-S5-05"
        )
        other_lifecycle, other_acceptance = _acceptance(other_mapping, "ACCEPTED")
        mappings.append(other_mapping)
        lifecycles.append(other_lifecycle)
        acceptances.append(other_acceptance)

    if reverse:
        mappings.reverse()
        lifecycles.reverse()
        acceptances.reverse()

    return evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.1-004",
        mappings=mappings,
        lifecycles=lifecycles,
        acceptances=acceptances,
        evaluated_at=TIMESTAMP,
    )


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


@pytest.mark.parametrize(
    "accepted_evidence_ids",
    [{"EVD-S5-05"}, {"EVD-S5-15"}],
)
def test_resource_decision_requires_both_sources(accepted_evidence_ids):
    mappings = _question_mappings("Q-C05-5.1-004")
    assert {mapping["evidence_id"] for mapping in mappings} == {
        "EVD-S5-05",
        "EVD-S5-15",
    }
    result = _evaluate_resource_decision(accepted_evidence_ids)
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_resource_decision_presence_without_acceptance_is_unresolved():
    result = _evaluate_resource_decision()
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_resource_decision_acceptance_for_another_question_is_unresolved():
    result = _evaluate_resource_decision(include_other_question_acceptance=True)
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_resource_decision_requires_question_specific_acceptance_of_both_sources():
    result = _evaluate_resource_decision({"EVD-S5-05", "EVD-S5-15"})
    assert result.outcome == "SUPPORTED"
    assert len(result.accepted_evidence_acceptance_ids) == 2


@pytest.mark.parametrize("rejected_evidence_id", ["EVD-S5-05", "EVD-S5-15"])
def test_rejected_required_resource_evidence_is_unsupported(rejected_evidence_id):
    other = {"EVD-S5-05", "EVD-S5-15"} - {rejected_evidence_id}
    result = _evaluate_resource_decision(
        other,
        rejected_evidence_ids={rejected_evidence_id},
    )
    assert result.outcome == "UNSUPPORTED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_resource_decision_combination_is_input_order_independent():
    accepted = {"EVD-S5-05", "EVD-S5-15"}
    forward = _evaluate_resource_decision(accepted)
    reversed_result = _evaluate_resource_decision(accepted, reverse=True)
    assert reversed_result == forward


@pytest.mark.parametrize(
    "accepted_evidence_ids",
    [
        {"EVD-S5-14"},
        {"EVD-S5-05", "EVD-S5-14"},
        {"EVD-S5-11", "EVD-S5-14"},
    ],
)
def test_incomplete_reporting_combination_is_unresolved(accepted_evidence_ids):
    mappings = _question_mappings("Q-C05-5.3-006")
    assert {mapping["evidence_id"] for mapping in mappings} == {
        "EVD-S5-05",
        "EVD-S5-11",
        "EVD-S5-14",
    }
    result = _evaluate_reporting(accepted_evidence_ids)
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_reporting_occurrence_requires_question_specific_human_acceptance():
    result = _evaluate_reporting(
        {"EVD-S5-05", "EVD-S5-11", "EVD-S5-14"}
    )
    assert result.outcome == "SUPPORTED"
    assert len(result.accepted_evidence_acceptance_ids) == 3


def test_reporting_file_presence_without_acceptance_is_unresolved():
    mappings = _question_mappings("Q-C05-5.3-006")
    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.3-006",
        mappings=mappings,
        lifecycles=[],
        acceptances=[],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNRESOLVED"


def test_reporting_acceptance_for_another_question_cannot_contribute():
    reporting_mappings = _question_mappings("Q-C05-5.3-006")
    other_mapping = next(
        mapping
        for mapping in _question_mappings("Q-C05-5.3-005")
        if mapping["evidence_id"] == "EVD-S5-11"
    )
    other_lifecycle, other_acceptance = _acceptance(other_mapping, "ACCEPTED")

    result = evaluate_clause05_question(
        assessment_id=ASSESSMENT_ID,
        question_id="Q-C05-5.3-006",
        mappings=[*reporting_mappings, other_mapping],
        lifecycles=[
            *[
                _lifecycle(mapping, "UNABLE_TO_ESTABLISH")
                for mapping in reporting_mappings
            ],
            other_lifecycle,
        ],
        acceptances=[other_acceptance],
        evaluated_at=TIMESTAMP,
    )
    assert result.outcome == "UNRESOLVED"
    assert result.accepted_evidence_acceptance_ids == ()


def test_reporting_combination_is_input_order_independent():
    accepted = {"EVD-S5-05", "EVD-S5-11", "EVD-S5-14"}
    forward = _evaluate_reporting(accepted)
    reversed_result = _evaluate_reporting(accepted, reverse=True)
    assert reversed_result == forward


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
