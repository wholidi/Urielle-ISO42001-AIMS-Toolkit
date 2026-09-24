"""Deterministic, explicitly authorized v2 execution-event construction."""

from __future__ import annotations

from agentic_assessment.shared_kernel.records import ExecutionEvent
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)

SUBJECT_PREFIXES = {
    "INTEGRITY_CHECKED": "LCR-",
    "CONTENT_REVIEW_RECORDED": "LCR-",
    "EVIDENCE_ACCEPTANCE_RECORDED": "ACC-",
    "REQUIREMENT_ASSESSED": "REQ-",
    "FINDING_RECORDED": "FND-",
    "REPORT_STATE_CHANGED": "RPT-",
}


class EventRecorder:
    """Create a contiguous event stream from caller-authorized event types.

    The authorization set is structural input for Phase 03 tests. It does not
    grant a runtime governance permission; Phase 5 must authorize the caller.
    """

    def __init__(
        self,
        *,
        assessment_id: str,
        component_id: str,
        authorized_event_types: frozenset[str],
    ) -> None:
        self.assessment_id = assessment_id
        self.component_id = component_id
        self.authorized_event_types = authorized_event_types
        self._events: list[ExecutionEvent] = []

    @property
    def events(self) -> tuple[ExecutionEvent, ...]:
        return tuple(self._events)

    def record(
        self,
        *,
        event_type: str,
        status: str,
        occurred_at: str,
        subject_id: str | None = None,
    ) -> ExecutionEvent:
        if event_type not in self.authorized_event_types:
            raise SharedKernelError("Actor/action pair is not authorized for this stream.")
        expected_prefix = SUBJECT_PREFIXES.get(event_type)
        if expected_prefix is not None and (
            subject_id is None or not subject_id.startswith(expected_prefix)
        ):
            raise SharedKernelError("Execution-event subject does not match its action.")
        if event_type == "WORKFLOW_FAILED" and status != "FAILED":
            raise SharedKernelError("WORKFLOW_FAILED events must have FAILED status.")

        sequence = len(self._events) + 1
        event = ExecutionEvent(
            event_id=canonical_identifier(
                "EVT",
                self.assessment_id,
                sequence,
                event_type,
                status,
                subject_id,
            ),
            assessment_id=self.assessment_id,
            sequence=sequence,
            component_id=self.component_id,
            event_type=event_type,
            status=status,
            occurred_at=occurred_at,
            subject_id=subject_id,
        )
        require_contract("execution_event", event)
        self._events.append(event)
        return event
