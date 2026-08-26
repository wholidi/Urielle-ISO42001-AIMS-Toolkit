"""Tests for deterministic Agentic Clause 04 report generation."""

from __future__ import annotations

import pytest

from agentic_assessment.clause04_adapter import (
    Clause04AssessmentResult,
)
from agentic_assessment.evidence_assessor import (
    EvidenceDecision,
)
from agentic_assessment.finding_generator import (
    FindingGenerator,
)
from agentic_assessment.human_review import (
    HumanReviewService,
)
from agentic_assessment.report_generator import (
    ReportGenerator,
    ReportGeneratorError,
)


def build_clause04_result() -> Clause04AssessmentResult:
    return Clause04AssessmentResult(
        assessment_id="CLAUSE04-001",
        session_id="CLAUSE4-TEST-001",
        status="COMPLETED",
        score=92.5,
        evidence_records=(),
        gaps=(),
        source_result={},
    )


def build_decision(
    *,
    decision: str = "NOT_EVIDENCED",
) -> EvidenceDecision:
    evidence_ids: tuple[str, ...]

    if decision in {
        "EVIDENCED",
        "PARTIALLY_EVIDENCED",
    }:
        evidence_ids = (
            "Clause4_Context_Register.xlsx",
        )
    else:
        evidence_ids = ()

    human_review_required = (
        decision
        in {
            "PARTIALLY_EVIDENCED",
            "REQUIRES_HUMAN_JUDGEMENT",
        }
    )

    semantic_observations = (
        (
            {
                "observer_type": "DETERMINISTIC_RULES",
                "observation": "Human review required.",
            },
        )
        if human_review_required
        else ()
    )

    return EvidenceDecision(
        schema_version="1.0.0",
        decision_id="ED-CLAUSE04-001-001",
        assessment_id="CLAUSE04-001",
        question_id="C4-Q01",
        evidence_ids=evidence_ids,
        deterministic_checks=(
            {
                "check_id": "CHK-C4-Q01-MAP",
                "check_type": "QUESTION_MAPPING_VALID",
                "status": "PASSED",
                "observation": (
                    "Evidence is mapped to C4-Q01."
                ),
            },
        ),
        semantic_observations=semantic_observations,
        decision=decision,
        confidence=1.0,
        human_review_required=human_review_required,
        provenance={
            "created_at": "2026-07-12T14:47:40+00:00",
            "created_by": "agentic.evidence_assessor",
            "generator": "DETERMINISTIC_RULES",
            "generator_version": "0.1.0",
            "source_refs": [
                "assessment:CLAUSE04-001",
                "question:C4-Q01",
            ],
        },
    )


def build_pending_finding():
    decision = build_decision(
        decision="NOT_EVIDENCED"
    )

    return FindingGenerator().generate(
        decisions=(decision,)
    )[0]


def build_reviewed_finding():
    pending = build_pending_finding()

    return HumanReviewService().review(
        finding=pending,
        reviewer_id="reviewer-001",
        disposition="ACCEPTED",
    )


def test_reviewed_findings_produce_final_report() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(),
        ),
        findings=(
            build_reviewed_finding(),
        ),
    )

    assert report.report_status == "FINAL"
    assert report.pending_finding_count == 0
    assert report.accepted_finding_count == 1


def test_pending_finding_produces_draft_report() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(),
        ),
        findings=(
            build_pending_finding(),
        ),
    )

    assert report.report_status == "DRAFT"
    assert report.pending_finding_count == 1


def test_report_preserves_readiness_score() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(),
        findings=(),
    )

    assert report.readiness_score == 92.5


def test_report_contains_assessment_identity() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(),
        findings=(),
    )

    assert report.assessment_id == "CLAUSE04-001"
    assert report.session_id == "CLAUSE4-TEST-001"


def test_markdown_contains_governance_disclaimer() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(),
        findings=(),
    )

    assert (
        "not a certification decision"
        in report.markdown
    )


def test_markdown_contains_evidence_decision() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(),
        ),
        findings=(),
    )

    assert "ED-CLAUSE04-001-001" in report.markdown
    assert "NOT_EVIDENCED" in report.markdown


def test_markdown_contains_reviewed_finding() -> None:
    generator = ReportGenerator()

    finding = build_reviewed_finding()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(),
        ),
        findings=(finding,),
    )

    assert finding.finding_id in report.markdown
    assert "ACCEPTED" in report.markdown
    assert "reviewer-001" in report.markdown


def test_report_does_not_modify_inputs() -> None:
    generator = ReportGenerator()

    clause04_result = build_clause04_result()
    decision = build_decision()
    finding = build_reviewed_finding()

    original_disposition = (
        finding.human_disposition
    )

    generator.generate(
        clause04_result=clause04_result,
        evidence_decisions=(decision,),
        findings=(finding,),
    )

    assert (
        finding.human_disposition
        == original_disposition
    )


def test_incomplete_clause04_result_fails_closed() -> None:
    generator = ReportGenerator()

    incomplete = Clause04AssessmentResult(
        assessment_id="CLAUSE04-001",
        session_id="CLAUSE4-TEST-001",
        status="FAILED",
        score=92.5,
        evidence_records=(),
        gaps=(),
        source_result={},
    )

    with pytest.raises(
        ReportGeneratorError,
        match="not completed",
    ):
        generator.generate(
            clause04_result=incomplete,
            evidence_decisions=(),
            findings=(),
        )


def test_decision_assessment_mismatch_fails_closed() -> None:
    generator = ReportGenerator()

    decision = build_decision()

    mismatched = EvidenceDecision(
        **{
            **decision.__dict__,
            "assessment_id": "CLAUSE04-999",
        }
    )

    with pytest.raises(
        ReportGeneratorError,
        match="assessment_id mismatch",
    ):
        generator.generate(
            clause04_result=build_clause04_result(),
            evidence_decisions=(mismatched,),
            findings=(),
        )


def test_finding_assessment_mismatch_fails_closed() -> None:
    generator = ReportGenerator()

    finding = build_pending_finding()

    mismatched = type(finding)(
        **{
            **finding.__dict__,
            "assessment_id": "CLAUSE04-999",
        }
    )

    with pytest.raises(
        ReportGeneratorError,
        match="assessment_id mismatch",
    ):
        generator.generate(
            clause04_result=build_clause04_result(),
            evidence_decisions=(),
            findings=(mismatched,),
        )


def test_no_findings_can_still_produce_final_report() -> None:
    generator = ReportGenerator()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(
                decision="EVIDENCED"
            ),
        ),
        findings=(),
    )

    assert report.report_status == "FINAL"
    assert report.finding_count == 0


def test_report_counts_human_dispositions() -> None:
    generator = ReportGenerator()

    accepted = build_reviewed_finding()

    report = generator.generate(
        clause04_result=build_clause04_result(),
        evidence_decisions=(
            build_decision(),
        ),
        findings=(accepted,),
    )

    assert report.finding_count == 1
    assert report.accepted_finding_count == 1
    assert report.modified_finding_count == 0
    assert report.rejected_finding_count == 0