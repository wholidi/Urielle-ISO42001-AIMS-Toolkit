"""Deterministic draft finding generation for Agentic Clause 04."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)
from agentic_assessment.evidence_assessor import (
    EvidenceDecision,
)


FINDING_GENERATOR_COMPONENT_ID = "agentic.finding_generator"
FINDING_GENERATOR_VERSION = "0.1.0"


QUESTION_REQUIREMENT_MAP = {
    "C4-Q01": "4.1",
    "C4-Q02": "4.2",
    "C4-Q03": "4.3",
    "C4-Q04": "4.4",
}


class FindingGeneratorError(RuntimeError):
    """Raised when draft findings cannot be generated safely."""


@dataclass(frozen=True)
class Finding:
    """Schema-bound deterministic draft finding."""

    schema_version: str
    finding_id: str
    assessment_id: str
    requirement_ref: str
    question_id: str
    condition: str
    criteria: str
    evidence_refs: tuple[Mapping[str, Any], ...]
    risk_statement: str
    severity_preliminary: str
    recommendation: str
    human_disposition: str
    review_record: Mapping[str, Any] | None
    provenance: Mapping[str, Any]

    def to_contract(self) -> dict[str, Any]:
        """Serialize to the Phase-1 finding contract."""

        return {
            "schema_version": self.schema_version,
            "finding_id": self.finding_id,
            "assessment_id": self.assessment_id,
            "requirement_ref": self.requirement_ref,
            "question_id": self.question_id,
            "condition": self.condition,
            "criteria": self.criteria,
            "evidence_refs": [
                dict(reference)
                for reference in self.evidence_refs
            ],
            "risk_statement": self.risk_statement,
            "severity_preliminary": self.severity_preliminary,
            "recommendation": self.recommendation,
            "human_disposition": self.human_disposition,
            "review_record": (
                dict(self.review_record)
                if self.review_record is not None
                else None
            ),
            "provenance": dict(self.provenance),
        }


class FindingGenerator:
    """Generate governed draft findings from evidence decisions.

    The generator is deterministic.

    It does not:
    - reassess raw evidence;
    - modify evidence decisions;
    - make certification decisions;
    - accept, reject, or modify its own findings;
    - invoke an LLM or external model.
    """

    def __init__(
        self,
        *,
        contract_validator: AssessmentContractValidator | None = None,
        requirement_map: Mapping[str, str] | None = None,
    ) -> None:
        self.contract_validator = (
            contract_validator
            if contract_validator is not None
            else AssessmentContractValidator()
        )

        self.requirement_map = dict(
            requirement_map
            if requirement_map is not None
            else QUESTION_REQUIREMENT_MAP
        )

    def generate(
        self,
        *,
        decisions: Sequence[EvidenceDecision],
    ) -> tuple[Finding, ...]:
        """Generate draft findings from validated evidence decisions."""

        if not isinstance(decisions, Sequence) or isinstance(
            decisions,
            (str, bytes),
        ):
            raise FindingGeneratorError(
                "decisions must be a sequence."
            )

        findings: list[Finding] = []

        for decision in decisions:
            self._require_valid_decision(decision)

            if decision.decision in {
                "EVIDENCED",
                "NOT_APPLICABLE",
            }:
                continue

            finding = self._generate_finding(
                decision=decision,
                sequence=len(findings) + 1,
            )

            findings.append(finding)

        return tuple(findings)

    def _require_valid_decision(
        self,
        decision: EvidenceDecision,
    ) -> None:
        """Require a schema-valid EvidenceDecision before use."""

        if not isinstance(decision, EvidenceDecision):
            raise FindingGeneratorError(
                "Evidence decision is missing or invalid."
            )

        try:
            self.contract_validator.require_valid(
                contract_name="evidence_decision",
                instance=decision.to_contract(),
            )

        except AssessmentContractError as exc:
            raise FindingGeneratorError(
                "Evidence decision failed contract validation."
            ) from exc

    def _generate_finding(
        self,
        *,
        decision: EvidenceDecision,
        sequence: int,
    ) -> Finding:
        """Generate one deterministic draft finding."""

        requirement_ref = self.requirement_map.get(
            decision.question_id
        )

        if requirement_ref is None:
            raise FindingGeneratorError(
                "No Clause 04 requirement mapping exists "
                f"for {decision.question_id}."
            )

        (
            condition,
            risk_statement,
            recommendation,
            severity,
        ) = self._finding_content(
            decision=decision,
            requirement_ref=requirement_ref,
        )

        evidence_refs = self._build_evidence_refs(
            decision
        )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        finding = Finding(
            schema_version="1.0.0",
            finding_id=(
                f"FND-{decision.assessment_id}-"
                f"{sequence:03d}"
            ),
            assessment_id=decision.assessment_id,
            requirement_ref=requirement_ref,
            question_id=decision.question_id,
            condition=condition,
            criteria=(
                "ISO/IEC 42001 Clause "
                f"{requirement_ref} assessment criteria "
                f"for {decision.question_id} require "
                "sufficient and traceable supporting evidence."
            ),
            evidence_refs=evidence_refs,
            risk_statement=risk_statement,
            severity_preliminary=severity,
            recommendation=recommendation,
            human_disposition="PENDING",
            review_record=None,
            provenance={
                "created_at": timestamp,
                "created_by": FINDING_GENERATOR_COMPONENT_ID,
                "generator": "DETERMINISTIC_RULES",
                "generator_version": FINDING_GENERATOR_VERSION,
                "source_refs": self._source_refs(
                    decision
                ),
            },
        )

        try:
            self.contract_validator.require_valid(
                contract_name="finding",
                instance=finding.to_contract(),
            )

        except AssessmentContractError as exc:
            raise FindingGeneratorError(
                "Finding failed contract validation."
            ) from exc

        return finding

    @staticmethod
    def _finding_content(
        *,
        decision: EvidenceDecision,
        requirement_ref: str,
    ) -> tuple[str, str, str, str]:
        """Map governed evidence decisions to draft finding content."""

        if decision.decision == "NOT_EVIDENCED":
            return (
                (
                    f"No structured evidence was accepted "
                    f"for {decision.question_id}."
                ),
                (
                    "Without sufficient supporting evidence, "
                    f"conformity with requirement "
                    f"{requirement_ref} cannot be demonstrated "
                    "by this assessment."
                ),
                (
                    "Provide and validate evidence addressing "
                    f"requirement {requirement_ref}, then "
                    "reassess the evidence."
                ),
                "MEDIUM",
            )

        if decision.decision == "PARTIALLY_EVIDENCED":
            return (
                (
                    f"Evidence for {decision.question_id} "
                    "was only partially evidenced by the "
                    "deterministic assessment."
                ),
                (
                    "Partial evidence may leave the assessment "
                    f"conclusion for requirement "
                    f"{requirement_ref} insufficiently supported."
                ),
                (
                    "Complete or strengthen the evidence for "
                    f"requirement {requirement_ref} and obtain "
                    "human review before final disposition."
                ),
                "LOW",
            )

        if (
            decision.decision
            == "REQUIRES_HUMAN_JUDGEMENT"
        ):
            return (
                (
                    f"Evidence for {decision.question_id} "
                    "requires human judgement before "
                    "assessment disposition."
                ),
                (
                    "Automated disposition would exceed the "
                    "deterministic assessment boundary for "
                    f"requirement {requirement_ref}."
                ),
                (
                    "Route the evidence decision to an "
                    "authorized human reviewer before final "
                    "disposition."
                ),
                "REVIEW_REQUIRED",
            )

        raise FindingGeneratorError(
            "Unsupported evidence decision for finding "
            f"generation: {decision.decision}."
        )

    @staticmethod
    def _build_evidence_refs(
        decision: EvidenceDecision,
    ) -> tuple[Mapping[str, Any], ...]:
        """Build traceable references without rereading source evidence."""

        references: list[Mapping[str, Any]] = [
            {
                "reference_type": "EVIDENCE_DECISION",
                "reference_id": decision.decision_id,
            }
        ]

        for evidence_id in decision.evidence_ids:
            references.append(
                {
                    "reference_type": "EVIDENCE",
                    "reference_id": evidence_id,
                }
            )

        return tuple(references)

    @staticmethod
    def _source_refs(
        decision: EvidenceDecision,
    ) -> list[str]:
        """Create finding provenance references."""

        refs = [
            f"evidence_decision:{decision.decision_id}",
            f"question:{decision.question_id}",
        ]

        refs.extend(
            f"evidence:{evidence_id}"
            for evidence_id in decision.evidence_ids
        )

        return list(dict.fromkeys(refs))