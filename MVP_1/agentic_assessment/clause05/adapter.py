"""Thin Clause 05 compatibility boundary into the P02/P03 governed interfaces."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from agentic_assessment.shared_kernel.records import RequirementAssessment
from agentic_assessment.shared_kernel.requirements import evaluate_requirement
from agentic_assessment.shared_kernel.validation import (
    SharedKernelError,
    as_contract,
    canonical_identifier,
    require_contract,
)

from .config import load_evidence_map, load_question_bank
from .validation import Clause05ConfigError, validate_clause05_configuration


def source_evidence_id(source_artifact_id: str) -> str:
    return f"EVD-{source_artifact_id}"


def _mapping_id_for(
    *,
    assessment_id: str,
    question_id: str,
    requirement_ref: str,
    evidence_id: str,
) -> str:
    return canonical_identifier(
        "MAP",
        assessment_id,
        question_id,
        requirement_ref,
        evidence_id,
    )


def build_evidence_mappings(
    *,
    assessment_id: str,
    created_at: str,
    mapping_status: str | None = None,
    question_bank: Mapping[str, Any] | None = None,
    evidence_map: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    qb = dict(load_question_bank() if question_bank is None else question_bank)
    em = dict(load_evidence_map() if evidence_map is None else evidence_map)
    validate_clause05_configuration(qb, em)
    if mapping_status not in {None, "PROPOSED", "IN_SCOPE", "OUT_OF_SCOPE"}:
        raise ValueError("Invalid v2 evidence mapping status.")

    result: list[dict[str, Any]] = []
    for source in sorted(
        em["mappings"],
        key=lambda item: (item["question_id"], item["evidence_id"], item["mapping_id"]),
    ):
        evidence_id = source_evidence_id(source["evidence_id"])
        record = {
            "schema_version": "2.0.0",
            "mapping_id": _mapping_id_for(
                assessment_id=assessment_id,
                question_id=source["question_id"],
                requirement_ref=source["clause_ref"],
                evidence_id=evidence_id,
            ),
            "assessment_id": assessment_id,
            "question_id": source["question_id"],
            "requirement_ref": source["clause_ref"],
            "evidence_id": evidence_id,
            "mapping_status": (
                mapping_status
                if mapping_status is not None
                else (
                    "PROPOSED"
                    if source["combination_rule"] == "CONDITIONAL"
                    else "IN_SCOPE"
                )
            ),
            "created_at": created_at,
        }
        result.append(require_contract("evidence_mapping", record))
    return result


def _override_requirement_result(
    kernel_result: Any,
    *,
    outcome: str,
    rationale: str,
) -> RequirementAssessment:
    base = as_contract(kernel_result)
    record = RequirementAssessment(
        requirement_assessment_id=base["requirement_assessment_id"],
        assessment_id=base["assessment_id"],
        requirement_ref=base["requirement_ref"],
        question_id=base["question_id"],
        outcome=outcome,
        accepted_evidence_acceptance_ids=(),
        rationale=rationale,
        evaluated_at=base["evaluated_at"],
    )
    require_contract("requirement_assessment", record)
    return record


def evaluate_clause05_question(
    *,
    assessment_id: str,
    question_id: str,
    mappings: Sequence[Any],
    lifecycles: Sequence[Any],
    acceptances: Sequence[Any],
    evaluated_at: str,
    question_bank: Mapping[str, Any] | None = None,
    evidence_map: Mapping[str, Any] | None = None,
) -> RequirementAssessment:
    """Evaluate one Clause 05 atomic question using P03 validation plus P04 combination rules."""

    qb = dict(load_question_bank() if question_bank is None else question_bank)
    em = dict(load_evidence_map() if evidence_map is None else evidence_map)
    validate_clause05_configuration(qb, em)

    questions = {item["question_id"]: item for item in qb["questions"]}
    question = questions.get(question_id)
    if question is None:
        raise Clause05ConfigError("Unknown Clause 05 question_id.")

    source_mappings = [
        item for item in em["mappings"] if item["question_id"] == question_id
    ]
    if not source_mappings:
        raise Clause05ConfigError("Question has no configured evidence mapping.")

    requirement_ref = question["requirement_ref"]
    kernel_result = evaluate_requirement(
        assessment_id=assessment_id,
        requirement_ref=requirement_ref,
        question_id=question_id,
        mappings=mappings,
        lifecycles=lifecycles,
        acceptances=acceptances,
        evaluated_at=evaluated_at,
    )

    mapping_records = [require_contract("evidence_mapping", item) for item in mappings]
    acceptance_records = [
        require_contract("evidence_acceptance_record", item) for item in acceptances
    ]

    expected: dict[str, dict[str, Any]] = {}
    for source in source_mappings:
        evidence_id = source_evidence_id(source["evidence_id"])
        mapping_id = _mapping_id_for(
            assessment_id=assessment_id,
            question_id=question_id,
            requirement_ref=requirement_ref,
            evidence_id=evidence_id,
        )
        expected[mapping_id] = source

    for item in mapping_records:
        source = expected.get(item["mapping_id"])
        if source is None:
            continue
        expected_evidence_id = source_evidence_id(source["evidence_id"])
        if (
            item["assessment_id"] != assessment_id
            or item["question_id"] != question_id
            or item["requirement_ref"] != requirement_ref
            or item["evidence_id"] != expected_evidence_id
        ):
            raise SharedKernelError(
                "Clause 05 runtime mapping does not match its configured question, "
                "requirement, mapping, and source identity."
            )

    question_records = [
        item
        for item in mapping_records
        if item["assessment_id"] == assessment_id
        and item["question_id"] == question_id
        and item["requirement_ref"] == requirement_ref
    ]
    unknown = sorted(
        item["mapping_id"]
        for item in question_records
        if item["mapping_id"] not in expected
    )
    if unknown:
        raise SharedKernelError(
            "Clause 05 evaluation received an unconfigured evidence mapping."
        )

    in_scope = {
        item["mapping_id"]: item
        for item in question_records
        if item["mapping_id"] in expected and item["mapping_status"] == "IN_SCOPE"
    }

    decisions: dict[str, str] = {}
    for acceptance in acceptance_records:
        mapping_id = acceptance["mapping_id"]
        if mapping_id not in expected:
            continue
        if mapping_id not in in_scope:
            raise SharedKernelError(
                "Acceptance cannot support a Clause 05 mapping that is not IN_SCOPE."
            )
        if mapping_id in decisions:
            raise SharedKernelError(
                "Multiple acceptance records for one Clause 05 mapping are prohibited."
            )
        decisions[mapping_id] = acceptance["decision"]

    expected_ids = set(expected)
    accepted_ids = {mid for mid, decision in decisions.items() if decision == "ACCEPTED"}
    rejected_ids = {mid for mid, decision in decisions.items() if decision == "REJECTED"}
    rule = source_mappings[0]["combination_rule"]

    if rule == "ALL_OF":
        if expected_ids and expected_ids <= accepted_ids:
            if as_contract(kernel_result)["outcome"] != "SUPPORTED":
                raise SharedKernelError("P03 kernel result conflicts with ALL_OF acceptance state.")
            return kernel_result
        if rejected_ids:
            return _override_requirement_result(
                kernel_result,
                outcome="UNSUPPORTED",
                rationale="At least one required ALL_OF evidence mapping was explicitly rejected.",
            )
        return _override_requirement_result(
            kernel_result,
            outcome="UNRESOLVED",
            rationale="Not all required ALL_OF evidence mappings have explicit human acceptance.",
        )

    if rule in {"ANY_OF", "CONDITIONAL"}:
        if accepted_ids:
            if as_contract(kernel_result)["outcome"] != "SUPPORTED":
                raise SharedKernelError("P03 kernel result conflicts with accepted evidence state.")
            return kernel_result
        if expected_ids and expected_ids <= rejected_ids and expected_ids <= set(in_scope):
            return _override_requirement_result(
                kernel_result,
                outcome="UNSUPPORTED",
                rationale=(
                    "All configured in-scope evidence mappings were explicitly rejected."
                    if rule == "ANY_OF"
                    else "All configured in-scope conditional evidence mappings were explicitly rejected."
                ),
            )
        return _override_requirement_result(
            kernel_result,
            outcome="UNRESOLVED",
            rationale=(
                "No configured ANY_OF evidence mapping has explicit human acceptance."
                if rule == "ANY_OF"
                else "Conditional applicability or question-specific human acceptance is not established."
            ),
        )

    raise Clause05ConfigError("Unsupported Clause 05 combination rule.")
