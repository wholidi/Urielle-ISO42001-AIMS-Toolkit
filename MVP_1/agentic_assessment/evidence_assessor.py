"""Deterministic evidence assessment for Agentic Clause 04."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from agentic_assessment.clause04_adapter import (
    Clause04AssessmentResult,
)
from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)


EVIDENCE_ASSESSOR_COMPONENT_ID = "agentic.evidence_assessor"
EVIDENCE_ASSESSOR_VERSION = "0.1.0"


class EvidenceAssessorError(RuntimeError):
    """Raised when evidence cannot be assessed safely."""


@dataclass(frozen=True)
class EvidenceDecision:
    """Schema-bound deterministic evidence decision."""

    schema_version: str
    decision_id: str
    assessment_id: str
    question_id: str
    evidence_ids: tuple[str, ...]
    deterministic_checks: tuple[Mapping[str, Any], ...]
    semantic_observations: tuple[Mapping[str, Any], ...]
    decision: str
    confidence: float | None
    human_review_required: bool
    provenance: Mapping[str, Any]

    def to_contract(self) -> dict[str, Any]:
        """Serialize to the Phase-1 evidence-decision contract."""

        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "evidence_ids": list(self.evidence_ids),
            "deterministic_checks": [
                dict(check)
                for check in self.deterministic_checks
            ],
            "semantic_observations": [
                dict(observation)
                for observation in self.semantic_observations
            ],
            "decision": self.decision,
            "confidence": self.confidence,
            "human_review_required": self.human_review_required,
            "provenance": dict(self.provenance),
        }


class EvidenceAssessor:
    """Convert Clause 04 evidence records into governed decisions.

    The assessor is deterministic.

    It does not:
    - modify source evidence;
    - generate findings;
    - make certification decisions;
    - perform human approval;
    - invoke an LLM or external model.
    """

    def __init__(
        self,
        *,
        contract_validator: AssessmentContractValidator | None = None,
    ) -> None:
        self.contract_validator = (
            contract_validator
            if contract_validator is not None
            else AssessmentContractValidator()
        )

    def assess(
        self,
        *,
        clause04_result: Clause04AssessmentResult,
    ) -> tuple[EvidenceDecision, ...]:
        """Assess every normalized Clause 04 evidence record."""

        if not isinstance(
            clause04_result,
            Clause04AssessmentResult,
        ):
            raise EvidenceAssessorError(
                "clause04_result is missing or invalid."
            )

        decisions: list[EvidenceDecision] = []

        for sequence, record in enumerate(
            clause04_result.evidence_records,
            start=1,
        ):
            decision = self._assess_record(
                assessment_id=clause04_result.assessment_id,
                sequence=sequence,
                record=record,
            )

            decisions.append(decision)

        return tuple(decisions)

    def _assess_record(
        self,
        *,
        assessment_id: str,
        sequence: int,
        record: Mapping[str, Any],
    ) -> EvidenceDecision:
        """Create one deterministic evidence decision."""

        if not isinstance(record, Mapping):
            raise EvidenceAssessorError(
                "Clause 04 evidence record is invalid."
            )

        question_id = self._require_string(
            record.get("question_id"),
            "question_id",
        )

        confidence = self._require_confidence(
            record.get("confidence_score")
        )

        auditor_flag = record.get("auditor_flag")

        if not isinstance(auditor_flag, bool):
            raise EvidenceAssessorError(
                "Clause 04 evidence record contains "
                "invalid auditor_flag."
            )

        evidence_ids = self._extract_evidence_ids(
            record.get("actual_evidence_references")
        )

        deterministic_checks = (
            self._build_deterministic_checks(
                question_id=question_id,
                evidence_ids=evidence_ids,
            )
        )

        decision = self._derive_decision(
            evidence_ids=evidence_ids,
            confidence=confidence,
            auditor_flag=auditor_flag,
        )

        human_review_required = decision in {
            "PARTIALLY_EVIDENCED",
            "REQUIRES_HUMAN_JUDGEMENT",
        }

        semantic_observations = (
            self._build_semantic_observations(
                decision=decision,
                auditor_note=record.get("auditor_note"),
            )
        )

        timestamp = self._require_string(
            record.get("timestamp"),
            "timestamp",
        )

        evidence_decision = EvidenceDecision(
            schema_version="1.0.0",
            decision_id=(
                f"ED-{assessment_id}-{sequence:03d}"
            ),
            assessment_id=assessment_id,
            question_id=question_id,
            evidence_ids=evidence_ids,
            deterministic_checks=deterministic_checks,
            semantic_observations=semantic_observations,
            decision=decision,
            confidence=confidence,
            human_review_required=human_review_required,
            provenance={
                "created_at": timestamp,
                "created_by": EVIDENCE_ASSESSOR_COMPONENT_ID,
                "generator": "DETERMINISTIC_RULES",
                "generator_version": EVIDENCE_ASSESSOR_VERSION,
                "source_refs": [
                    f"assessment:{assessment_id}",
                    f"question:{question_id}",
                ],
            },
        )

        try:
            self.contract_validator.require_valid(
                contract_name="evidence_decision",
                instance=evidence_decision.to_contract(),
            )

        except AssessmentContractError as exc:
            raise EvidenceAssessorError(
                "Evidence decision failed contract validation."
            ) from exc

        return evidence_decision

    @staticmethod
    def _derive_decision(
        *,
        evidence_ids: tuple[str, ...],
        confidence: float,
        auditor_flag: bool,
    ) -> str:
        """Apply deterministic evidence-decision rules."""

        if auditor_flag:
            return "REQUIRES_HUMAN_JUDGEMENT"

        if not evidence_ids:
            return "NOT_EVIDENCED"

        if confidence < 1.0:
            return "PARTIALLY_EVIDENCED"

        return "EVIDENCED"

    @staticmethod
    def _extract_evidence_ids(
        references: Any,
    ) -> tuple[str, ...]:
        """Extract stable evidence identifiers from source records."""

        if references is None:
            return ()

        if not isinstance(references, (list, tuple)):
            raise EvidenceAssessorError(
                "actual_evidence_references must be "
                "a list or tuple."
            )

        evidence_ids: list[str] = []

        for reference in references:
            if not isinstance(reference, Mapping):
                raise EvidenceAssessorError(
                    "Evidence reference is invalid."
                )

            reference_name = reference.get(
                "reference_name"
            )

            if (
                not isinstance(reference_name, str)
                or not reference_name.strip()
            ):
                raise EvidenceAssessorError(
                    "Evidence reference is missing "
                    "reference_name."
                )

            if reference_name not in evidence_ids:
                evidence_ids.append(reference_name)

        return tuple(evidence_ids)

    @staticmethod
    def _build_deterministic_checks(
        *,
        question_id: str,
        evidence_ids: tuple[str, ...],
    ) -> tuple[Mapping[str, Any], ...]:
        """Create schema-valid deterministic checks."""

        mapping_check = {
            "check_id": f"CHK-{question_id}-MAP",
            "check_type": "QUESTION_MAPPING_VALID",
            "status": "PASSED",
            "observation": (
                f"Evidence record is mapped to {question_id}."
            ),
        }

        evidence_check = {
            "check_id": f"CHK-{question_id}-EVIDENCE",
            "check_type": "EVIDENCE_TYPE_VALID",
            "status": (
                "PASSED"
                if evidence_ids
                else "FAILED"
            ),
            "observation": (
                "Structured evidence references were supplied."
                if evidence_ids
                else (
                    "No structured evidence references "
                    "were supplied."
                )
            ),
        }

        return (
            mapping_check,
            evidence_check,
        )

    @staticmethod
    def _build_semantic_observations(
        *,
        decision: str,
        auditor_note: Any,
    ) -> tuple[Mapping[str, Any], ...]:
        """Create deterministic observations when required."""

        if decision not in {
            "PARTIALLY_EVIDENCED",
            "REQUIRES_HUMAN_JUDGEMENT",
        }:
            return ()

        if (
            not isinstance(auditor_note, str)
            or not auditor_note.strip()
        ):
            observation = (
                "Deterministic assessment requires "
                "human review."
            )
        else:
            observation = auditor_note.strip()

        return (
            {
                "observer_type": "DETERMINISTIC_RULES",
                "observation": observation,
            },
        )

    @staticmethod
    def _require_confidence(
        value: Any,
    ) -> float:
        if not isinstance(value, (int, float)):
            raise EvidenceAssessorError(
                "Clause 04 evidence record contains "
                "invalid confidence_score."
            )

        confidence = float(value)

        if confidence < 0 or confidence > 1:
            raise EvidenceAssessorError(
                "confidence_score must be between 0 and 1."
            )

        return confidence

    @staticmethod
    def _require_string(
        value: Any,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise EvidenceAssessorError(
                f"{field_name} is missing or invalid."
            )

        return value.strip()