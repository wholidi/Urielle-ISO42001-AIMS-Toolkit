from clause_04_context.fabric.gap_detector import (
    calculate_readiness,
    detect_coverage_gaps,
    detect_evidence_gaps,
    detect_gaps,
)


def question(question_id, clause):
    return {
        "question_id": question_id,
        "clause": clause,
        "title": f"Question {question_id}",
    }


def response(question_id):
    return {
        "question_id": question_id,
        "response": "Sample response",
        "auditor_note": "Sample note",
    }


def evidence_record(question_id, clause, score, expected_evidence=None, actual_refs=None):
    return {
        "question_id": question_id,
        "clause": clause,
        "title": f"Question {question_id}",
        "confidence_score": score,
        "expected_evidence": expected_evidence or [],
        "actual_evidence_references": actual_refs or [],
    }


def complete_questions():
    return [
        question("C4-Q01", "4.1"),
        question("C4-Q02", "4.2"),
        question("C4-Q03", "4.3"),
        question("C4-Q04", "4.4"),
    ]


def complete_responses():
    return [
        response("C4-Q01"),
        response("C4-Q02"),
        response("C4-Q03"),
        response("C4-Q04"),
    ]


def complete_evidence_records(score=1.0):
    ref = [{"reference_type": "file_reference", "reference_name": "x.xlsx"}]
    return [
        evidence_record("C4-Q01", "4.1", score, ["context register"], ref),
        evidence_record("C4-Q02", "4.2", score, ["stakeholder register"], ref),
        evidence_record("C4-Q03", "4.3", score, ["scope statement"], ref),
        evidence_record("C4-Q04", "4.4", score, ["process map"], ref),
    ]


def test_detect_evidence_gaps_classifies_missing_and_weak_evidence():
    records = [
        evidence_record("C4-Q01", "4.1", 0.0),
        evidence_record("C4-Q02", "4.2", 0.6),
    ]

    gaps = detect_evidence_gaps(records)

    assert [gap["gap_type"] for gap in gaps] == [
        "missing_evidence",
        "weak_evidence",
    ]


def test_detect_evidence_gaps_accepts_threshold_score():
    records = [
        evidence_record("C4-Q01", "4.1", 0.75),
    ]

    assert detect_evidence_gaps(records) == []


def test_detect_evidence_gaps_flags_missing_structured_evidence_reference():
    records = [
        {
            "question_id": "C4-Q03",
            "clause": "4.3",
            "title": "AIMS scope",
            "confidence_score": 0.9,
            "expected_evidence": ["AIMS scope statement"],
            "actual_evidence_references": [],
        }
    ]

    gaps = detect_evidence_gaps(records)

    assert any(
        gap["gap_type"] == "missing_structured_evidence_reference"
        and gap["question_id"] == "C4-Q03"
        for gap in gaps
    )


def test_detect_evidence_gaps_does_not_flag_missing_reference_when_no_expected_evidence():
    records = [
        evidence_record("C4-Q01", "4.1", 0.75),
    ]

    assert detect_evidence_gaps(records) == []


def test_detect_coverage_gaps_detects_missing_clause_44():
    questions = [
        question("C4-Q01", "4.1"),
        question("C4-Q02", "4.2"),
        question("C4-Q03", "4.3"),
    ]

    responses = [
        response("C4-Q01"),
        response("C4-Q02"),
        response("C4-Q03"),
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert any(
        gap["gap_type"] == "missing_required_subclause"
        and gap["clause"] == "4.4"
        for gap in gaps
    )


def test_detect_coverage_gaps_detects_unexpected_response_id():
    questions = complete_questions()
    responses = complete_responses() + [response("C4-Q05")]

    gaps = detect_coverage_gaps(questions, responses)

    assert any(
        gap["gap_type"] == "unexpected_response_id"
        and gap["question_id"] == "C4-Q05"
        for gap in gaps
    )


def test_detect_gaps_combines_coverage_and_evidence_gaps():
    questions = complete_questions()
    responses = complete_responses() + [response("C4-Q05")]
    records = [
        evidence_record("C4-Q01", "4.1", 1.0),
        evidence_record("C4-Q02", "4.2", 0.6),
        evidence_record("C4-Q03", "4.3", 1.0),
        evidence_record("C4-Q04", "4.4", 1.0),
    ]

    gaps = detect_gaps(questions, responses, records)
    gap_types = [gap["gap_type"] for gap in gaps]

    assert "unexpected_response_id" in gap_types
    assert "weak_evidence" in gap_types


def test_calculate_readiness_empty_records_returns_zero():
    assert calculate_readiness([]) == 0


def test_calculate_readiness_without_structural_gaps():
    records = [
        evidence_record("C4-Q01", "4.1", 1.0),
        evidence_record("C4-Q02", "4.2", 0.5),
    ]

    assert calculate_readiness(records) == 75.0


def test_calculate_readiness_caps_score_when_structural_gap_exists():
    records = complete_evidence_records(score=1.0)
    gaps = [
        {
            "question_id": "QUESTION_BANK",
            "clause": "4.4",
            "gap_type": "missing_required_subclause",
            "description": "Required Clause 4.4 is missing from the question bank.",
        }
    ]

    assert calculate_readiness(records, gaps) == 74.0


def test_calculate_readiness_not_capped_for_evidence_gap_only():
    records = [
        evidence_record("C4-Q01", "4.1", 1.0),
        evidence_record("C4-Q02", "4.2", 0.6),
    ]

    gaps = [
        {
            "question_id": "C4-Q02",
            "clause": "4.2",
            "gap_type": "weak_evidence",
            "description": "Evidence is weak.",
        }
    ]

    assert calculate_readiness(records, gaps) == 80.0
