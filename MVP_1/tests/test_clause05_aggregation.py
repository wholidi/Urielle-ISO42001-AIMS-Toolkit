from agentic_assessment.clause05.aggregation import aggregate_requirement

def rec(qid, outcome):
    return {
        "requirement_assessment_id": "REQ-" + qid,
        "assessment_id": "ASM-C05-TEST",
        "requirement_ref": "5.1",
        "question_id": qid,
        "outcome": outcome,
    }

Q = ["Q-C05-5.1-001", "Q-C05-5.1-002", "Q-C05-5.1-003"]

def test_all_supported_aggregates_supported():
    result = aggregate_requirement(
        assessment_id="ASM-C05-TEST", requirement_ref="5.1",
        question_ids=Q, assessments=[rec(q, "SUPPORTED") for q in reversed(Q)]
    )
    assert result.outcome == "SUPPORTED"

def test_one_unsupported_aggregates_unsupported():
    rows = [rec(Q[0],"SUPPORTED"), rec(Q[1],"UNSUPPORTED"), rec(Q[2],"UNRESOLVED")]
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
