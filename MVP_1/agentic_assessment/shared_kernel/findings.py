"""Deterministic draft finding derivation from requirement assessments."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agentic_assessment.shared_kernel.records import FindingRecord
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)


def derive_findings(
    assessments: Sequence[Any],
    *,
    existing_findings: Sequence[Any] = (),
) -> tuple[FindingRecord, ...]:
    """Return one stable draft finding per unsupported or unresolved result."""

    requirements = [require_contract("requirement_assessment", item) for item in assessments]
    existing = [require_contract("finding", item) for item in existing_findings]
    existing_by_id: dict[str, dict[str, Any]] = {}
    for item in existing:
        prior = existing_by_id.get(item["finding_id"])
        if prior is not None and prior != item:
            raise SharedKernelError("Conflicting duplicate finding identity.")
        existing_by_id[item["finding_id"]] = item

    results: list[FindingRecord] = []
    seen_keys: set[tuple[str, str]] = set()
    ordered = sorted(
        requirements,
        key=lambda item: (
            item["question_id"],
            item["requirement_ref"],
            item["requirement_assessment_id"],
        ),
    )
    for requirement in ordered:
        if requirement["outcome"] in {"SUPPORTED", "NOT_APPLICABLE"}:
            continue
        key = (requirement["assessment_id"], requirement["requirement_assessment_id"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        finding_id = canonical_identifier(
            "FND",
            requirement["schema_version"],
            requirement["assessment_id"],
            requirement["requirement_assessment_id"],
            requirement["requirement_ref"],
            requirement["question_id"],
            requirement["outcome"],
        )
        candidate = FindingRecord(
            finding_id=finding_id,
            assessment_id=requirement["assessment_id"],
            requirement_assessment_id=requirement["requirement_assessment_id"],
            question_id=requirement["question_id"],
            status="DRAFT",
            disposition="PENDING",
            condition=(
                f"Requirement assessment outcome is {requirement['outcome']}."
            ),
            criteria=(
                f"Requirement {requirement['requirement_ref']} requires a resolved, "
                "question-specific assessment basis."
            ),
            created_at=requirement["evaluated_at"],
        )
        contract = require_contract("finding", candidate)
        prior = existing_by_id.get(finding_id)
        if prior is not None and prior != contract:
            raise SharedKernelError("Existing finding conflicts with deterministic output.")
        results.append(candidate)
    return tuple(results)
