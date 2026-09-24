"""Phase 03 deterministic execution-event tests."""

from __future__ import annotations

import pytest

from agentic_assessment.shared_kernel.events import EventRecorder
from agentic_assessment.shared_kernel.validation import SharedKernelError
from tests._shared_kernel_fixtures import ASSESSMENT_ID, TIMESTAMP

ALLOWED = frozenset({"REQUIREMENT_ASSESSED", "FINDING_RECORDED", "WORKFLOW_FAILED"})


def _recorder() -> EventRecorder:
    return EventRecorder(
        assessment_id=ASSESSMENT_ID,
        component_id="phase03.test_driver",
        authorized_event_types=ALLOWED,
    )


def test_events_have_stable_order_and_contiguous_sequence() -> None:
    recorder = _recorder()
    recorder.record(
        event_type="REQUIREMENT_ASSESSED", status="SUCCEEDED",
        occurred_at=TIMESTAMP, subject_id="REQ-" + "A" * 64
    )
    recorder.record(
        event_type="FINDING_RECORDED", status="SUCCEEDED",
        occurred_at=TIMESTAMP, subject_id="FND-" + "B" * 64
    )
    assert [item.sequence for item in recorder.events] == [1, 2]
    assert [item.event_type for item in recorder.events] == [
        "REQUIREMENT_ASSESSED", "FINDING_RECORDED"
    ]


def test_unknown_actor_action_fails_closed() -> None:
    with pytest.raises(SharedKernelError, match="not authorized"):
        _recorder().record(
            event_type="REPORT_STATE_CHANGED", status="SUCCEEDED",
            occurred_at=TIMESTAMP, subject_id="RPT-" + "A" * 64
        )


def test_subject_action_mismatch_fails_closed() -> None:
    with pytest.raises(SharedKernelError, match="subject"):
        _recorder().record(
            event_type="FINDING_RECORDED", status="SUCCEEDED",
            occurred_at=TIMESTAMP, subject_id="REQ-" + "A" * 64
        )


def test_blocked_and_failed_operations_emit_no_success_output() -> None:
    recorder = _recorder()
    blocked = recorder.record(
        event_type="REQUIREMENT_ASSESSED", status="BLOCKED",
        occurred_at=TIMESTAMP, subject_id="REQ-" + "A" * 64
    )
    failed = recorder.record(
        event_type="WORKFLOW_FAILED", status="FAILED",
        occurred_at=TIMESTAMP, subject_id="REQ-" + "A" * 64
    )
    assert blocked.status == "BLOCKED"
    assert failed.status == "FAILED"
    assert not any(item.status == "SUCCEEDED" for item in recorder.events)


def test_event_identity_does_not_depend_on_timestamp() -> None:
    first = _recorder().record(
        event_type="REQUIREMENT_ASSESSED", status="SUCCEEDED",
        occurred_at="2026-09-16T08:00:00Z", subject_id="REQ-" + "A" * 64
    )
    second = _recorder().record(
        event_type="REQUIREMENT_ASSESSED", status="SUCCEEDED",
        occurred_at="2026-09-16T09:00:00Z", subject_id="REQ-" + "A" * 64
    )
    assert first.event_id == second.event_id
    assert first.occurred_at != second.occurred_at


def test_repeated_event_stream_is_identical_with_fixed_timestamp() -> None:
    def build():
        recorder = _recorder()
        recorder.record(
            event_type="REQUIREMENT_ASSESSED", status="SUCCEEDED",
            occurred_at=TIMESTAMP, subject_id="REQ-" + "A" * 64
        )
        return recorder.events

    assert build() == build()
