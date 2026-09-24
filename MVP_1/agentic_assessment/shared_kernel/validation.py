"""Fail-closed schema and relationship validation for shared-kernel inputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)


class SharedKernelError(RuntimeError):
    """Raised when a shared-kernel invariant cannot be established."""


def canonical_identifier(prefix: str, *parts: Any) -> str:
    """Return a stable contract-compatible identifier for governed inputs."""

    payload = json.dumps(
        parts,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest().upper()}"


def as_contract(value: Any) -> dict[str, Any]:
    """Copy a mapping or serialize an immutable shared-kernel record."""

    if isinstance(value, Mapping):
        return dict(value)
    serializer = getattr(value, "to_contract", None)
    if not callable(serializer):
        raise SharedKernelError("A governed record is missing or invalid.")
    contract = serializer()
    if not isinstance(contract, Mapping):
        raise SharedKernelError("A governed record serialized to an invalid value.")
    return dict(contract)


def require_contract(contract_name: str, value: Any) -> dict[str, Any]:
    contract = as_contract(value)
    try:
        AssessmentContractValidator().require_valid(
            contract_name=f"v2.{contract_name}",
            instance=contract,
        )
    except AssessmentContractError as exc:
        raise SharedKernelError(
            f"The {contract_name} record failed v2 contract validation."
        ) from exc
    return contract


def _unique(records: Sequence[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        identity = record[field]
        if identity in indexed:
            raise SharedKernelError(f"Duplicate {field} is prohibited: {identity}")
        indexed[identity] = record
    return indexed


def validate_linked_records(
    *,
    plan: Any,
    manifest: Any,
    mappings: Sequence[Any],
    lifecycles: Sequence[Any],
    acceptances: Sequence[Any],
) -> None:
    """Validate schema, identity and question-specific record relationships."""

    plan_record = require_contract("assessment_plan", plan)
    manifest_record = require_contract("evidence_manifest", manifest)
    mapping_records = [require_contract("evidence_mapping", item) for item in mappings]
    lifecycle_records = [
        require_contract("evidence_lifecycle_record", item) for item in lifecycles
    ]
    acceptance_records = [
        require_contract("evidence_acceptance_record", item) for item in acceptances
    ]

    assessment_id = plan_record["assessment_id"]
    if manifest_record["assessment_id"] != assessment_id:
        raise SharedKernelError("Manifest assessment_id does not match the plan.")

    evidence_items = _unique(manifest_record["evidence_items"], "evidence_id")
    mapping_index = _unique(mapping_records, "mapping_id")
    lifecycle_index = _unique(lifecycle_records, "lifecycle_id")
    _unique(acceptance_records, "acceptance_id")

    from agentic_assessment.shared_kernel.lifecycle import lifecycle_id_for

    for mapping in mapping_records:
        if mapping["assessment_id"] != assessment_id:
            raise SharedKernelError("Mapping assessment_id does not match the plan.")
        if mapping["question_id"] not in plan_record["question_ids"]:
            raise SharedKernelError("Mapping question_id is outside the assessment plan.")
        if mapping["requirement_ref"] not in plan_record["requirement_refs"]:
            raise SharedKernelError("Mapping requirement_ref is outside the assessment plan.")
        if mapping["evidence_id"] not in evidence_items:
            raise SharedKernelError("Mapping references missing evidence.")

    expected_lifecycle_ids = {
        lifecycle_id_for(
            assessment_id=mapping["assessment_id"],
            mapping_id=mapping["mapping_id"],
            evidence_id=mapping["evidence_id"],
        ): mapping
        for mapping in mapping_records
    }
    for lifecycle in lifecycle_records:
        mapping = expected_lifecycle_ids.get(lifecycle["lifecycle_id"])
        if mapping is None:
            raise SharedKernelError("Lifecycle record has no matching evidence mapping.")
        if lifecycle["assessment_id"] != assessment_id:
            raise SharedKernelError("Lifecycle assessment_id does not match the plan.")
        if lifecycle["evidence_id"] != mapping["evidence_id"]:
            raise SharedKernelError("Lifecycle evidence_id does not match its mapping.")

    for acceptance in acceptance_records:
        mapping = mapping_index.get(acceptance["mapping_id"])
        lifecycle = lifecycle_index.get(acceptance["lifecycle_id"])
        if mapping is None or lifecycle is None:
            raise SharedKernelError("Acceptance references a missing linked record.")
        fields = ("assessment_id", "question_id", "evidence_id")
        if any(acceptance[field] != mapping[field] for field in fields):
            raise SharedKernelError("Acceptance identity does not match its mapping.")
        if acceptance["assessment_id"] != lifecycle["assessment_id"]:
            raise SharedKernelError("Acceptance assessment_id does not match lifecycle.")
        if acceptance["evidence_id"] != lifecycle["evidence_id"]:
            raise SharedKernelError("Acceptance evidence_id does not match lifecycle.")
        if lifecycle["lifecycle_id"] != lifecycle_id_for(
            assessment_id=acceptance["assessment_id"],
            mapping_id=acceptance["mapping_id"],
            evidence_id=acceptance["evidence_id"],
        ):
            raise SharedKernelError("Acceptance lifecycle_id does not match its mapping path.")
        if lifecycle["state"] != acceptance["decision"]:
            raise SharedKernelError("Acceptance decision conflicts with lifecycle state.")
