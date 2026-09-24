"""Phase 03 repeatability tests across the shared-kernel record chain."""

from __future__ import annotations

import json

from agentic_assessment.shared_kernel.findings import derive_findings
from agentic_assessment.shared_kernel.report_state import derive_report_state
from agentic_assessment.shared_kernel.requirements import evaluate_requirement
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    QUESTION_ID,
    REQUIREMENT_REF,
    TIMESTAMP,
    accepted_records,
    mapping,
)


def _evaluate() -> bytes:
    lifecycle, acceptance = accepted_records()
    requirement = evaluate_requirement(
        assessment_id=ASSESSMENT_ID, requirement_ref=REQUIREMENT_REF,
        question_id=QUESTION_ID, mappings=[mapping()], lifecycles=[lifecycle],
        acceptances=[acceptance], evaluated_at=TIMESTAMP
    )
    findings = derive_findings([requirement])
    report = derive_report_state(
        assessment_id=ASSESSMENT_ID, findings=findings,
        requirement_assessments=[requirement], recorded_at=TIMESTAMP
    )
    payload = {
        "lifecycle": lifecycle.to_contract(),
        "acceptance": acceptance.to_contract(),
        "requirement": requirement.to_contract(),
        "findings": [item.to_contract() for item in findings],
        "report": report.to_contract(),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def test_repeated_evaluation_is_byte_stable_with_fixed_clock() -> None:
    assert _evaluate() == _evaluate()
