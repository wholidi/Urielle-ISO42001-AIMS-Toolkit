from clause_04_context.fabric.gap_detector import detect_coverage_gaps


def test_complete_clause04_coverage_has_no_missing_required_subclauses():
    questions = [
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q02", "clause": "4.2"},
        {"question_id": "C4-Q03", "clause": "4.3"},
        {"question_id": "C4-Q04", "clause": "4.4"},
    ]

    responses = [
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q02"},
        {"question_id": "C4-Q03"},
        {"question_id": "C4-Q04"},
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert not any(
        gap["gap_type"] == "missing_required_subclause"
        for gap in gaps
    )


def test_missing_clause_44_is_detected():
    questions = [
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q02", "clause": "4.2"},
        {"question_id": "C4-Q03", "clause": "4.3"},
    ]

    responses = [
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q02"},
        {"question_id": "C4-Q03"},
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert {
        "question_id": "QUESTION_BANK",
        "clause": "4.4",
        "gap_type": "missing_required_subclause",
        "description": "Required Clause 4.4 is missing from the question bank.",
    } in gaps


def test_unexpected_response_id_is_detected():
    questions = [
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q02", "clause": "4.2"},
        {"question_id": "C4-Q03", "clause": "4.3"},
        {"question_id": "C4-Q04", "clause": "4.4"},
    ]

    responses = [
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q02"},
        {"question_id": "C4-Q03"},
        {"question_id": "C4-Q04"},
        {"question_id": "C4-Q05"},
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert any(
        gap["gap_type"] == "unexpected_response_id"
        and gap["question_id"] == "C4-Q05"
        for gap in gaps
    )


def test_duplicate_question_id_is_detected():
    questions = [
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q02", "clause": "4.2"},
        {"question_id": "C4-Q03", "clause": "4.3"},
        {"question_id": "C4-Q04", "clause": "4.4"},
    ]

    responses = [
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q02"},
        {"question_id": "C4-Q03"},
        {"question_id": "C4-Q04"},
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert any(
        gap["gap_type"] == "duplicate_question_id"
        and gap["question_id"] == "C4-Q01"
        for gap in gaps
    )


def test_duplicate_response_id_is_detected():
    questions = [
        {"question_id": "C4-Q01", "clause": "4.1"},
        {"question_id": "C4-Q02", "clause": "4.2"},
        {"question_id": "C4-Q03", "clause": "4.3"},
        {"question_id": "C4-Q04", "clause": "4.4"},
    ]

    responses = [
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q01"},
        {"question_id": "C4-Q02"},
        {"question_id": "C4-Q03"},
        {"question_id": "C4-Q04"},
    ]

    gaps = detect_coverage_gaps(questions, responses)

    assert any(
        gap["gap_type"] == "duplicate_response_id"
        and gap["question_id"] == "C4-Q01"
        for gap in gaps
    )