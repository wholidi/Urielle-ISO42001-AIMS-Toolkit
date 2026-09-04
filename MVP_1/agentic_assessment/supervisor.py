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

from datetime import datetime, timezone

from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)

SUPERVISOR_COMPONENT_ID = "agentic.supervisor"
WORKFLOW_RESOURCE = "AGENTIC_ASSESSMENT_WORKFLOW"
SUPERVISOR_VERSION = "0.3.0"

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
    """Schema-bound immutable Agentic Clause 04 execution event."""

    schema_version: str
    event_id: str
    timestamp: str
    assessment_id: str
    correlation_id: str
    component_id: str
    component_version: str
    workflow_state: str
    event_status: str
    step: str
    action: str
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    result: str | None
    policy_decision: str
    human_review_required: bool
    duration_ms: int
    error: Mapping[str, Any] | None
    provenance: Mapping[str, Any]

    def to_contract(self) -> dict[str, Any]:
        """Serialize exactly to the Phase-1 execution-event contract."""

        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "assessment_id": self.assessment_id,
            "correlation_id": self.correlation_id,
            "component_id": self.component_id,
            "component_version": self.component_version,
            "workflow_state": self.workflow_state,
            "event_status": self.event_status,
            "step": self.step,
            "action": self.action,
            "input_refs": list(self.input_refs),
            "output_refs": list(self.output_refs),
            "result": self.result,
            "policy_decision": self.policy_decision,
            "human_review_required": self.human_review_required,
            "duration_ms": self.duration_ms,
            "error": (
                dict(self.error)
                if self.error is not None
                else None
            ),
            "provenance": dict(self.provenance),
        }

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
        contract_validator: AssessmentContractValidator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.policy_enforcer = policy_enforcer
        self.handlers = dict(handlers or {})
        self.contract_validator = (
            contract_validator
            if contract_validator is not None
            else AssessmentContractValidator()
        )
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run(
        self,
        *,
        run_id: str,
        assessment_id: str,
        assessment_context: Mapping[str, Any],
        steps: Sequence[WorkflowStep] = WORKFLOW_SEQUENCE,
    ) -> SupervisorResult:
        """Execute approved workflow steps sequentially."""

        self._require_identifier(run_id, "run_id")
        self._require_identifier(
            assessment_id,
            "assessment_id",
    )

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
                assessment_id=assessment_id,
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
                        assessment_id=assessment_id,
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
                        assessment_id=assessment_id,
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
                    assessment_id=assessment_id,
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
                            assessment_id=assessment_id,
                            sequence=len(events) + 1,
                            event_type="WORKFLOW_STEP_FAILED",
                            workflow_step=step,
                            decision="STOP",
                            reason=(
                                f"Workflow handler failed: "
                                f"{type(exc).__name__}"
                            ),
                            error={
                                "error_type": type(exc).__name__,
                                "message": (
                                    "Workflow handler execution failed."
                                ),
                                "retryable": False,
                            },
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
                    assessment_id=assessment_id,
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
                assessment_id=assessment_id,
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

    def _event(
        self,
        *,
        run_id: str,
        assessment_id: str,
        sequence: int,
        event_type: str,
        workflow_step: WorkflowStep | None,
        decision: str,
        reason: str,
        error: Mapping[str, Any] | None = None,
    ) -> ExecutionEvent:
        """Create and validate one execution event before emission."""

        timestamp = self.clock().astimezone(timezone.utc).isoformat()

        event_status = self._event_status(event_type)

        workflow_state = self._workflow_state(
            event_type=event_type,
            workflow_step=workflow_step,
        )

        policy_decision = self._policy_decision(decision)

        event = ExecutionEvent(
            schema_version="1.0.0",
            event_id=f"EVT-{run_id}-{sequence:04d}",
            timestamp=timestamp,
            assessment_id=assessment_id,
            correlation_id=run_id,
            component_id=SUPERVISOR_COMPONENT_ID,
            component_version=SUPERVISOR_VERSION,
            workflow_state=workflow_state,
            event_status=event_status,
            step=(
                workflow_step.value
                if workflow_step is not None
                else "SUPERVISOR"
            ),
            action=event_type,
            input_refs=(f"assessment:{assessment_id}",),
            output_refs=(),
            result=reason,
            policy_decision=policy_decision,
            human_review_required=(
                event_status == "AWAITING_HUMAN_REVIEW"
            ),
            duration_ms=0,
            error=error,
            provenance={
                "created_at": timestamp,
                "created_by": SUPERVISOR_COMPONENT_ID,
                "generator": "DETERMINISTIC_RULES",
                "generator_version": SUPERVISOR_VERSION,
                "source_refs": [
                    f"assessment:{assessment_id}",
                    f"run:{run_id}",
                ],
            },
        )

        try:
            self.contract_validator.require_valid(
                contract_name="execution_event",
                instance=event.to_contract(),
            )

        except AssessmentContractError as exc:
            raise SupervisorError(
                "Execution event failed contract validation."
            ) from exc

        return event

    @staticmethod
    def _require_identifier(value: Any, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise SupervisorError(
                f"{field_name} is missing or invalid."
            )

    @staticmethod
    def _event_status(event_type: str) -> str:
        mapping = {
            "ASSESSMENT_RUN_STARTED": "STARTED",
            "WORKFLOW_STEP_STARTED": "STARTED",
            "WORKFLOW_STEP_COMPLETED": "SUCCEEDED",
            "WORKFLOW_STEP_FAILED": "FAILED",
            "WORKFLOW_BLOCKED": "BLOCKED",
            "HUMAN_REVIEW_REQUIRED": "AWAITING_HUMAN_REVIEW",
            "ASSESSMENT_RUN_COMPLETED": "SUCCEEDED",
    }

        try:
            return mapping[event_type]
        except KeyError as exc:
            raise SupervisorError(
                f"Unknown execution event type: {event_type}"
            ) from exc


    @staticmethod
    def _policy_decision(decision: str) -> str:
        mapping = {
            "ALLOW": "ALLOWED",
            "DENY": "DENIED",
            "REQUIRE_HUMAN_APPROVAL": "NOT_APPLICABLE",
            "STOP": "NOT_APPLICABLE",
        }

        try:
            return mapping[decision]
        except KeyError as exc:
            raise SupervisorError(
                f"Unknown policy decision: {decision}"
            ) from exc


    @staticmethod
    def _workflow_state(
        *,
        event_type: str,
        workflow_step: WorkflowStep | None,
    ) -> str:
        if event_type == "ASSESSMENT_RUN_STARTED":
            return "INITIALISED"

        if event_type == "ASSESSMENT_RUN_COMPLETED":
            return "COMPLETED"

        if event_type == "WORKFLOW_STEP_FAILED":
            return "FAILED"

        if event_type == "WORKFLOW_BLOCKED":
            return "FAILED"

        if event_type == "HUMAN_REVIEW_REQUIRED":
            return "REVIEW_PENDING"

        mapping = {
            WorkflowStep.ASSESSMENT_PLANNING:
                "SCOPE_PENDING",

            WorkflowStep.QUESTION_SELECTION:
                "VALIDATING",

            WorkflowStep.CLAUSE_04_EXECUTION:
                "VALIDATING",

            WorkflowStep.EVIDENCE_ASSESSMENT:
                "ASSESSING_EVIDENCE",

            WorkflowStep.FINDING_GENERATION:
                "GENERATING_FINDINGS",

            WorkflowStep.HUMAN_REVIEW_DECISION:
                "REVIEW_PENDING",

            WorkflowStep.REPORT_GENERATION:
                "REPORT_DRAFTED",
        }

        if workflow_step not in mapping:
            raise SupervisorError(
                "Unable to derive workflow state."
            )

        return mapping[workflow_step]
