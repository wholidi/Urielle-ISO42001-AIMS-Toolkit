"""Question-specific recording of externally supplied human acceptance."""

from __future__ import annotations

from typing import Any

from agentic_assessment.shared_kernel.lifecycle import lifecycle_id_for, transition_lifecycle
from agentic_assessment.shared_kernel.records import AcceptanceRecord, LifecycleRecord
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)


def acceptance_id_for(*, assessment_id: str, mapping_id: str, evidence_id: str) -> str:
    return canonical_identifier("ACC", assessment_id, mapping_id, evidence_id)


def record_acceptance(
    *,
    mapping: Any,
    lifecycle: Any,
    decision: str,
    reviewer_id: str,
    decided_at: str,
    rationale: str,
) -> tuple[LifecycleRecord, AcceptanceRecord]:
    """Atomically record a human decision without inferring it from evidence."""

    mapping_record = require_contract("evidence_mapping", mapping)
    lifecycle_record = require_contract("evidence_lifecycle_record", lifecycle)
    if mapping_record["assessment_id"] != lifecycle_record["assessment_id"]:
        raise SharedKernelError("Mapping and lifecycle assessment IDs do not match.")
    if mapping_record["evidence_id"] != lifecycle_record["evidence_id"]:
        raise SharedKernelError("Mapping and lifecycle evidence IDs do not match.")
    expected_lifecycle_id = lifecycle_id_for(
        assessment_id=mapping_record["assessment_id"],
        mapping_id=mapping_record["mapping_id"],
        evidence_id=mapping_record["evidence_id"],
    )
    if lifecycle_record["lifecycle_id"] != expected_lifecycle_id:
        raise SharedKernelError("Lifecycle identity does not match the evidence mapping.")
    if lifecycle_record["state"] != "CONTENT_REVIEWED":
        raise SharedKernelError("Acceptance requires CONTENT_REVIEWED evidence.")
    if decision not in {"ACCEPTED", "REJECTED"}:
        raise SharedKernelError("Human acceptance decision is invalid.")

    terminal = transition_lifecycle(
        lifecycle_record,
        target_state=decision,
        recorded_at=decided_at,
        recorded_by=reviewer_id,
        actor_type="HUMAN",
        comments=rationale,
    )
    acceptance = AcceptanceRecord(
        acceptance_id=acceptance_id_for(
            assessment_id=mapping_record["assessment_id"],
            mapping_id=mapping_record["mapping_id"],
            evidence_id=mapping_record["evidence_id"],
        ),
        assessment_id=mapping_record["assessment_id"],
        question_id=mapping_record["question_id"],
        mapping_id=mapping_record["mapping_id"],
        evidence_id=mapping_record["evidence_id"],
        lifecycle_id=terminal.lifecycle_id,
        decision=decision,
        reviewer_id=reviewer_id,
        decided_at=decided_at,
        rationale=rationale,
    )
    require_contract("evidence_acceptance_record", acceptance)
    return terminal, acceptance
