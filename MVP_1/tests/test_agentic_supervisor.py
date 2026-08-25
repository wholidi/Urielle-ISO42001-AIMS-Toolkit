"""Tests for deterministic Agentic Clause 04 supervision."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from agentic_assessment.supervisor import (
    SequentialSupervisor,
    SupervisorError,
    SupervisorState,
    WorkflowStep,
)
from governance.startup_validator import initialize_governance


def build_supervisor() -> SequentialSupervisor:
    runtime = initialize_governance()

    return SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
    )


def test_supervisor_completes_sequential_workflow() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-001",
        assessment_id="CLAUSE04-001",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.QUESTION_SELECTION,
        ),
    )

    assert result.state is SupervisorState.COMPLETED

    assert result.completed_steps == (
        WorkflowStep.ASSESSMENT_PLANNING,
        WorkflowStep.QUESTION_SELECTION,
    )


def test_supervisor_executes_steps_in_declared_order() -> None:
    observed: list[str] = []

    def planning(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        observed.append("planning")
        return context

    def selection(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        observed.append("selection")
        return context

    runtime = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers={
            WorkflowStep.ASSESSMENT_PLANNING: planning,
            WorkflowStep.QUESTION_SELECTION: selection,
        },
    )

    supervisor.run(
        run_id="RUN-002",
        assessment_id="CLAUSE04-002",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.QUESTION_SELECTION,
        ),
    )

    assert observed == [
        "planning",
        "selection",
    ]


def test_each_step_produces_execution_events() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-003",
        assessment_id="CLAUSE04-003",
        assessment_context={},
        steps=(WorkflowStep.ASSESSMENT_PLANNING,),
    )

    event_types = [
        event.action
        for event in result.events
    ]

    assert event_types == [
        "ASSESSMENT_RUN_STARTED",
        "WORKFLOW_STEP_STARTED",
        "WORKFLOW_STEP_COMPLETED",
        "ASSESSMENT_RUN_COMPLETED",
    ]


def test_event_sequence_is_monotonic() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-004",
        assessment_id="CLAUSE04-004",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.QUESTION_SELECTION,
        ),
    )

    assert [
        event.event_id
        for event in result.events
    ] == [
    "EVT-RUN-004-0001",
    "EVT-RUN-004-0002",
    "EVT-RUN-004-0003",
    "EVT-RUN-004-0004",
    "EVT-RUN-004-0005",
    "EVT-RUN-004-0006",
    ]

def test_handler_failure_stops_workflow() -> None:
    def failing_handler(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        raise RuntimeError("failure")

    runtime = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers={
            WorkflowStep.ASSESSMENT_PLANNING:
                failing_handler,
        },
    )

    result = supervisor.run(
        run_id="RUN-005",
        assessment_id="CLAUSE04-005",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.QUESTION_SELECTION,
        ),
    )

    assert result.state is SupervisorState.STOPPED
    assert result.completed_steps == ()

    assert (
        result.events[-1].action
        == "WORKFLOW_STEP_FAILED"
    )


def test_handler_failure_prevents_later_steps() -> None:
    observed: list[str] = []

    def failing(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        observed.append("first")
        raise RuntimeError

    def later(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        observed.append("later")
        return context

    runtime = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers={
            WorkflowStep.ASSESSMENT_PLANNING: failing,
            WorkflowStep.QUESTION_SELECTION: later,
        },
    )

    supervisor.run(
        run_id="RUN-006",
        assessment_id="CLAUSE04-006",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.QUESTION_SELECTION,
        ),
    )

    assert observed == ["first"]


def test_missing_run_identifier_fails_closed() -> None:
    supervisor = build_supervisor()

    with pytest.raises(
        SupervisorError,
        match="run_id is missing or invalid",
    ):
        supervisor.run(
            run_id="",
            assessment_id="CLAUSE04-008",
            assessment_context={},
        )


def test_invalid_handler_output_fails_closed() -> None:
    def invalid_handler(
        context: Mapping[str, Any],
    ) -> Any:
        return "invalid"

    runtime = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers={
            WorkflowStep.ASSESSMENT_PLANNING:
                invalid_handler,
        },
    )

    with pytest.raises(
        SupervisorError,
        match="returned invalid context",
    ):
        supervisor.run(
            run_id="RUN-007",
            assessment_id="CLAUSE04-007",
            assessment_context={},
            steps=(WorkflowStep.ASSESSMENT_PLANNING,),
        )


def test_human_review_is_never_self_approved() -> None:
    supervisor = build_supervisor()

    decision = supervisor.request_human_review(
        run_id="RUN-008",
        reason="Evidence conflict requires review.",
    )

    assert decision.decision.value == (
        "REQUIRE_HUMAN_APPROVAL"
    )

def test_all_emitted_events_satisfy_phase1_contract() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-009",
        assessment_id="CLAUSE04-009",
        assessment_context={},
        steps=(
            WorkflowStep.ASSESSMENT_PLANNING,
            WorkflowStep.EVIDENCE_ASSESSMENT,
        ),
    )

    for event in result.events:
        supervisor.contract_validator.require_valid(
            contract_name="execution_event",
            instance=event.to_contract(),
        )


def test_execution_event_contains_required_identity_fields() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-010",
        assessment_id="CLAUSE04-010",
        assessment_context={},
        steps=(WorkflowStep.ASSESSMENT_PLANNING,),
    )

    event = result.events[0]
    payload = event.to_contract()

    assert payload["assessment_id"] == "CLAUSE04-010"
    assert payload["correlation_id"] == "RUN-010"
    assert payload["component_id"] == "agentic.supervisor"
    assert payload["schema_version"] == "1.0.0"


def test_execution_event_ids_follow_sequence() -> None:
    supervisor = build_supervisor()

    result = supervisor.run(
        run_id="RUN-011",
        assessment_id="CLAUSE04-011",
        assessment_context={},
        steps=(WorkflowStep.ASSESSMENT_PLANNING,),
    )

    assert [
        event.event_id
        for event in result.events
    ] == [
        "EVT-RUN-011-0001",
        "EVT-RUN-011-0002",
        "EVT-RUN-011-0003",
        "EVT-RUN-011-0004",
    ]


def test_missing_assessment_identifier_fails_closed() -> None:
    supervisor = build_supervisor()

    with pytest.raises(
        SupervisorError,
        match="assessment_id is missing or invalid",
    ):
        supervisor.run(
            run_id="RUN-012",
            assessment_id="",
            assessment_context={},
        )


def test_failed_handler_emits_schema_valid_error_record() -> None:
    def failing_handler(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        raise RuntimeError("internal detail")

    runtime = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=runtime.policy_enforcer,
        handlers={
            WorkflowStep.ASSESSMENT_PLANNING:
                failing_handler,
        },
    )

    result = supervisor.run(
        run_id="RUN-013",
        assessment_id="CLAUSE04-013",
        assessment_context={},
        steps=(WorkflowStep.ASSESSMENT_PLANNING,),
    )

    failed_event = result.events[-1]
    payload = failed_event.to_contract()

    assert payload["event_status"] == "FAILED"
    assert payload["workflow_state"] == "FAILED"
    assert payload["error"]["error_type"] == "RuntimeError"

    supervisor.contract_validator.require_valid(
        contract_name="execution_event",
        instance=payload,
    )