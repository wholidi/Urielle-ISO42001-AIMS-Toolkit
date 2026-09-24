"""Clause-neutral evidence lifecycle state transitions."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from agentic_assessment.shared_kernel.records import LifecycleRecord
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)

TRANSITIONS = {
    "REFERENCED": frozenset({"FILE_PRESENT", "UNABLE_TO_ESTABLISH"}),
    "FILE_PRESENT": frozenset({"INTEGRITY_VERIFIED", "UNABLE_TO_ESTABLISH"}),
    "INTEGRITY_VERIFIED": frozenset({"CONTENT_REVIEWED", "UNABLE_TO_ESTABLISH"}),
    "CONTENT_REVIEWED": frozenset({"ACCEPTED", "REJECTED"}),
    "ACCEPTED": frozenset(),
    "REJECTED": frozenset(),
    "UNABLE_TO_ESTABLISH": frozenset(),
}

HUMAN_STATES = frozenset({"CONTENT_REVIEWED", "ACCEPTED", "REJECTED"})
TERMINAL_STATES = frozenset({"ACCEPTED", "REJECTED", "UNABLE_TO_ESTABLISH"})


def lifecycle_id_for(*, assessment_id: str, mapping_id: str, evidence_id: str) -> str:
    return canonical_identifier("LCR", assessment_id, mapping_id, evidence_id)


def initialize_lifecycle(
    *,
    assessment_id: str,
    mapping_id: str,
    evidence_id: str,
    recorded_at: str,
    recorded_by: str,
) -> LifecycleRecord:
    record = LifecycleRecord(
        lifecycle_id=lifecycle_id_for(
            assessment_id=assessment_id,
            mapping_id=mapping_id,
            evidence_id=evidence_id,
        ),
        assessment_id=assessment_id,
        evidence_id=evidence_id,
        state="REFERENCED",
        recorded_at=recorded_at,
        recorded_by=recorded_by,
        actor_type="DETERMINISTIC_RULES",
    )
    require_contract("evidence_lifecycle_record", record)
    return record


def transition_lifecycle(
    current: Any,
    *,
    target_state: str,
    recorded_at: str,
    recorded_by: str,
    actor_type: str,
    sha256: str | None = None,
    comments: str | None = None,
) -> LifecycleRecord:
    """Return the next immutable state or fail without changing the input."""

    source = require_contract("evidence_lifecycle_record", current)
    source_state = source["state"]
    if target_state == source_state:
        candidate = LifecycleRecord(
            lifecycle_id=source["lifecycle_id"],
            assessment_id=source["assessment_id"],
            evidence_id=source["evidence_id"],
            state=source_state,
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type=actor_type,
            sha256=sha256 if sha256 is not None else source.get("sha256"),
            comments=comments,
        )
        if candidate.to_contract() == source:
            return candidate
        raise SharedKernelError("A lifecycle replay must be byte-for-byte identical.")

    if target_state not in TRANSITIONS.get(source_state, frozenset()):
        raise SharedKernelError(
            f"Invalid lifecycle transition: {source_state} -> {target_state}"
        )
    if (target_state in HUMAN_STATES) != (actor_type == "HUMAN"):
        raise SharedKernelError("Lifecycle actor_type is not authorized for the target state.")

    established_hash = source.get("sha256")
    if established_hash is not None and sha256 not in (None, established_hash):
        raise SharedKernelError("An established evidence hash is immutable.")
    next_hash = established_hash if established_hash is not None else sha256
    if target_state == "INTEGRITY_VERIFIED" and next_hash is None:
        raise SharedKernelError("Integrity verification requires an observed SHA-256.")

    record = LifecycleRecord(
        lifecycle_id=source["lifecycle_id"],
        assessment_id=source["assessment_id"],
        evidence_id=source["evidence_id"],
        state=target_state,
        recorded_at=recorded_at,
        recorded_by=recorded_by,
        actor_type=actor_type,
        sha256=next_hash,
        comments=comments,
    )
    require_contract("evidence_lifecycle_record", record)
    return record


def verify_evidence_integrity(
    *,
    mapping: Any,
    manifest: Any,
    evidence_root: Path | str,
    recorded_at: str,
    recorded_by: str,
) -> LifecycleRecord:
    """Establish safe presence and optional hash integrity without content review."""

    mapping_record = require_contract("evidence_mapping", mapping)
    manifest_record = require_contract("evidence_manifest", manifest)
    if mapping_record["assessment_id"] != manifest_record["assessment_id"]:
        raise SharedKernelError("Mapping and manifest assessment IDs do not match.")
    matches = [
        item for item in manifest_record["evidence_items"]
        if item["evidence_id"] == mapping_record["evidence_id"]
    ]
    if len(matches) != 1:
        raise SharedKernelError("Evidence manifest must contain one matching evidence item.")

    lifecycle = initialize_lifecycle(
        assessment_id=mapping_record["assessment_id"],
        mapping_id=mapping_record["mapping_id"],
        evidence_id=mapping_record["evidence_id"],
        recorded_at=recorded_at,
        recorded_by=recorded_by,
    )
    item = matches[0]
    root = Path(evidence_root).resolve()
    relative = Path(item["path"])
    if relative.is_absolute() or ".." in relative.parts:
        return transition_lifecycle(
            lifecycle,
            target_state="UNABLE_TO_ESTABLISH",
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type="DETERMINISTIC_RULES",
            comments="Evidence path is outside the permitted root.",
        )
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return transition_lifecycle(
            lifecycle,
            target_state="UNABLE_TO_ESTABLISH",
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type="DETERMINISTIC_RULES",
            comments="Evidence path resolves outside the permitted root.",
        )
    if not target.is_file():
        return transition_lifecycle(
            lifecycle,
            target_state="UNABLE_TO_ESTABLISH",
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type="DETERMINISTIC_RULES",
            comments="A readable regular evidence file was not established.",
        )

    present = transition_lifecycle(
        lifecycle,
        target_state="FILE_PRESENT",
        recorded_at=recorded_at,
        recorded_by=recorded_by,
        actor_type="DETERMINISTIC_RULES",
    )
    declared = item.get("declared_sha256")
    if declared is None:
        return present
    digest = hashlib.sha256()
    try:
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
    except OSError:
        return transition_lifecycle(
            present,
            target_state="UNABLE_TO_ESTABLISH",
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type="DETERMINISTIC_RULES",
            comments="The evidence file could not be read.",
        )
    observed = digest.hexdigest()
    if observed != declared:
        return transition_lifecycle(
            present,
            target_state="UNABLE_TO_ESTABLISH",
            recorded_at=recorded_at,
            recorded_by=recorded_by,
            actor_type="DETERMINISTIC_RULES",
            comments="Observed SHA-256 does not match the declared value.",
        )
    return transition_lifecycle(
        present,
        target_state="INTEGRITY_VERIFIED",
        recorded_at=recorded_at,
        recorded_by=recorded_by,
        actor_type="DETERMINISTIC_RULES",
        sha256=observed,
    )
