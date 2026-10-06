import pytest

from agentic_assessment.clause05.aggregation import (
    Clause05AggregationError,
    aggregate_requirement,
)
from agentic_assessment.clause05.config import load_question_bank

TIMESTAMP = "2026-09-29T00:00:00Z"

def rec(qid, outcome):
    return {
        "schema_version": "2.0.0",
        "requirement_assessment_id": "REQ-" + qid,
        "assessment_id": "ASM-C05-TEST",
        "requirement_ref": "5.1",
        "question_id": qid,
        "outcome": outcome,
        "accepted_evidence_acceptance_ids": (
            ["ACC-" + qid] if outcome == "SUPPORTED" else []
        ),
        "rationale": "Governed test assessment.",
        "evaluated_at": TIMESTAMP,
        "evaluator_type": "DETERMINISTIC_RULES",
    }

Q = [
    question["question_id"]
    for question in load_question_bank()["questions"]
    if question["requirement_ref"] == "5.1" and question["mandatory"] is True
]

def test_all_supported_aggregates_supported():
    result = aggregate_requirement(
        assessment_id="ASM-C05-TEST", requirement_ref="5.1",
        question_ids=Q, assessments=[rec(q, "SUPPORTED") for q in reversed(Q)]
    )
    assert result.outcome == "SUPPORTED"

def test_one_unsupported_aggregates_unsupported():
    rows = [rec(q, "SUPPORTED") for q in Q]
    rows[1] = rec(Q[1], "UNSUPPORTED")
    rows[2] = rec(Q[2], "UNRESOLVED")
    assert aggregate_requirement(
        assessment_id="ASM-C05-TEST", requirement_ref="5.1",
        question_ids=Q, assessments=rows
    ).outcome == "UNSUPPORTED"

def test_missing_or_unresolved_fails_closed():
    assert aggregate_requirement(
        assessment_id="ASM-C05-TEST", requirement_ref="5.1",
        question_ids=Q, assessments=[rec(Q[0],"SUPPORTED")]
    ).outcome == "UNRESOLVED"

def test_input_order_does_not_change_identity():
    rows = [rec(q, "SUPPORTED") for q in Q]
    a = aggregate_requirement(assessment_id="ASM-C05-TEST", requirement_ref="5.1", question_ids=Q, assessments=rows)
    b = aggregate_requirement(assessment_id="ASM-C05-TEST", requirement_ref="5.1", question_ids=list(reversed(Q)), assessments=list(reversed(rows)))
    assert a.to_dict() == b.to_dict()


def test_duplicate_expected_question_fails_closed():
    with pytest.raises(Clause05AggregationError, match="Duplicate expected"):
        aggregate_requirement(
            assessment_id="ASM-C05-TEST",
            requirement_ref="5.1",
            question_ids=[Q[0], Q[0]],
            assessments=[rec(Q[0], "SUPPORTED")],
        )


def test_invalid_requirement_assessment_fails_closed():
    invalid = rec(Q[0], "SUPPORTED")
    invalid["accepted_evidence_acceptance_ids"] = []
    with pytest.raises(Clause05AggregationError, match="Invalid requirement"):
        aggregate_requirement(
            assessment_id="ASM-C05-TEST",
            requirement_ref="5.1",
            question_ids=Q,
            assessments=[invalid],
        )


def test_subset_of_configured_mandatory_questions_is_rejected():
    with pytest.raises(Clause05AggregationError, match="complete configured"):
        aggregate_requirement(
            assessment_id="ASM-C05-TEST",
            requirement_ref="5.1",
            question_ids=Q[:1],
            assessments=[rec(Q[0], "SUPPORTED")],
        )


def test_unsupported_precedes_missing_mandatory_question():
    rows = [rec(q, "SUPPORTED") for q in Q[:-1]]
    rows[0] = rec(Q[0], "UNSUPPORTED")
    result = aggregate_requirement(
        assessment_id="ASM-C05-TEST",
        requirement_ref="5.1",
        question_ids=Q,
        assessments=rows,
    )
    assert result.outcome == "UNSUPPORTED"
