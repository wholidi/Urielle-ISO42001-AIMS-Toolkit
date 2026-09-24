"""Deterministic requirement evaluation from validated linked records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agentic_assessment.shared_kernel.records import RequirementAssessment
from agentic_assessment.shared_kernel.lifecycle import lifecycle_id_for
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)


def evaluate_requirement(
    *,
    assessment_id: str,
    requirement_ref: str,
    question_id: str,
    mappings: Sequence[Any],
    lifecycles: Sequence[Any],
    acceptances: Sequence[Any],
    evaluated_at: str,
) -> RequirementAssessment:
    """Evaluate one question without interpreting evidence content."""

    mapping_records = [require_contract("evidence_mapping", item) for item in mappings]
    lifecycle_records = [
        require_contract("evidence_lifecycle_record", item) for item in lifecycles
    ]
    acceptance_records = [
        require_contract("evidence_acceptance_record", item) for item in acceptances
    ]
    mapping_index: dict[str, dict[str, Any]] = {}
    for item in mapping_records:
        if item["mapping_id"] in mapping_index:
            raise SharedKernelError("Duplicate mapping_id is prohibited.")
        mapping_index[item["mapping_id"]] = item
    lifecycle_index: dict[str, dict[str, Any]] = {}
    for item in lifecycle_records:
        if item["lifecycle_id"] in lifecycle_index:
            raise SharedKernelError("Duplicate lifecycle_id is prohibited.")
        lifecycle_index[item["lifecycle_id"]] = item
    acceptance_ids: set[str] = set()
    for acceptance in acceptance_records:
        if acceptance["acceptance_id"] in acceptance_ids:
            raise SharedKernelError("Duplicate acceptance_id is prohibited.")
        acceptance_ids.add(acceptance["acceptance_id"])
        linked_mapping = mapping_index.get(acceptance["mapping_id"])
        linked_lifecycle = lifecycle_index.get(acceptance["lifecycle_id"])
        if linked_mapping is None or linked_lifecycle is None:
            raise SharedKernelError("Acceptance references a missing linked record.")
        if any(
            acceptance[field] != linked_mapping[field]
            for field in ("assessment_id", "question_id", "evidence_id")
        ):
            raise SharedKernelError("Acceptance identity does not match its mapping.")
        if linked_lifecycle["assessment_id"] != acceptance["assessment_id"] or (
            linked_lifecycle["evidence_id"] != acceptance["evidence_id"]
        ):
            raise SharedKernelError("Acceptance identity does not match its lifecycle.")
        if linked_lifecycle["state"] != acceptance["decision"]:
            raise SharedKernelError("Acceptance decision conflicts with lifecycle state.")
        if linked_lifecycle["lifecycle_id"] != lifecycle_id_for(
            assessment_id=acceptance["assessment_id"],
            mapping_id=acceptance["mapping_id"],
            evidence_id=acceptance["evidence_id"],
        ):
            raise SharedKernelError("Acceptance lifecycle identity is invalid.")
    relevant = [
        item
        for item in mapping_records
        if item["assessment_id"] == assessment_id
        and item["question_id"] == question_id
        and item["requirement_ref"] == requirement_ref
        and item["mapping_status"] == "IN_SCOPE"
    ]
    if not relevant:
        outcome = "UNRESOLVED"
        accepted_ids: tuple[str, ...] = ()
        rationale = "No in-scope evidence mapping was established for the question."
    else:
        relevant_mapping_ids = {item["mapping_id"] for item in relevant}
        accepted = sorted(
            item["acceptance_id"]
            for item in acceptance_records
            if item["assessment_id"] == assessment_id
            and item["question_id"] == question_id
            and item["mapping_id"] in relevant_mapping_ids
            and item["decision"] == "ACCEPTED"
        )
        if accepted:
            outcome = "SUPPORTED"
            accepted_ids = tuple(accepted)
            rationale = "Question-specific human-accepted evidence supports the requirement."
        else:
            relevant_lifecycle_ids = {
                item["lifecycle_id"]
                for item in acceptance_records
                if item["mapping_id"] in relevant_mapping_ids
            }
            states = {
                item["state"]
                for item in lifecycle_records
                if item["lifecycle_id"] in relevant_lifecycle_ids
            }
            rejected_mappings = {
                item["mapping_id"]
                for item in acceptance_records
                if item["mapping_id"] in relevant_mapping_ids
                and item["decision"] == "REJECTED"
            }
            if rejected_mappings == relevant_mapping_ids and states <= {"REJECTED"}:
                outcome = "UNSUPPORTED"
                accepted_ids = ()
                rationale = "All in-scope evidence mappings were explicitly rejected."
            else:
                outcome = "UNRESOLVED"
                accepted_ids = ()
                rationale = "Question-specific human acceptance was not established."

    record = RequirementAssessment(
        requirement_assessment_id=canonical_identifier(
            "REQ", assessment_id, requirement_ref, question_id
        ),
        assessment_id=assessment_id,
        requirement_ref=requirement_ref,
        question_id=question_id,
        outcome=outcome,
        accepted_evidence_acceptance_ids=accepted_ids,
        rationale=rationale,
        evaluated_at=evaluated_at,
    )
    require_contract("requirement_assessment", record)
    return record
