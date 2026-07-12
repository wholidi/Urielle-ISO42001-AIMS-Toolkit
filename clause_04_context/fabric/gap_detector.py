REQUIRED_CLAUSE_04_SUBCLAUSES = ["4.1", "4.2", "4.3", "4.4"]


def find_duplicates(items):
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)

    return sorted(list(duplicates))


def detect_coverage_gaps(questions, responses):
    gaps = []

    question_ids = [question.get("question_id") for question in questions]
    response_ids = [response.get("question_id") for response in responses]
    question_clauses = [question.get("clause") for question in questions]

    for required_clause in REQUIRED_CLAUSE_04_SUBCLAUSES:
        if required_clause not in question_clauses:
            gaps.append({
                "question_id": "QUESTION_BANK",
                "clause": required_clause,
                "gap_type": "missing_required_subclause",
                "description": f"Required Clause {required_clause} is missing from the question bank."
            })

    duplicate_question_ids = find_duplicates(question_ids)
    for question_id in duplicate_question_ids:
        gaps.append({
            "question_id": question_id,
            "clause": "unknown",
            "gap_type": "duplicate_question_id",
            "description": f"Duplicate question ID found in question bank: {question_id}."
        })

    duplicate_response_ids = find_duplicates(response_ids)
    for response_id in duplicate_response_ids:
        gaps.append({
            "question_id": response_id,
            "clause": "unknown",
            "gap_type": "duplicate_response_id",
            "description": f"Duplicate response ID found in human responses: {response_id}."
        })

    for response_id in response_ids:
        if response_id not in question_ids:
            gaps.append({
                "question_id": response_id,
                "clause": "unknown",
                "gap_type": "unexpected_response_id",
                "description": f"Response ID {response_id} does not match any question in the question bank."
            })

    for question in questions:
        question_id = question.get("question_id")
        clause = question.get("clause")

        if question_id not in response_ids:
            gaps.append({
                "question_id": question_id,
                "clause": clause,
                "gap_type": "missing_response",
                "description": f"No human response found for {question_id} / Clause {clause}."
            })

    return gaps


def detect_evidence_gaps(evidence_records):
    gaps = []

    for record in evidence_records:
        score = record["confidence_score"]

        if score == 0.0:
            gaps.append({
                "question_id": record["question_id"],
                "clause": record["clause"],
                "gap_type": "missing_evidence",
                "description": f"No response or evidence provided for {record['title']}."
            })

        elif score < 0.75:
            gaps.append({
                "question_id": record["question_id"],
                "clause": record["clause"],
                "gap_type": "weak_evidence",
                "description": f"Evidence for {record['title']} is incomplete or requires auditor review."
            })

        if record.get("expected_evidence") and not record.get("actual_evidence_references"):
            gaps.append({
                "question_id": record["question_id"],
                "clause": record["clause"],
                "gap_type": "missing_structured_evidence_reference",
                "description": (
                    f"{record['title']} has expected evidence, but no structured evidence "
                    "reference was extracted from the response."
                )
            })

    return gaps


def detect_gaps(questions, responses, evidence_records):
    coverage_gaps = detect_coverage_gaps(questions, responses)
    evidence_gaps = detect_evidence_gaps(evidence_records)

    return coverage_gaps + evidence_gaps


def calculate_readiness(evidence_records, gaps=None):
    if not evidence_records:
        return 0

    total_score = sum(record["confidence_score"] for record in evidence_records)
    readiness = total_score / len(evidence_records)

    if gaps:
        structural_gap_types = {
            "missing_required_subclause",
            "duplicate_question_id",
            "duplicate_response_id",
            "unexpected_response_id",
            "missing_response",
        }

        has_structural_gap = any(
            gap.get("gap_type") in structural_gap_types
            for gap in gaps
        )

        if has_structural_gap:
            readiness = min(readiness, 0.74)

    return round(readiness * 100, 2)
