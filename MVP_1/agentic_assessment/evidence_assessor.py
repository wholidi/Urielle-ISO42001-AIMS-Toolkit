"""Deterministic evidence assessment for Agentic Clause 04."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from agentic_assessment.clause04_adapter import (
    Clause04AssessmentResult,
)
from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)
from agentic_assessment.evidence_integrity import (
    EvidenceIntegrityError,
    EvidenceIntegrityRecord,
    EvidenceIntegrityVerifier,
)


EVIDENCE_ASSESSOR_COMPONENT_ID = "agentic.evidence_assessor"
EVIDENCE_ASSESSOR_VERSION = "0.2.0"


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
        integrity_verifier: EvidenceIntegrityVerifier | None = None,
    ) -> None:
        self.contract_validator = (
            contract_validator
            if contract_validator is not None
            else AssessmentContractValidator()
        )
        self.integrity_verifier = integrity_verifier or EvidenceIntegrityVerifier(
            contract_validator=self.contract_validator
        )
        self.last_integrity_records: tuple[EvidenceIntegrityRecord, ...] = ()

    def assess(
        self,
        *,
        clause04_result: Clause04AssessmentResult,
        evidence_root: Path | str | None = None,
        evidence_manifest: Mapping[str, Any] | None = None,
        evidence_reviews: Mapping[str, Any] | None = None,
    ) -> tuple[EvidenceDecision, ...]:
        """Assess every normalized Clause 04 evidence record."""

        if not isinstance(
            clause04_result,
            Clause04AssessmentResult,
        ):
            raise EvidenceAssessorError(
                "clause04_result is missing or invalid."
            )

        manifest = self._require_mapping(evidence_manifest, "evidence_manifest")
        reviews = self._require_mapping(evidence_reviews, "evidence_reviews")
        referenced_ids: set[str] = set()
        for source_record in clause04_result.evidence_records:
            if not isinstance(source_record, Mapping):
                raise EvidenceAssessorError("Clause 04 evidence record is invalid.")
            referenced_ids.update(
                self._extract_evidence_ids(
                    source_record.get("actual_evidence_references")
                )
            )
        unknown_reviews = set(reviews) - referenced_ids
        if unknown_reviews:
            raise EvidenceAssessorError(
                "Evidence review references an unknown evidence identifier."
            )
        decisions: list[EvidenceDecision] = []
        integrity_records: list[EvidenceIntegrityRecord] = []
        integrity_sequence = 0

        for sequence, record in enumerate(
            clause04_result.evidence_records,
            start=1,
        ):
            evidence_ids = self._extract_evidence_ids(
                record.get("actual_evidence_references")
            ) if isinstance(record, Mapping) else ()
            record_integrity: list[EvidenceIntegrityRecord] = []
            for evidence_id in evidence_ids:
                integrity_sequence += 1
                try:
                    integrity = self.integrity_verifier.verify(
                        sequence=integrity_sequence,
                        assessment_id=clause04_result.assessment_id,
                        question_id=self._require_string(record.get("question_id"), "question_id"),
                        evidence_id=evidence_id,
                        evidence_root=evidence_root,
                        manifest_entry=manifest.get(evidence_id),
                        review=reviews.get(evidence_id),
                        timestamp=self._require_string(record.get("timestamp"), "timestamp"),
                    )
                except EvidenceIntegrityError as exc:
                    raise EvidenceAssessorError(str(exc)) from exc
                record_integrity.append(integrity)
                integrity_records.append(integrity)
            decision = self._assess_record(
                assessment_id=clause04_result.assessment_id,
                sequence=sequence,
                record=record,
                integrity_records=tuple(record_integrity),
            )

            decisions.append(decision)

        self.last_integrity_records = tuple(integrity_records)
        return tuple(decisions)

    def _assess_record(
        self,
        *,
        assessment_id: str,
        sequence: int,
        record: Mapping[str, Any],
        integrity_records: tuple[EvidenceIntegrityRecord, ...],
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
            auditor_flag=auditor_flag,
            integrity_records=integrity_records,
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
        auditor_flag: bool,
        integrity_records: tuple[EvidenceIntegrityRecord, ...],
    ) -> str:
        """Apply deterministic evidence-decision rules."""

        if not evidence_ids:
            return "NOT_EVIDENCED"
        statuses = [item.evidence_status for item in integrity_records]
        accepted = statuses.count("ACCEPTED")
        if not auditor_flag and accepted == len(evidence_ids):
            return "EVIDENCED"
        if accepted:
            return "PARTIALLY_EVIDENCED"
        return "REQUIRES_HUMAN_JUDGEMENT"

    @staticmethod
    def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise EvidenceAssessorError(f"{field_name} must be a mapping.")
        return value

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

            if reference_name in evidence_ids:
                raise EvidenceAssessorError(
                    "Duplicate evidence identifier is not permitted."
                )
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
