"""Deterministic sequential supervisor for the Clause 4 agentic pilot."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from governance.policy_enforcer import (
    PolicyDecision,
    PolicyDecisionType,
    PolicyEnforcer,
)


SUPERVISOR_COMPONENT_ID = "agentic.supervisor"
WORKFLOW_RESOURCE = "AGENTIC_ASSESSMENT_WORKFLOW"


class SupervisorError(RuntimeError):
    """Raised when the supervisor cannot continue safely."""


class SupervisorState(str, Enum):
    """Deterministic workflow states."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"


class WorkflowStep(str, Enum):
    """Approved sequential Clause 4 workflow stages."""

    ASSESSMENT_PLANNING = "ASSESSMENT_PLANNING"
    QUESTION_SELECTION = "QUESTION_SELECTION"
    CLAUSE_04_EXECUTION = "CLAUSE_04_EXECUTION"
    EVIDENCE_ASSESSMENT = "EVIDENCE_ASSESSMENT"
    FINDING_GENERATION = "FINDING_GENERATION"
    HUMAN_REVIEW_DECISION = "HUMAN_REVIEW_DECISION"
    REPORT_GENERATION = "REPORT_GENERATION"


WORKFLOW_SEQUENCE: tuple[WorkflowStep, ...] = (
    WorkflowStep.ASSESSMENT_PLANNING,
    WorkflowStep.QUESTION_SELECTION,
    WorkflowStep.CLAUSE_04_EXECUTION,
    WorkflowStep.EVIDENCE_ASSESSMENT,
    WorkflowStep.FINDING_GENERATION,
    WorkflowStep.HUMAN_REVIEW_DECISION,
    WorkflowStep.REPORT_GENERATION,
)


@dataclass(frozen=True)
class ExecutionEvent:
    """One immutable supervisor execution event."""

    run_id: str
    sequence: int
    component_id: str
    event_type: str
    workflow_step: str | None
    decision: str
    reason: str


@dataclass(frozen=True)
class SupervisorResult:
    """Immutable result of one supervisor run."""

    run_id: str
    state: SupervisorState
    completed_steps: tuple[WorkflowStep, ...]
    events: tuple[ExecutionEvent, ...]


StepHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class SequentialSupervisor:
    """Governed deterministic coordinator for Agentic Clause 04.

    The supervisor coordinates approved components only.

    It does not:
    - score Clause 4 responses;
    - calculate readiness;
    - perform gap detection;
    - generate findings;
    - modify source evidence;
    - approve human decisions;
    - invoke external or generative models.
    """

    def __init__(
        self,
        *,
        policy_enforcer: PolicyEnforcer,
        handlers: Mapping[WorkflowStep, StepHandler] | None = None,
    ) -> None:
        self.policy_enforcer = policy_enforcer
        self.handlers = dict(handlers or {})

    def run(
        self,
        *,
        run_id: str,
        assessment_context: Mapping[str, Any],
        steps: Sequence[WorkflowStep] = WORKFLOW_SEQUENCE,
    ) -> SupervisorResult:
        """Execute approved workflow steps sequentially."""

        self._require_identifier(run_id, "run_id")

        events: list[ExecutionEvent] = []
        completed: list[WorkflowStep] = []

        self._require_allowed(
            action="START_ASSESSMENT_RUN",
        )

        events.append(
            self._event(
                run_id=run_id,
                sequence=len(events) + 1,
                event_type="ASSESSMENT_RUN_STARTED",
                workflow_step=None,
                decision="ALLOW",
                reason="Governance permitted assessment run start.",
            )
        )

        context: Mapping[str, Any] = dict(assessment_context)

        for step in steps:
            decision = self.policy_enforcer.evaluate(
                component_id=SUPERVISOR_COMPONENT_ID,
                resource=WORKFLOW_RESOURCE,
                action="EXECUTE_WORKFLOW_STEP",
            )

            if decision.decision is PolicyDecisionType.DENY:
                events.append(
                    self._event(
                        run_id=run_id,
                        sequence=len(events) + 1,
                        event_type="WORKFLOW_BLOCKED",
                        workflow_step=step,
                        decision="DENY",
                        reason=decision.reason,
                    )
                )

                return SupervisorResult(
                    run_id=run_id,
                    state=SupervisorState.STOPPED,
                    completed_steps=tuple(completed),
                    events=tuple(events),
                )

            if decision.decision is PolicyDecisionType.REQUIRE_HUMAN_APPROVAL:
                events.append(
                    self._event(
                        run_id=run_id,
                        sequence=len(events) + 1,
                        event_type="HUMAN_REVIEW_REQUIRED",
                        workflow_step=step,
                        decision="REQUIRE_HUMAN_APPROVAL",
                        reason=decision.reason,
                    )
                )

                return SupervisorResult(
                    run_id=run_id,
                    state=SupervisorState.WAITING_FOR_HUMAN,
                    completed_steps=tuple(completed),
                    events=tuple(events),
                )

            events.append(
                self._event(
                    run_id=run_id,
                    sequence=len(events) + 1,
                    event_type="WORKFLOW_STEP_STARTED",
                    workflow_step=step,
                    decision="ALLOW",
                    reason="Governance permitted workflow step.",
                )
            )

            handler = self.handlers.get(step)

            if handler is not None:
                try:
                    next_context = handler(context)
                except Exception as exc:
                    events.append(
                        self._event(
                            run_id=run_id,
                            sequence=len(events) + 1,
                            event_type="WORKFLOW_STEP_FAILED",
                            workflow_step=step,
                            decision="STOP",
                            reason=f"Workflow handler failed: {type(exc).__name__}",
                        )
                    )

                    return SupervisorResult(
                        run_id=run_id,
                        state=SupervisorState.STOPPED,
                        completed_steps=tuple(completed),
                        events=tuple(events),
                    )

                if not isinstance(next_context, Mapping):
                    raise SupervisorError(
                        f"Handler for {step.value} returned invalid context."
                    )

                context = next_context

            completed.append(step)

            events.append(
                self._event(
                    run_id=run_id,
                    sequence=len(events) + 1,
                    event_type="WORKFLOW_STEP_COMPLETED",
                    workflow_step=step,
                    decision="ALLOW",
                    reason="Workflow step completed.",
                )
            )

        self._require_allowed(
            action="COMPLETE_ASSESSMENT_RUN",
        )

        events.append(
            self._event(
                run_id=run_id,
                sequence=len(events) + 1,
                event_type="ASSESSMENT_RUN_COMPLETED",
                workflow_step=None,
                decision="ALLOW",
                reason="All approved workflow steps completed.",
            )
        )

        return SupervisorResult(
            run_id=run_id,
            state=SupervisorState.COMPLETED,
            completed_steps=tuple(completed),
            events=tuple(events),
        )

    def request_human_review(
        self,
        *,
        run_id: str,
        reason: str,
    ) -> PolicyDecision:
        """Request—not approve—a human-review transition."""

        self._require_identifier(run_id, "run_id")
        self._require_identifier(reason, "reason")

        return self.policy_enforcer.evaluate(
            component_id=SUPERVISOR_COMPONENT_ID,
            resource=WORKFLOW_RESOURCE,
            action="ROUTE_HUMAN_REVIEW",
        )

    def _require_allowed(self, *, action: str) -> None:
        decision = self.policy_enforcer.evaluate(
            component_id=SUPERVISOR_COMPONENT_ID,
            resource=WORKFLOW_RESOURCE,
            action=action,
        )

        if decision.decision is not PolicyDecisionType.ALLOW:
            raise SupervisorError(
                f"Supervisor action not permitted: {action}: "
                f"{decision.decision.value}: {decision.reason}"
            )

    @staticmethod
    def _event(
        *,
        run_id: str,
        sequence: int,
        event_type: str,
        workflow_step: WorkflowStep | None,
        decision: str,
        reason: str,
    ) -> ExecutionEvent:
        return ExecutionEvent(
            run_id=run_id,
            sequence=sequence,
            component_id=SUPERVISOR_COMPONENT_ID,
            event_type=event_type,
            workflow_step=(
                workflow_step.value
                if workflow_step is not None
                else None
            ),
            decision=decision,
            reason=reason,
        )

    @staticmethod
    def _require_identifier(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise SupervisorError(
                f"{field_name} is missing or invalid."
            )