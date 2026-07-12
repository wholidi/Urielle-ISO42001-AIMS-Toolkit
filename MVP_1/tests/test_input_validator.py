import pytest

from clause_04_context.validator.input_validator import (
    raise_if_invalid_inputs,
    validate_inputs,
    validate_question_response_alignment,
    validate_questions,
    validate_responses,
)


def valid_questions():
    return [
        {
            "question_id": "C4-Q01",
            "clause": "4.1",
            "title": "Context of the organization",
            "question": "Has the organization identified internal and external issues?",
            "expected_evidence": ["context register"],
        },
        {
            "question_id": "C4-Q02",
            "clause": "4.2",
            "title": "Interested parties",
            "question": "Has the organization identified interested parties?",
            "expected_evidence": ["stakeholder register"],
        },
        {
            "question_id": "C4-Q03",
            "clause": "4.3",
            "title": "AIMS scope",
            "question": "Has the organization defined the AIMS scope?",
            "expected_evidence": ["AIMS scope statement"],
        },
        {
            "question_id": "C4-Q04",
            "clause": "4.4",
            "title": "AI Management System",
            "question": "Has the organization established an AI Management System?",
            "expected_evidence": ["AIMS process map"],
        },
    ]


def valid_responses():
    return [
        {
            "question_id": "C4-Q01",
            "response": "Evidence is stored in Clause4_Context_Register.xlsx.",
            "auditor_note": "Reviewed.",
        },
        {
            "question_id": "C4-Q02",
            "response": "Evidence is stored in Clause4_Stakeholder_Register.xlsx.",
            "auditor_note": "Reviewed.",
        },
        {
            "question_id": "C4-Q03",
            "response": "Evidence is stored in Clause4_AIMS_Scope_Statement.xlsx.",
            "auditor_note": "Reviewed.",
        },
        {
            "question_id": "C4-Q04",
            "response": "Evidence is stored in Clause4_AIMS_Process_Map.xlsx.",
            "auditor_note": "Reviewed.",
        },
    ]


def test_validate_questions_accepts_valid_questions():
    errors = validate_questions(valid_questions())

    assert errors == []


def test_validate_questions_rejects_non_array_input():
    errors = validate_questions({"question_id": "C4-Q01"})

    assert errors == ["Questions file must contain a JSON array."]


def test_validate_questions_rejects_non_object_item():
    questions = valid_questions()
    questions.append("not-a-question-object")

    errors = validate_questions(questions)

    assert "Question at index 4 must be a JSON object." in errors


def test_validate_questions_detects_missing_required_field():
    questions = valid_questions()
    del questions[0]["question_id"]

    errors = validate_questions(questions)

    assert "Question at index 0 is missing required field: question_id." in errors


def test_validate_questions_detects_expected_evidence_not_list():
    questions = valid_questions()
    questions[0]["expected_evidence"] = "context register"

    errors = validate_questions(questions)

    assert "Question C4-Q01 field expected_evidence must be a list." in errors


def test_validate_questions_detects_duplicate_question_id():
    questions = valid_questions()
    questions[1]["question_id"] = "C4-Q01"

    errors = validate_questions(questions)

    assert "Duplicate question_id found in questions: C4-Q01." in errors


def test_validate_responses_accepts_valid_responses():
    errors = validate_responses(valid_responses())

    assert errors == []


def test_validate_responses_rejects_non_array_input():
    errors = validate_responses({"question_id": "C4-Q01"})

    assert errors == ["Responses file must contain a JSON array."]


def test_validate_responses_rejects_non_object_item():
    responses = valid_responses()
    responses.append("not-a-response-object")

    errors = validate_responses(responses)

    assert "Response at index 4 must be a JSON object." in errors


def test_validate_responses_detects_missing_question_id():
    responses = valid_responses()
    del responses[0]["question_id"]

    errors = validate_responses(responses)

    assert "Response at index 0 is missing required field: question_id." in errors


def test_validate_responses_detects_missing_response_field():
    responses = valid_responses()
    del responses[0]["response"]

    errors = validate_responses(responses)

    assert "Response at index 0 is missing required field: response." in errors


def test_validate_responses_detects_missing_auditor_note():
    responses = valid_responses()
    del responses[0]["auditor_note"]

    errors = validate_responses(responses)

    assert "Response at index 0 is missing required field: auditor_note." in errors


def test_validate_responses_detects_non_string_response():
    responses = valid_responses()
    responses[0]["response"] = 123

    errors = validate_responses(responses)

    assert "Response C4-Q01 field response must be a string." in errors


def test_validate_responses_detects_non_string_auditor_note():
    responses = valid_responses()
    responses[0]["auditor_note"] = ["not", "a", "string"]

    errors = validate_responses(responses)

    assert "Response C4-Q01 field auditor_note must be a string." in errors


def test_validate_responses_detects_duplicate_response_id():
    responses = valid_responses()
    responses[1]["question_id"] = "C4-Q01"

    errors = validate_responses(responses)

    assert "Duplicate question_id found in responses: C4-Q01." in errors


def test_validate_alignment_accepts_matching_question_and_response_ids():
    errors = validate_question_response_alignment(
        valid_questions(),
        valid_responses(),
    )

    assert errors == []


def test_validate_alignment_detects_unexpected_response_id():
    responses = valid_responses()
    responses.append(
        {
            "question_id": "C4-Q05",
            "response": "Extra response.",
            "auditor_note": "Unexpected.",
        }
    )

    errors = validate_question_response_alignment(valid_questions(), responses)

    assert "Unexpected response ID found: C4-Q05. No matching question exists." in errors


def test_validate_alignment_detects_missing_response():
    responses = valid_responses()
    responses = [
        response for response in responses
        if response["question_id"] != "C4-Q04"
    ]

    errors = validate_question_response_alignment(valid_questions(), responses)

    assert "Missing response for question ID: C4-Q04." in errors


def test_validate_inputs_accepts_clean_inputs():
    errors = validate_inputs(valid_questions(), valid_responses())

    assert errors == []


def test_raise_if_invalid_inputs_does_not_raise_for_valid_inputs():
    raise_if_invalid_inputs(valid_questions(), valid_responses())


def test_raise_if_invalid_inputs_raises_clear_error_for_invalid_inputs():
    responses = valid_responses()
    responses.append(
        {
            "question_id": "C4-Q05",
            "response": "Unexpected extra response.",
            "auditor_note": "Unexpected.",
        }
    )

    with pytest.raises(ValueError) as error:
        raise_if_invalid_inputs(valid_questions(), responses)

    message = str(error.value)

    assert "Input validation failed" in message
    assert "Unexpected response ID found: C4-Q05" in message