"""Tests for deterministic Agentic Clause 04 evidence assessment."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from agentic_assessment.clause04_adapter import (
    Clause04AssessmentResult,
)
from agentic_assessment.evidence_assessor import (
    EvidenceAssessor,
    EvidenceAssessorError,
)


def build_record(
    *,
    question_id: str = "C4-Q01",
    confidence_score: float = 1.0,
    auditor_flag: bool = False,
    references: list[Mapping[str, Any]] | None = None,
    auditor_note: str = "Initial evidence appears available.",
) -> Mapping[str, Any]:
    if references is None:
        references = [
            {
                "reference_type": "file_reference",
                "reference_name": "Clause4_Context_Register.xlsx",
                "extracted_from": "human_response",
            }
        ]

    return {
        "session_id": "CLAUSE4-TEST-001",
        "question_id": question_id,
        "clause": "4.1",
        "title": "Context of the organization",
        "question": "Test question",
        "expected_evidence": [
            "context register",
        ],
        "response": "Evidence provided.",
        "response_source_type": "human_file",
        "actual_evidence_references": references,
        "confidence_score": confidence_score,
        "confidence_type": "rule_based_response_quality",
        "auditor_note": auditor_note,
        "auditor_flag": auditor_flag,
        "timestamp": "2026-07-12T14:47:40+00:00",
    }


def build_result(
    record: Mapping[str, Any],
) -> Clause04AssessmentResult:
    return Clause04AssessmentResult(
        assessment_id="CLAUSE04-001",
        session_id="CLAUSE4-TEST-001",
        status="COMPLETED",
        score=100.0,
        evidence_records=(record,),
        gaps=(),
        source_result={},
    )


def test_evidenced_record_produces_evidenced_decision() -> None:
    assessor = EvidenceAssessor()

    decisions = assessor.assess(
        clause04_result=build_result(
            build_record()
        )
    )

    assert len(decisions) == 1

    decision = decisions[0]

    assert decision.question_id == "C4-Q01"
    assert decision.decision == "EVIDENCED"
    assert decision.human_review_required is False
    assert decision.confidence == 1.0

    assert decision.evidence_ids == (
        "Clause4_Context_Register.xlsx",
    )


def test_decision_satisfies_phase1_contract() -> None:
    assessor = EvidenceAssessor()

    decision = assessor.assess(
        clause04_result=build_result(
            build_record()
        )
    )[0]

    assessor.contract_validator.require_valid(
        contract_name="evidence_decision",
        instance=decision.to_contract(),
    )


def test_missing_evidence_is_not_evidenced() -> None:
    assessor = EvidenceAssessor()

    record = build_record(
        references=[],
    )

    decision = assessor.assess(
        clause04_result=build_result(record)
    )[0]

    assert decision.decision == "NOT_EVIDENCED"
    assert decision.evidence_ids == ()
    assert decision.human_review_required is False


def test_partial_confidence_requires_human_review() -> None:
    assessor = EvidenceAssessor()

    record = build_record(
        confidence_score=0.75,
    )

    decision = assessor.assess(
        clause04_result=build_result(record)
    )[0]

    assert (
        decision.decision
        == "PARTIALLY_EVIDENCED"
    )

    assert decision.human_review_required is True
    assert decision.semantic_observations


def test_auditor_flag_requires_human_judgement() -> None:
    assessor = EvidenceAssessor()

    record = build_record(
        auditor_flag=True,
        auditor_note=(
            "Evidence requires auditor review."
        ),
    )

    decision = assessor.assess(
        clause04_result=build_result(record)
    )[0]

    assert (
        decision.decision
        == "REQUIRES_HUMAN_JUDGEMENT"
    )

    assert decision.human_review_required is True

    assert (
        decision.semantic_observations[0][
            "observation"
        ]
        == "Evidence requires auditor review."
    )


def test_source_evidence_is_not_modified() -> None:
    assessor = EvidenceAssessor()

    record = dict(build_record())

    original = dict(record)

    assessor.assess(
        clause04_result=build_result(record)
    )

    assert record == original


def test_missing_question_id_fails_closed() -> None:
    assessor = EvidenceAssessor()

    record = dict(build_record())
    record.pop("question_id")

    with pytest.raises(
        EvidenceAssessorError,
        match="question_id is missing or invalid",
    ):
        assessor.assess(
            clause04_result=build_result(record)
        )


def test_invalid_confidence_fails_closed() -> None:
    assessor = EvidenceAssessor()

    record = dict(build_record())
    record["confidence_score"] = 2.0

    with pytest.raises(
        EvidenceAssessorError,
        match="between 0 and 1",
    ):
        assessor.assess(
            clause04_result=build_result(record)
        )


def test_invalid_auditor_flag_fails_closed() -> None:
    assessor = EvidenceAssessor()

    record = dict(build_record())
    record["auditor_flag"] = "false"

    with pytest.raises(
        EvidenceAssessorError,
        match="invalid auditor_flag",
    ):
        assessor.assess(
            clause04_result=build_result(record)
        )


def test_invalid_evidence_reference_fails_closed() -> None:
    assessor = EvidenceAssessor()

    record = build_record(
        references=[
            {
                "reference_type": "file_reference",
            }
        ],
    )

    with pytest.raises(
        EvidenceAssessorError,
        match="missing reference_name",
    ):
        assessor.assess(
            clause04_result=build_result(record)
        )


def test_decision_ids_are_deterministic() -> None:
    assessor = EvidenceAssessor()

    result = build_result(
        build_record()
    )

    first = assessor.assess(
        clause04_result=result
    )

    second = assessor.assess(
        clause04_result=result
    )

    assert (
        first[0].decision_id
        == second[0].decision_id
        == "ED-CLAUSE04-001-001"
    )


def test_multiple_records_preserve_order() -> None:
    assessor = EvidenceAssessor()

    result = Clause04AssessmentResult(
        assessment_id="CLAUSE04-002",
        session_id="CLAUSE4-TEST-002",
        status="COMPLETED",
        score=100.0,
        evidence_records=(
            build_record(
                question_id="C4-Q01"
            ),
            build_record(
                question_id="C4-Q02"
            ),
        ),
        gaps=(),
        source_result={},
    )

    decisions = assessor.assess(
        clause04_result=result
    )

    assert [
        decision.question_id
        for decision in decisions
    ] == [
        "C4-Q01",
        "C4-Q02",
    ]