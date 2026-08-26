"""End-to-end deterministic Clause 04 governed workflow handlers."""

from __future__ import annotations

from typing import Any, Mapping

from agentic_assessment.clause04_adapter import (
    Clause04Adapter,
    Clause04AssessmentResult,
)
from agentic_assessment.evidence_assessor import (
    EvidenceAssessor,
    EvidenceDecision,
)
from agentic_assessment.finding_generator import (
    Finding,
    FindingGenerator,
)
from agentic_assessment.human_review import (
    HumanReviewService,
)
from agentic_assessment.report_generator import (
    AgenticClause04Report,
    ReportGenerator,
)
from agentic_assessment.supervisor import (
    WorkflowStep,
)


class Clause04WorkflowError(RuntimeError):
    """Raised when the governed Clause 04 workflow cannot continue safely."""


class Clause04Workflow:
    """Bind deterministic Clause 04 components to supervisor workflow steps.

    The workflow:
    - coordinates existing deterministic components;
    - preserves the supervisor as the governance coordinator;
    - consumes human review decisions supplied externally;
    - never creates its own human disposition;
    - never invokes an LLM or external model.
    """

    def __init__(
        self,
        *,
        clause04_adapter: Clause04Adapter,
        evidence_assessor: EvidenceAssessor | None = None,
        finding_generator: FindingGenerator | None = None,
        human_review_service: HumanReviewService | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        self.clause04_adapter = clause04_adapter

        self.evidence_assessor = (
            evidence_assessor
            if evidence_assessor is not None
            else EvidenceAssessor()
        )

        self.finding_generator = (
            finding_generator
            if finding_generator is not None
            else FindingGenerator()
        )

        self.human_review_service = (
            human_review_service
            if human_review_service is not None
            else HumanReviewService()
        )

        self.report_generator = (
            report_generator
            if report_generator is not None
            else ReportGenerator()
        )

        self.last_report: AgenticClause04Report | None = None

    def handlers(self) -> Mapping[WorkflowStep, Any]:
        """Return handlers for the existing SequentialSupervisor."""

        return {
            WorkflowStep.ASSESSMENT_PLANNING:
                self.assessment_planning,

            WorkflowStep.QUESTION_SELECTION:
                self.question_selection,

            WorkflowStep.CLAUSE_04_EXECUTION:
                self.clause04_execution,

            WorkflowStep.EVIDENCE_ASSESSMENT:
                self.evidence_assessment,

            WorkflowStep.FINDING_GENERATION:
                self.finding_generation,

            WorkflowStep.HUMAN_REVIEW_DECISION:
                self.human_review_decision,

            WorkflowStep.REPORT_GENERATION:
                self.report_generation,
        }

    @staticmethod
    def assessment_planning(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Preserve already supplied governed assessment context."""

        Clause04Workflow._require_mapping(
            context,
            "assessment context",
        )

        return dict(context)

    @staticmethod
    def question_selection(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Preserve deterministic Clause 04 question selection.

        Phase 3D.3 does not introduce autonomous question selection.
        """

        Clause04Workflow._require_mapping(
            context,
            "assessment context",
        )

        return dict(context)

    def clause04_execution(
        self,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Execute the existing deterministic Clause 04 adapter."""

        self._require_mapping(
            context,
            "assessment context",
        )

        assessment_id = self._require_string(
            context.get("assessment_id"),
            "assessment_id",
        )

        result = self.clause04_adapter.execute(
            assessment_id=assessment_id,
            assessment_context=context,
        )

        next_context = dict(context)
        next_context["clause04_result"] = result

        return next_context

    def evidence_assessment(
        self,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Convert Clause 04 evidence into governed evidence decisions."""

        clause04_result = context.get(
            "clause04_result"
        )

        if not isinstance(
            clause04_result,
            Clause04AssessmentResult,
        ):
            raise Clause04WorkflowError(
                "Clause 04 result is missing or invalid."
            )

        decisions = self.evidence_assessor.assess(
            clause04_result=clause04_result
        )

        next_context = dict(context)
        next_context["evidence_decisions"] = tuple(
            decisions
        )

        return next_context

    def finding_generation(
        self,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Generate deterministic draft findings from evidence decisions."""

        decisions = self._require_decisions(
            context.get("evidence_decisions")
        )

        findings = self.finding_generator.generate(
            decisions=decisions
        )

        next_context = dict(context)
        next_context["findings"] = tuple(
            findings
        )

        return next_context

    def human_review_decision(
        self,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Apply only explicit externally supplied human review decisions."""

        findings = self._require_findings(
            context.get("findings")
        )

        raw_reviews = context.get(
            "human_reviews",
            {},
        )

        if not isinstance(raw_reviews, Mapping):
            raise Clause04WorkflowError(
                "human_reviews must be a mapping."
            )

        finding_ids = {
            finding.finding_id
            for finding in findings
        }

        unknown_review_ids = (
            set(raw_reviews.keys())
            - finding_ids
        )

        if unknown_review_ids:
            raise Clause04WorkflowError(
                "Human review references an unknown finding."
            )

        reviewed_findings: list[Finding] = []

        for finding in findings:
            review = raw_reviews.get(
                finding.finding_id
            )

            if review is None:
                reviewed_findings.append(
                    finding
                )
                continue

            if not isinstance(review, Mapping):
                raise Clause04WorkflowError(
                    "Human review record is invalid."
                )

            reviewer_id = review.get(
                "reviewer_id"
            )

            disposition = review.get(
                "disposition"
            )

            comments = review.get(
                "comments"
            )

            reviewed = (
                self.human_review_service.review(
                    finding=finding,
                    reviewer_id=reviewer_id,
                    disposition=disposition,
                    comments=comments,
                )
            )

            reviewed_findings.append(
                reviewed
            )

        next_context = dict(context)

        next_context["reviewed_findings"] = tuple(
            reviewed_findings
        )

        return next_context

    def report_generation(
        self,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Generate the governed final or draft report."""

        clause04_result = context.get(
            "clause04_result"
        )

        if not isinstance(
            clause04_result,
            Clause04AssessmentResult,
        ):
            raise Clause04WorkflowError(
                "Clause 04 result is missing or invalid."
            )

        decisions = self._require_decisions(
            context.get("evidence_decisions")
        )

        findings = self._require_findings(
            context.get(
                "reviewed_findings",
                context.get("findings"),
            )
        )

        report = self.report_generator.generate(
            clause04_result=clause04_result,
            evidence_decisions=decisions,
            findings=findings,
        )

        self.last_report = report

        next_context = dict(context)
        next_context["agentic_report"] = report

        return next_context

    @staticmethod
    def _require_decisions(
        value: Any,
    ) -> tuple[EvidenceDecision, ...]:
        if not isinstance(value, (tuple, list)):
            raise Clause04WorkflowError(
                "Evidence decisions are missing or invalid."
            )

        decisions = tuple(value)

        if not all(
            isinstance(item, EvidenceDecision)
            for item in decisions
        ):
            raise Clause04WorkflowError(
                "Evidence decisions are missing or invalid."
            )

        return decisions

    @staticmethod
    def _require_findings(
        value: Any,
    ) -> tuple[Finding, ...]:
        if not isinstance(value, (tuple, list)):
            raise Clause04WorkflowError(
                "Findings are missing or invalid."
            )

        findings = tuple(value)

        if not all(
            isinstance(item, Finding)
            for item in findings
        ):
            raise Clause04WorkflowError(
                "Findings are missing or invalid."
            )

        return findings

    @staticmethod
    def _require_mapping(
        value: Any,
        field_name: str,
    ) -> None:
        if not isinstance(value, Mapping):
            raise Clause04WorkflowError(
                f"{field_name} is missing or invalid."
            )

    @staticmethod
    def _require_string(
        value: Any,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise Clause04WorkflowError(
                f"{field_name} is missing or invalid."
            )

        return value.strip()