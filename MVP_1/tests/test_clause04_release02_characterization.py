"""Release 0.2 guards for the frozen Clause 04 authority boundary."""

from __future__ import annotations

import hashlib
import json

from agentic_assessment.supervisor import WORKFLOW_SEQUENCE, WorkflowStep
from clause_04_context.run_clause04_demo import (
    QUESTIONS_FILE,
    RESPONSES_FILE,
    load_json,
    run_clause04_assessment,
)


EXPECTED_NORMALIZED_RESULT_SHA256 = (
    "76c36e453f29b650f8cce0e41d99d71a09c87ab47592bf2244e089d79cc6984d"
)

def _frozen_clause04_result() -> dict:
    return run_clause04_assessment(
        session_id="CLAUSE4-CHARACTERIZATION-001",
        questions=load_json(QUESTIONS_FILE),
        responses=load_json(RESPONSES_FILE),
    )


def _normalized_fingerprint(result: dict) -> str:
    normalized = json.loads(json.dumps(result))
    for record in normalized["evidence_records"]:
        record.pop("timestamp", None)
    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_clause04_authoritative_result_remains_frozen() -> None:
    result = _frozen_clause04_result()

    assert result["status"] == "COMPLETED"
    assert result["score"] == 100.0
    assert result["gaps"] == []
    assert [item["question_id"] for item in result["evidence_records"]] == [
        "C4-Q01",
        "C4-Q02",
        "C4-Q03",
        "C4-Q04",
    ]
    assert [item["clause"] for item in result["evidence_records"]] == [
        "4.1",
        "4.2",
        "4.3",
        "4.4",
    ]
    assert _normalized_fingerprint(result) == EXPECTED_NORMALIZED_RESULT_SHA256


def test_clause04_default_workflow_sequence_remains_unchanged() -> None:
    assert WORKFLOW_SEQUENCE == (
        WorkflowStep.ASSESSMENT_PLANNING,
        WorkflowStep.QUESTION_SELECTION,
        WorkflowStep.CLAUSE_04_EXECUTION,
        WorkflowStep.EVIDENCE_ASSESSMENT,
        WorkflowStep.FINDING_GENERATION,
        WorkflowStep.HUMAN_REVIEW_DECISION,
        WorkflowStep.REPORT_GENERATION,
    )
