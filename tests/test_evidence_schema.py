from datetime import datetime

from clause_04_context.schema.evidence import (
    EvidenceRecord,
    extract_evidence_references,
    create_evidence_record,
)


def sample_question():
    return {
        "question_id": "C4-Q01",
        "clause": "4.1",
        "title": "Context of the organization",
        "question": "Has the organization identified internal and external issues?",
        "expected_evidence": [
            "context register",
            "internal and external issue list",
        ],
    }


def sample_response():
    return {
        "question_id": "C4-Q01",
        "response": (
            "The organization has identified internal and external AI governance issues "
            "in the Context Register. Evidence is stored in Clause4_Context_Register.xlsx. "
            "Owner: AI Governance Lead. Date: 2026-07-04."
        ),
        "auditor_note": "Initial evidence appears available.",
    }


def test_extract_evidence_references_finds_excel_file():
    response_text = "Evidence is stored in Clause4_Context_Register.xlsx."

    references = extract_evidence_references(response_text)

    assert references == [
        {
            "reference_type": "file_reference",
            "reference_name": "Clause4_Context_Register.xlsx",
            "extracted_from": "human_response",
        }
    ]


def test_extract_evidence_references_finds_multiple_file_types():
    response_text = (
        "Evidence is stored in Clause4_Context_Register.xlsx, "
        "Clause4_AIMS_Process_Map.pdf, and audit_notes.md."
    )

    references = extract_evidence_references(response_text)
    reference_names = [item["reference_name"] for item in references]

    assert "Clause4_Context_Register.xlsx" in reference_names
    assert "Clause4_AIMS_Process_Map.pdf" in reference_names
    assert "audit_notes.md" in reference_names


def test_extract_evidence_references_returns_empty_list_when_no_file_reference():
    response_text = "Evidence is available in the stakeholder register."

    assert extract_evidence_references(response_text) == []


def test_create_evidence_record_returns_evidence_record_instance():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    assert isinstance(record, EvidenceRecord)


def test_create_evidence_record_maps_required_fields():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    data = record.to_dict()

    assert data["session_id"] == "SESSION-001"
    assert data["question_id"] == "C4-Q01"
    assert data["clause"] == "4.1"
    assert data["title"] == "Context of the organization"
    assert data["question"] == "Has the organization identified internal and external issues?"
    assert data["response_source_type"] == "human_file"
    assert data["confidence_score"] == 0.95
    assert data["confidence_type"] == "rule_based_response_quality"
    assert data["auditor_note"] == "Initial evidence appears available."
    assert data["auditor_flag"] is False


def test_create_evidence_record_preserves_expected_evidence():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    data = record.to_dict()

    assert data["expected_evidence"] == [
        "context register",
        "internal and external issue list",
    ]


def test_create_evidence_record_extracts_actual_evidence_references():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    data = record.to_dict()

    assert data["actual_evidence_references"] == [
        {
            "reference_type": "file_reference",
            "reference_name": "Clause4_Context_Register.xlsx",
            "extracted_from": "human_response",
        }
    ]


def test_create_evidence_record_handles_missing_expected_evidence():
    question = sample_question()
    del question["expected_evidence"]

    record = create_evidence_record(
        session_id="SESSION-001",
        question=question,
        response=sample_response(),
        confidence_score=0.8,
        auditor_flag=False,
    )

    data = record.to_dict()

    assert data["expected_evidence"] == []


def test_create_evidence_record_handles_missing_response_text():
    response = {
        "question_id": "C4-Q01",
        "auditor_note": "No response text.",
    }

    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=response,
        confidence_score=0.0,
        auditor_flag=True,
    )

    data = record.to_dict()

    assert data["response"] == ""
    assert data["actual_evidence_references"] == []
    assert data["auditor_flag"] is True


def test_evidence_record_serializes_to_dict():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    data = record.to_dict()

    assert isinstance(data, dict)
    assert data["question_id"] == "C4-Q01"


def test_timestamp_is_valid_utc_iso_format():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=0.95,
        auditor_flag=False,
    )

    timestamp = datetime.fromisoformat(record.to_dict()["timestamp"])

    assert timestamp.utcoffset() is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_score_is_within_expected_bounds():
    record = create_evidence_record(
        session_id="SESSION-001",
        question=sample_question(),
        response=sample_response(),
        confidence_score=1.0,
        auditor_flag=False,
    )

    score = record.to_dict()["confidence_score"]

    assert 0.0 <= score <= 1.0