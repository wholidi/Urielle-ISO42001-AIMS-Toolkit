"""Phase 03 lifecycle transition tests."""

from __future__ import annotations

import pytest

from agentic_assessment.shared_kernel.lifecycle import (
    initialize_lifecycle,
    transition_lifecycle,
)
from agentic_assessment.shared_kernel.validation import SharedKernelError
from tests._shared_kernel_fixtures import (
    ASSESSMENT_ID,
    EVIDENCE_ID,
    MAPPING_ID,
    SHA256,
    TIMESTAMP,
    reviewed_lifecycle,
)


def _initial():
    return initialize_lifecycle(
        assessment_id=ASSESSMENT_ID,
        mapping_id=MAPPING_ID,
        evidence_id=EVIDENCE_ID,
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
    )


def test_valid_lifecycle_transitions_preserve_identity() -> None:
    initial = _initial()
    present = transition_lifecycle(
        initial,
        target_state="FILE_PRESENT",
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
        actor_type="DETERMINISTIC_RULES",
    )
    verified = transition_lifecycle(
        present,
        target_state="INTEGRITY_VERIFIED",
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
        actor_type="DETERMINISTIC_RULES",
        sha256=SHA256,
    )
    reviewed = transition_lifecycle(
        verified,
        target_state="CONTENT_REVIEWED",
        recorded_at=TIMESTAMP,
        recorded_by="HUM-REVIEWER-001",
        actor_type="HUMAN",
        comments="Reviewed content.",
    )
    assert [initial.state, present.state, verified.state, reviewed.state] == [
        "REFERENCED", "FILE_PRESENT", "INTEGRITY_VERIFIED", "CONTENT_REVIEWED"
    ]
    assert len({item.lifecycle_id for item in (initial, present, verified, reviewed)}) == 1
    assert reviewed.sha256 == SHA256


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("REFERENCED", "INTEGRITY_VERIFIED"),
        ("REFERENCED", "CONTENT_REVIEWED"),
        ("REFERENCED", "ACCEPTED"),
        ("FILE_PRESENT", "CONTENT_REVIEWED"),
        ("INTEGRITY_VERIFIED", "ACCEPTED"),
    ],
)
def test_invalid_lifecycle_transition_fails_closed(source: str, target: str) -> None:
    records = {"REFERENCED": _initial()}
    records["FILE_PRESENT"] = transition_lifecycle(
        records["REFERENCED"], target_state="FILE_PRESENT", recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES"
    )
    records["INTEGRITY_VERIFIED"] = transition_lifecycle(
        records["FILE_PRESENT"], target_state="INTEGRITY_VERIFIED", recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES", sha256=SHA256
    )
    with pytest.raises(SharedKernelError, match="Invalid lifecycle transition"):
        transition_lifecycle(
            records[source], target_state=target, recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES", sha256=SHA256
        )


def test_regressive_transition_fails_closed() -> None:
    with pytest.raises(SharedKernelError, match="Invalid lifecycle transition"):
        transition_lifecycle(
            reviewed_lifecycle(), target_state="INTEGRITY_VERIFIED", recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES", sha256=SHA256
        )


def test_terminal_lifecycle_state_cannot_transition() -> None:
    unable = transition_lifecycle(
        _initial(), target_state="UNABLE_TO_ESTABLISH", recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES",
        comments="Evidence could not be resolved."
    )
    with pytest.raises(SharedKernelError, match="Invalid lifecycle transition"):
        transition_lifecycle(
            unable, target_state="FILE_PRESENT", recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES"
        )


def test_deterministic_actor_cannot_record_human_state() -> None:
    verified = transition_lifecycle(
        transition_lifecycle(
            _initial(), target_state="FILE_PRESENT", recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES"
        ),
        target_state="INTEGRITY_VERIFIED", recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES", sha256=SHA256
    )
    with pytest.raises(SharedKernelError, match="actor_type"):
        transition_lifecycle(
            verified, target_state="CONTENT_REVIEWED", recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES",
            comments="Automated review is prohibited."
        )


def test_integrity_transition_requires_hash() -> None:
    present = transition_lifecycle(
        _initial(), target_state="FILE_PRESENT", recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES"
    )
    with pytest.raises(SharedKernelError, match="requires an observed SHA-256"):
        transition_lifecycle(
            present, target_state="INTEGRITY_VERIFIED", recorded_at=TIMESTAMP,
            recorded_by="KERNEL.TEST", actor_type="DETERMINISTIC_RULES"
        )
