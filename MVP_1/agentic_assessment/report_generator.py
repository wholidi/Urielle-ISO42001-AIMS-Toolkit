"""Deterministic report generation for Agentic Clause 04."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from agentic_assessment.clause04_adapter import (
    Clause04AssessmentResult,
)
from agentic_assessment.evidence_assessor import (
    EvidenceDecision,
)
from agentic_assessment.finding_generator import (
    Finding,
)


REPORT_GENERATOR_COMPONENT_ID = "agentic.report_generator"
REPORT_GENERATOR_VERSION = "0.1.0"


class ReportGeneratorError(RuntimeError):
    """Raised when an Agentic Clause 04 report cannot be generated safely."""


@dataclass(frozen=True)
class AgenticClause04Report:
    """Immutable Agentic Clause 04 report result."""

    assessment_id: str
    session_id: str
    generated_at: str
    report_status: str
    readiness_score: float
    evidence_decision_count: int
    finding_count: int
    pending_finding_count: int
    accepted_finding_count: int
    modified_finding_count: int
    rejected_finding_count: int
    markdown: str
    provenance: Mapping[str, Any]


class ReportGenerator:
    """Assemble governed Agentic Clause 04 results into Markdown.

    The generator does not:
    - rescore Clause 04;
    - reassess source evidence;
    - generate findings;
    - modify human dispositions;
    - perform human review;
    - invoke an LLM or external model.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def generate(
        self,
        *,
        clause04_result: Clause04AssessmentResult,
        evidence_decisions: Sequence[EvidenceDecision],
        findings: Sequence[Finding],
    ) -> AgenticClause04Report:
        """Generate one deterministic governed report."""

        self._validate_clause04_result(
            clause04_result
        )

        decisions = self._validate_decisions(
            evidence_decisions
        )

        reviewed_findings = self._validate_findings(
            findings
        )

        self._require_consistent_assessment_ids(
            assessment_id=clause04_result.assessment_id,
            decisions=decisions,
            findings=reviewed_findings,
        )

        pending_count = self._count_disposition(
            reviewed_findings,
            "PENDING",
        )

        accepted_count = self._count_disposition(
            reviewed_findings,
            "ACCEPTED",
        )

        modified_count = self._count_disposition(
            reviewed_findings,
            "MODIFIED",
        )

        rejected_count = self._count_disposition(
            reviewed_findings,
            "REJECTED",
        )

        report_status = (
            "DRAFT"
            if pending_count > 0
            else "FINAL"
        )

        generated_at = self.clock().astimezone(timezone.utc).isoformat()

        markdown = self._render_markdown(
            clause04_result=clause04_result,
            evidence_decisions=decisions,
            findings=reviewed_findings,
            generated_at=generated_at,
            report_status=report_status,
        )

        return AgenticClause04Report(
            assessment_id=clause04_result.assessment_id,
            session_id=clause04_result.session_id,
            generated_at=generated_at,
            report_status=report_status,
            readiness_score=clause04_result.score,
            evidence_decision_count=len(decisions),
            finding_count=len(reviewed_findings),
            pending_finding_count=pending_count,
            accepted_finding_count=accepted_count,
            modified_finding_count=modified_count,
            rejected_finding_count=rejected_count,
            markdown=markdown,
            provenance={
                "created_at": generated_at,
                "created_by": REPORT_GENERATOR_COMPONENT_ID,
                "generator": "DETERMINISTIC_RULES",
                "generator_version": REPORT_GENERATOR_VERSION,
                "source_refs": [
                    (
                        "assessment:"
                        f"{clause04_result.assessment_id}"
                    ),
                    (
                        "session:"
                        f"{clause04_result.session_id}"
                    ),
                ],
            },
        )

    @staticmethod
    def _validate_clause04_result(
        result: Clause04AssessmentResult,
    ) -> None:
        if not isinstance(
            result,
            Clause04AssessmentResult,
        ):
            raise ReportGeneratorError(
                "clause04_result is missing or invalid."
            )

        if result.status != "COMPLETED":
            raise ReportGeneratorError(
                "Clause 04 assessment is not completed."
            )

        if (
            not isinstance(result.score, (int, float))
            or result.score < 0
            or result.score > 100
        ):
            raise ReportGeneratorError(
                "Clause 04 readiness score is invalid."
            )

    @staticmethod
    def _validate_decisions(
        decisions: Sequence[EvidenceDecision],
    ) -> tuple[EvidenceDecision, ...]:
        if not isinstance(decisions, Sequence) or isinstance(
            decisions,
            (str, bytes),
        ):
            raise ReportGeneratorError(
                "evidence_decisions must be a sequence."
            )

        normalized = tuple(decisions)

        if not all(
            isinstance(item, EvidenceDecision)
            for item in normalized
        ):
            raise ReportGeneratorError(
                "Evidence decision input is invalid."
            )

        return normalized

    @staticmethod
    def _validate_findings(
        findings: Sequence[Finding],
    ) -> tuple[Finding, ...]:
        if not isinstance(findings, Sequence) or isinstance(
            findings,
            (str, bytes),
        ):
            raise ReportGeneratorError(
                "findings must be a sequence."
            )

        normalized = tuple(findings)

        if not all(
            isinstance(item, Finding)
            for item in normalized
        ):
            raise ReportGeneratorError(
                "Finding input is invalid."
            )

        return normalized

    @staticmethod
    def _require_consistent_assessment_ids(
        *,
        assessment_id: str,
        decisions: tuple[EvidenceDecision, ...],
        findings: tuple[Finding, ...],
    ) -> None:
        if any(
            decision.assessment_id != assessment_id
            for decision in decisions
        ):
            raise ReportGeneratorError(
                "Evidence decision assessment_id mismatch."
            )

        if any(
            finding.assessment_id != assessment_id
            for finding in findings
        ):
            raise ReportGeneratorError(
                "Finding assessment_id mismatch."
            )

    @staticmethod
    def _count_disposition(
        findings: tuple[Finding, ...],
        disposition: str,
    ) -> int:
        return sum(
            1
            for finding in findings
            if finding.human_disposition == disposition
        )

    def _render_markdown(
        self,
        *,
        clause04_result: Clause04AssessmentResult,
        evidence_decisions: tuple[
            EvidenceDecision,
            ...
        ],
        findings: tuple[Finding, ...],
        generated_at: str,
        report_status: str,
    ) -> str:
        """Render governed results without new assessment reasoning."""

        lines: list[str] = []

        lines.append(
            "# ISO/IEC 42001 Clause 04 "
            "Agentic Assessment Report"
        )
        lines.append("")

        lines.append(
            f"Assessment ID: "
            f"`{clause04_result.assessment_id}`"
        )

        lines.append(
            f"Session ID: "
            f"`{clause04_result.session_id}`"
        )

        lines.append(
            f"Generated: {generated_at}"
        )

        lines.append(
            f"Report Status: **{report_status}**"
        )

        lines.append("")

        if report_status == "DRAFT":
            lines.append(
                "> This report remains DRAFT because "
                "one or more findings are awaiting "
                "human disposition."
            )
            lines.append("")

        lines.append(
            "## Clause 04 Rule-based Readiness"
        )
        lines.append("")

        lines.append(
            f"**{clause04_result.score}%**"
        )
        lines.append("")

        lines.append(
            "_The readiness score is inherited from the "
            "existing deterministic Clause 04 engine. "
            "The ReportGenerator does not recalculate it._"
        )
        lines.append("")

        lines.append(
            "This report is not a certification decision "
            "or full audit assurance."
        )
        lines.append("")

        self._append_evidence_decisions(
            lines=lines,
            decisions=evidence_decisions,
        )

        self._append_findings(
            lines=lines,
            findings=findings,
        )

        self._append_traceability(
            lines=lines,
            clause04_result=clause04_result,
            evidence_decisions=evidence_decisions,
            findings=findings,
        )

        lines.append("## Limitations")
        lines.append("")

        lines.append(
            "- Evidence references may originate from "
            "human responses and are not independently "
            "verified by this report generator."
        )

        lines.append(
            "- Preliminary finding severity is generated "
            "deterministically and does not replace "
            "authorized human judgement."
        )

        lines.append(
            "- The report generator performs no new "
            "assessment, scoring, evidence interpretation, "
            "or certification decision."
        )

        lines.append(
            "- No LLM or external model is used in report "
            "generation."
        )

        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _append_evidence_decisions(
        *,
        lines: list[str],
        decisions: tuple[EvidenceDecision, ...],
    ) -> None:
        lines.append("## Governed Evidence Decisions")
        lines.append("")

        if not decisions:
            lines.append(
                "No evidence decisions were supplied."
            )
            lines.append("")
            return

        for decision in decisions:
            lines.append(
                f"### {decision.question_id}"
            )
            lines.append("")

            lines.append(
                f"- Decision ID: "
                f"`{decision.decision_id}`"
            )

            lines.append(
                f"- Decision: "
                f"**{decision.decision}**"
            )

            lines.append(
                f"- Confidence: "
                f"{decision.confidence}"
            )

            lines.append(
                "- Human Review Required: "
                f"{decision.human_review_required}"
            )

            if decision.evidence_ids:
                lines.append(
                    "- Evidence References:"
                )

                for evidence_id in (
                    decision.evidence_ids
                ):
                    lines.append(
                        f"  - {evidence_id}"
                    )

            else:
                lines.append(
                    "- Evidence References: None"
                )

            lines.append("")

    @staticmethod
    def _append_findings(
        *,
        lines: list[str],
        findings: tuple[Finding, ...],
    ) -> None:
        lines.append("## Findings")
        lines.append("")

        if not findings:
            lines.append(
                "No draft findings were generated."
            )
            lines.append("")
            return

        for finding in findings:
            lines.append(
                f"### {finding.finding_id} — "
                f"Clause {finding.requirement_ref}"
            )
            lines.append("")

            lines.append(
                f"- Question: {finding.question_id}"
            )

            lines.append(
                "- Preliminary Severity: "
                f"**{finding.severity_preliminary}**"
            )

            lines.append(
                "- Human Disposition: "
                f"**{finding.human_disposition}**"
            )

            lines.append("")

            lines.append("**Condition**")
            lines.append("")
            lines.append(finding.condition)
            lines.append("")

            lines.append("**Criteria**")
            lines.append("")
            lines.append(finding.criteria)
            lines.append("")

            lines.append("**Risk Statement**")
            lines.append("")
            lines.append(
                finding.risk_statement
            )
            lines.append("")

            lines.append("**Recommendation**")
            lines.append("")
            lines.append(
                finding.recommendation
            )
            lines.append("")

            if finding.review_record is not None:
                lines.append("**Human Review**")
                lines.append("")

                lines.append(
                    "- Reviewer: "
                    f"{finding.review_record['reviewer_id']}"
                )

                lines.append(
                    "- Reviewed At: "
                    f"{finding.review_record['reviewed_at']}"
                )

                lines.append(
                    "- Disposition: "
                    f"{finding.review_record['disposition']}"
                )

                comments = finding.review_record.get(
                    "comments"
                )

                if comments:
                    lines.append(
                        f"- Comments: {comments}"
                    )

                lines.append("")

    @staticmethod
    def _append_traceability(
        *,
        lines: list[str],
        clause04_result: Clause04AssessmentResult,
        evidence_decisions: tuple[
            EvidenceDecision,
            ...
        ],
        findings: tuple[Finding, ...],
    ) -> None:
        lines.append("## Traceability")
        lines.append("")

        lines.append(
            f"- Assessment: "
            f"{clause04_result.assessment_id}"
        )

        lines.append(
            f"- Clause 04 Session: "
            f"{clause04_result.session_id}"
        )

        lines.append(
            f"- Evidence Decisions: "
            f"{len(evidence_decisions)}"
        )

        lines.append(
            f"- Findings: {len(findings)}"
        )

        for finding in findings:
            lines.append(
                f"- {finding.finding_id} "
                f"<- {finding.question_id}"
            )

        lines.append("")
