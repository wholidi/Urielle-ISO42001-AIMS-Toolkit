"""Small contract-valid fixtures for focused shared-kernel tests."""

from __future__ import annotations

from agentic_assessment.shared_kernel.acceptance import record_acceptance
from agentic_assessment.shared_kernel.lifecycle import (
    initialize_lifecycle,
    transition_lifecycle,
)

ASSESSMENT_ID = "ASM-PHASE03-001"
QUESTION_ID = "Q-CONTROL-001"
REQUIREMENT_REF = "1.1"
MAPPING_ID = "MAP-CONTROL-001"
EVIDENCE_ID = "EVD-CONTROL-001"
TIMESTAMP = "2026-09-16T08:00:00Z"
SHA256 = "a" * 64


def plan(**changes):
    value = {
        "schema_version": "2.0.0",
        "assessment_id": ASSESSMENT_ID,
        "scope": "Clause-neutral shared-kernel test",
        "requirement_refs": [REQUIREMENT_REF],
        "question_ids": [QUESTION_ID],
        "plan_status": "APPROVED",
        "created_at": TIMESTAMP,
        "created_by": "TEST.OPERATOR",
    }
    value.update(changes)
    return value


def manifest(**changes):
    value = {
        "schema_version": "2.0.0",
        "assessment_id": ASSESSMENT_ID,
        "evidence_items": [
            {
                "evidence_id": EVIDENCE_ID,
                "path": "evidence/control.txt",
                "media_type": "text/plain",
                "declared_sha256": SHA256,
            }
        ],
    }
    value.update(changes)
    return value


def mapping(**changes):
    value = {
        "schema_version": "2.0.0",
        "mapping_id": MAPPING_ID,
        "assessment_id": ASSESSMENT_ID,
        "question_id": QUESTION_ID,
        "requirement_ref": REQUIREMENT_REF,
        "evidence_id": EVIDENCE_ID,
        "mapping_status": "IN_SCOPE",
        "created_at": TIMESTAMP,
    }
    value.update(changes)
    return value


def reviewed_lifecycle(mapping_record=None):
    mapping_record = mapping_record or mapping()
    record = initialize_lifecycle(
        assessment_id=mapping_record["assessment_id"],
        mapping_id=mapping_record["mapping_id"],
        evidence_id=mapping_record["evidence_id"],
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
    )
    record = transition_lifecycle(
        record,
        target_state="FILE_PRESENT",
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
        actor_type="DETERMINISTIC_RULES",
    )
    record = transition_lifecycle(
        record,
        target_state="INTEGRITY_VERIFIED",
        recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST",
        actor_type="DETERMINISTIC_RULES",
        sha256=SHA256,
    )
    return transition_lifecycle(
        record,
        target_state="CONTENT_REVIEWED",
        recorded_at=TIMESTAMP,
        recorded_by="HUM-REVIEWER-001",
        actor_type="HUMAN",
        comments="Content was reviewed for this evidence mapping.",
    )


def accepted_records(mapping_record=None):
    mapping_record = mapping_record or mapping()
    return record_acceptance(
        mapping=mapping_record,
        lifecycle=reviewed_lifecycle(mapping_record),
        decision="ACCEPTED",
        reviewer_id="HUM-REVIEWER-001",
        decided_at=TIMESTAMP,
        rationale="The reviewed content is sufficient for this question.",
    )
