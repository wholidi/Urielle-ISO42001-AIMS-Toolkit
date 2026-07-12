REQUIRED_QUESTION_FIELDS = [
    "question_id",
    "clause",
    "title",
    "question",
    "expected_evidence"
]

REQUIRED_RESPONSE_FIELDS = [
    "question_id",
    "response",
    "auditor_note"
]


def find_duplicates(values):
    seen = set()
    duplicates = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return sorted(list(duplicates))


def validate_questions(questions):
    errors = []

    if not isinstance(questions, list):
        return ["Questions file must contain a JSON array."]

    question_ids = []

    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            errors.append(f"Question at index {index} must be a JSON object.")
            continue

        for field in REQUIRED_QUESTION_FIELDS:
            if field not in question:
                errors.append(
                    f"Question at index {index} is missing required field: {field}."
                )

        question_id = question.get("question_id")

        if question_id:
            question_ids.append(question_id)

        expected_evidence = question.get("expected_evidence")

        if "expected_evidence" in question and not isinstance(expected_evidence, list):
            errors.append(
                f"Question {question_id or index} field expected_evidence must be a list."
            )

    duplicate_question_ids = find_duplicates(question_ids)

    for question_id in duplicate_question_ids:
        errors.append(f"Duplicate question_id found in questions: {question_id}.")

    return errors


def validate_responses(responses):
    errors = []

    if not isinstance(responses, list):
        return ["Responses file must contain a JSON array."]

    response_ids = []

    for index, response in enumerate(responses):
        if not isinstance(response, dict):
            errors.append(f"Response at index {index} must be a JSON object.")
            continue

        for field in REQUIRED_RESPONSE_FIELDS:
            if field not in response:
                errors.append(
                    f"Response at index {index} is missing required field: {field}."
                )

        question_id = response.get("question_id")

        if question_id:
            response_ids.append(question_id)

        if "response" in response and not isinstance(response.get("response"), str):
            errors.append(
                f"Response {question_id or index} field response must be a string."
            )

        if "auditor_note" in response and not isinstance(response.get("auditor_note"), str):
            errors.append(
                f"Response {question_id or index} field auditor_note must be a string."
            )

    duplicate_response_ids = find_duplicates(response_ids)

    for response_id in duplicate_response_ids:
        errors.append(f"Duplicate question_id found in responses: {response_id}.")

    return errors


def validate_question_response_alignment(questions, responses):
    errors = []

    question_ids = {
        question.get("question_id")
        for question in questions
        if isinstance(question, dict) and question.get("question_id")
    }

    response_ids = {
        response.get("question_id")
        for response in responses
        if isinstance(response, dict) and response.get("question_id")
    }

    for response_id in sorted(response_ids - question_ids):
        errors.append(
            f"Unexpected response ID found: {response_id}. No matching question exists."
        )

    for question_id in sorted(question_ids - response_ids):
        errors.append(
            f"Missing response for question ID: {question_id}."
        )

    return errors


def validate_inputs(questions, responses):
    errors = []

    errors.extend(validate_questions(questions))
    errors.extend(validate_responses(responses))

    if not errors:
        errors.extend(validate_question_response_alignment(questions, responses))

    return errors


def raise_if_invalid_inputs(questions, responses):
    errors = validate_inputs(questions, responses)

    if errors:
        formatted_errors = "\n".join(f"- {error}" for error in errors)
        raise ValueError(
            "Input validation failed. Please fix the question/response JSON files:\n"
            f"{formatted_errors}"
        )