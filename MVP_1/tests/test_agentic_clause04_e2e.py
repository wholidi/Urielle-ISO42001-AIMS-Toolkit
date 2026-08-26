"""End-to-end tests for governed Agentic Clause 04."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from agentic_assessment.clause04_adapter import (
    Clause04Adapter,
)
from agentic_assessment.clause04_workflow import (
    Clause04Workflow,
)
from agentic_assessment.supervisor import (
    SequentialSupervisor,
    SupervisorState,
    WORKFLOW_SEQUENCE,
)
from governance.startup_validator import (
    initialize_governance,
)


ASSESSMENT_ID = "CLAUSE04-E2E-001"


def deterministic_e2e_executor(
    context: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Return one valid Clause 04 record with no evidence reference."""

    return {
        "session_id": "CLAUSE4-E2E-001",
        "status": "COMPLETED",
        "score": 75.0,
        "evidence_records": [
            {
                "session_id": "CLAUSE4-E2E-001",
                "question_id": "C4-Q01",
                "clause": "4.1",
                "title": "Context of the organization",
                "question": (
                    "Has the organization determined "
                    "internal and external issues?"
                ),
                "expected_evidence": [
                    "context register",
                ],
                "response": (
                    "Context has been discussed but "
                    "structured evidence is not yet supplied."
                ),
                "response_source_type": "human_response",
                "actual_evidence_references": [],
                "confidence_score": 1.0,
                "confidence_type": "DETERMINISTIC",
                "auditor_note": (
                    "Structured evidence reference required."
                ),
                "auditor_flag": False,
                "timestamp": (
                    "2026-08-26T00:00:00+00:00"
                ),
            },
        ],
        "gaps": [
            {
                "question_id": "C4-Q01",
                "clause": "4.1",
                "gap_type": "EVIDENCE_REQUIRED",
                "description": (
                    "Structured evidence reference is missing."
                ),
            },
        ],
    }


def build_workflow() -> Clause04Workflow:
    return Clause04Workflow(
        clause04_adapter=Clause04Adapter(
            executor=deterministic_e2e_executor
        )
    )


def build_supervisor(
    workflow: Clause04Workflow,
) -> SequentialSupervisor:
    runtime = initialize_governance()

    return SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers=workflow.handlers(),
    )


def base_context() -> dict[str, Any]:
    return {
        "assessment_id": ASSESSMENT_ID,
    }


def test_e2e_pending_finding_produces_draft_report() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    result = supervisor.run(
        run_id="RUN-E2E-001",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    assert result.state is SupervisorState.COMPLETED

    assert workflow.last_report is not None
    assert workflow.last_report.report_status == "DRAFT"
    assert workflow.last_report.finding_count == 1
    assert workflow.last_report.pending_finding_count == 1


def test_e2e_explicit_human_review_produces_final_report() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    context = base_context()

    context["human_reviews"] = {
        (
            "FND-CLAUSE04-E2E-001-001"
        ): {
            "reviewer_id": "reviewer-e2e-001",
            "disposition": "ACCEPTED",
        }
    }

    result = supervisor.run(
        run_id="RUN-E2E-002",
        assessment_id=ASSESSMENT_ID,
        assessment_context=context,
        steps=WORKFLOW_SEQUENCE,
    )

    assert result.state is SupervisorState.COMPLETED

    assert workflow.last_report is not None
    assert workflow.last_report.report_status == "FINAL"
    assert workflow.last_report.pending_finding_count == 0
    assert workflow.last_report.accepted_finding_count == 1


def test_e2e_executes_complete_declared_workflow() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    result = supervisor.run(
        run_id="RUN-E2E-003",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    assert result.completed_steps == WORKFLOW_SEQUENCE


def test_e2e_emits_schema_valid_execution_events() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    result = supervisor.run(
        run_id="RUN-E2E-004",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    validator = supervisor.contract_validator

    for event in result.events:
        validator.require_valid(
            contract_name="execution_event",
            instance=event.to_contract(),
        )


def test_e2e_report_contains_traceability() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    supervisor.run(
        run_id="RUN-E2E-005",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    assert workflow.last_report is not None

    markdown = workflow.last_report.markdown

    assert ASSESSMENT_ID in markdown
    assert "C4-Q01" in markdown
    assert "ED-" in markdown
    assert "FND-" in markdown


def test_e2e_unknown_human_review_fails_closed() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    context = base_context()

    context["human_reviews"] = {
        "FND-UNKNOWN-001": {
            "reviewer_id": "reviewer-e2e-002",
            "disposition": "ACCEPTED",
        }
    }

    result = supervisor.run(
        run_id="RUN-E2E-006",
        assessment_id=ASSESSMENT_ID,
        assessment_context=context,
        steps=WORKFLOW_SEQUENCE,
    )

    assert result.state is SupervisorState.STOPPED

    assert (
        result.completed_steps[-1]
        is not WORKFLOW_SEQUENCE[-1]
    )

    assert workflow.last_report is None


def test_e2e_invalid_human_disposition_fails_closed() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    context = base_context()

    context["human_reviews"] = {
        "FND-CLAUSE04-E2E-001-001": {
            "reviewer_id": "reviewer-e2e-003",
            "disposition": "PENDING",
        }
    }

    result = supervisor.run(
        run_id="RUN-E2E-007",
        assessment_id=ASSESSMENT_ID,
        assessment_context=context,
        steps=WORKFLOW_SEQUENCE,
    )

    assert result.state is SupervisorState.STOPPED
    assert workflow.last_report is None


def test_e2e_human_review_is_not_invented() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    supervisor.run(
        run_id="RUN-E2E-008",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    assert workflow.last_report is not None

    assert (
        workflow.last_report.pending_finding_count
        == 1
    )

    assert (
        workflow.last_report.accepted_finding_count
        == 0
    )


def test_e2e_report_generator_does_not_recalculate_score() -> None:
    workflow = build_workflow()
    supervisor = build_supervisor(
        workflow
    )

    supervisor.run(
        run_id="RUN-E2E-009",
        assessment_id=ASSESSMENT_ID,
        assessment_context=base_context(),
        steps=WORKFLOW_SEQUENCE,
    )

    assert workflow.last_report is not None
    assert workflow.last_report.readiness_score == 75.0