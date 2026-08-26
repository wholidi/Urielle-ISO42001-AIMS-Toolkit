"""Tests for deterministic Agentic Clause 04 finding generation."""

from __future__ import annotations

from typing import Any

import pytest

from agentic_assessment.evidence_assessor import (
    EvidenceDecision,
)
from agentic_assessment.finding_generator import (
    FindingGenerator,
    FindingGeneratorError,
)


def build_decision(
    *,
    decision: str = "NOT_EVIDENCED",
    question_id: str = "C4-Q01",
    evidence_ids: tuple[str, ...] | None = None,
    human_review_required: bool | None = None,
) -> EvidenceDecision:
    if evidence_ids is None:
        if decision in {
            "EVIDENCED",
            "PARTIALLY_EVIDENCED",
            "NOT_APPLICABLE",
        }:
            evidence_ids = (
                "Clause4_Context_Register.xlsx",
            )
        else:
            evidence_ids = ()

    if human_review_required is None:
        human_review_required = decision in {
            "PARTIALLY_EVIDENCED",
            "REQUIRES_HUMAN_JUDGEMENT",
        }

    semantic_observations: tuple[
        dict[str, Any],
        ...
    ]

    if human_review_required:
        semantic_observations = (
            {
                "observer_type": "DETERMINISTIC_RULES",
                "observation": (
                    "Human review is required."
                ),
            },
        )
    else:
        semantic_observations = ()

    return EvidenceDecision(
        schema_version="1.0.0",
        decision_id="ED-CLAUSE04-001-001",
        assessment_id="CLAUSE04-001",
        question_id=question_id,
        evidence_ids=evidence_ids,
        deterministic_checks=(
            {
                "check_id": (
                    f"CHK-{question_id}-MAP"
                ),
                "check_type": "QUESTION_MAPPING_VALID",
                "status": "PASSED",
                "observation": (
                    f"Evidence is mapped to {question_id}."
                ),
            },
        ),
        semantic_observations=semantic_observations,
        decision=decision,
        confidence=1.0,
        human_review_required=human_review_required,
        provenance={
            "created_at": (
                "2026-07-12T14:47:40+00:00"
            ),
            "created_by": "agentic.evidence_assessor",
            "generator": "DETERMINISTIC_RULES",
            "generator_version": "0.1.0",
            "source_refs": [
                "assessment:CLAUSE04-001",
                f"question:{question_id}",
            ],
        },
    )


def test_not_evidenced_generates_draft_finding() -> None:
    generator = FindingGenerator()

    findings = generator.generate(
        decisions=(
            build_decision(
                decision="NOT_EVIDENCED"
            ),
        )
    )

    assert len(findings) == 1

    finding = findings[0]

    assert finding.question_id == "C4-Q01"
    assert finding.requirement_ref == "4.1"
    assert finding.severity_preliminary == "MEDIUM"
    assert finding.human_disposition == "PENDING"
    assert finding.review_record is None


def test_partial_evidence_generates_low_preliminary_severity() -> None:
    generator = FindingGenerator()

    finding = generator.generate(
        decisions=(
            build_decision(
                decision="PARTIALLY_EVIDENCED"
            ),
        )
    )[0]

    assert finding.severity_preliminary == "LOW"
    assert finding.human_disposition == "PENDING"


def test_human_judgement_generates_review_required_finding() -> None:
    generator = FindingGenerator()

    finding = generator.generate(
        decisions=(
            build_decision(
                decision="REQUIRES_HUMAN_JUDGEMENT"
            ),
        )
    )[0]

    assert (
        finding.severity_preliminary
        == "REVIEW_REQUIRED"
    )

    assert finding.human_disposition == "PENDING"


def test_evidenced_decision_generates_no_finding() -> None:
    generator = FindingGenerator()

    findings = generator.generate(
        decisions=(
            build_decision(
                decision="EVIDENCED"
            ),
        )
    )

    assert findings == ()


def test_not_applicable_generates_no_finding() -> None:
    generator = FindingGenerator()

    findings = generator.generate(
        decisions=(
            build_decision(
                decision="NOT_APPLICABLE"
            ),
        )
    )

    assert findings == ()


def test_finding_satisfies_phase1_contract() -> None:
    generator = FindingGenerator()

    finding = generator.generate(
        decisions=(
            build_decision(
                decision="NOT_EVIDENCED"
            ),
        )
    )[0]

    generator.contract_validator.require_valid(
        contract_name="finding",
        instance=finding.to_contract(),
    )


def test_finding_references_source_decision() -> None:
    generator = FindingGenerator()

    finding = generator.generate(
        decisions=(
            build_decision(
                decision="NOT_EVIDENCED"
            ),
        )
    )[0]

    assert {
        "reference_type": "EVIDENCE_DECISION",
        "reference_id": "ED-CLAUSE04-001-001",
    } in finding.evidence_refs


def test_partial_finding_preserves_evidence_reference() -> None:
    generator = FindingGenerator()

    finding = generator.generate(
        decisions=(
            build_decision(
                decision="PARTIALLY_EVIDENCED"
            ),
        )
    )[0]

    assert {
        "reference_type": "EVIDENCE",
        "reference_id": (
            "Clause4_Context_Register.xlsx"
        ),
    } in finding.evidence_refs


def test_invalid_input_fails_closed() -> None:
    generator = FindingGenerator()

    with pytest.raises(
        FindingGeneratorError,
        match="Evidence decision is missing or invalid",
    ):
        generator.generate(
            decisions=(
                {"decision": "NOT_EVIDENCED"},  # type: ignore[arg-type]
            )
        )


def test_schema_invalid_decision_fails_closed() -> None:
    generator = FindingGenerator()

    invalid = build_decision(
        decision="PARTIALLY_EVIDENCED",
        evidence_ids=(),
    )

    with pytest.raises(
        FindingGeneratorError,
        match="failed contract validation",
    ):
        generator.generate(
            decisions=(invalid,)
        )


def test_unknown_question_mapping_fails_closed() -> None:
    generator = FindingGenerator()

    decision = build_decision(
        question_id="C4-Q99",
        decision="NOT_EVIDENCED",
    )

    with pytest.raises(
        FindingGeneratorError,
        match="No Clause 04 requirement mapping",
    ):
        generator.generate(
            decisions=(decision,)
        )


def test_finding_ids_are_deterministic() -> None:
    generator = FindingGenerator()

    decision = build_decision(
        decision="NOT_EVIDENCED"
    )

    first = generator.generate(
        decisions=(decision,)
    )

    second = generator.generate(
        decisions=(decision,)
    )

    assert (
        first[0].finding_id
        == second[0].finding_id
        == "FND-CLAUSE04-001-001"
    )


def test_finding_order_follows_adverse_decisions() -> None:
    generator = FindingGenerator()

    first = build_decision(
        question_id="C4-Q01",
        decision="NOT_EVIDENCED",
    )

    evidenced = build_decision(
        question_id="C4-Q02",
        decision="EVIDENCED",
    )

    third = build_decision(
        question_id="C4-Q03",
        decision="NOT_EVIDENCED",
    )

    findings = generator.generate(
        decisions=(
            first,
            evidenced,
            third,
        )
    )

    assert [
        finding.question_id
        for finding in findings
    ] == [
        "C4-Q01",
        "C4-Q03",
    ]

    assert [
        finding.finding_id
        for finding in findings
    ] == [
        "FND-CLAUSE04-001-001",
        "FND-CLAUSE04-001-002",
    ]