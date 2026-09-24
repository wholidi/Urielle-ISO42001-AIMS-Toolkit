"""Derive workflow-only report status from governed v2 records."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agentic_assessment.shared_kernel.records import ReportState
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    canonical_identifier,
    require_contract,
)


def derive_report_state(
    *,
    assessment_id: str,
    findings: Sequence[Any],
    requirement_assessments: Sequence[Any],
    recorded_at: str,
) -> ReportState:
    finding_records = [require_contract("finding", item) for item in findings]
    requirement_records = [
        require_contract("requirement_assessment", item)
        for item in requirement_assessments
    ]
    if any(item["assessment_id"] != assessment_id for item in finding_records):
        raise SharedKernelError("Finding assessment_id does not match the report.")
    if any(item["assessment_id"] != assessment_id for item in requirement_records):
        raise SharedKernelError("Requirement assessment_id does not match the report.")

    requirement_index = {
        item["requirement_assessment_id"]: item for item in requirement_records
    }
    if len(requirement_index) != len(requirement_records):
        raise SharedKernelError("Duplicate requirement assessment identity.")
    finding_requirement_ids: set[str] = set()
    for finding in finding_records:
        requirement = requirement_index.get(finding["requirement_assessment_id"])
        if requirement is None:
            raise SharedKernelError("Finding references a missing requirement assessment.")
        if finding["question_id"] != requirement["question_id"]:
            raise SharedKernelError("Finding question_id does not match its requirement.")
        if finding["requirement_assessment_id"] in finding_requirement_ids:
            raise SharedKernelError("Duplicate finding for one requirement assessment.")
        finding_requirement_ids.add(finding["requirement_assessment_id"])

    pending = tuple(sorted(
        item["finding_id"]
        for item in finding_records
        if item["disposition"] == "PENDING"
    ))
    unresolved = tuple(sorted(
        item["requirement_assessment_id"]
        for item in requirement_records
        if item["outcome"] == "UNRESOLVED"
        or (
            item["outcome"] == "UNSUPPORTED"
            and item["requirement_assessment_id"] not in finding_requirement_ids
        )
    ))
    record = ReportState(
        report_id=canonical_identifier("RPT", assessment_id),
        assessment_id=assessment_id,
        status="FINAL" if not pending and not unresolved else "DRAFT",
        pending_finding_ids=pending,
        unresolved_requirement_assessment_ids=unresolved,
        recorded_at=recorded_at,
    )
    require_contract("report_state", record)
    return record
