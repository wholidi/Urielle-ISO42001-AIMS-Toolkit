"""Deterministic, fail-closed Clause 04 evidence integrity verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)


INTEGRITY_COMPONENT_ID = "agentic.evidence_integrity"
INTEGRITY_COMPONENT_VERSION = "0.1.0"
LIFECYCLE_STATUSES = {
    "REFERENCED",
    "FILE_PRESENT",
    "INTEGRITY_VERIFIED",
    "CONTENT_REVIEWED",
    "ACCEPTED",
    "REJECTED",
    "UNABLE_TO_ESTABLISH",
}


class EvidenceIntegrityError(RuntimeError):
    """Raised when integrity inputs are structurally unsafe or inconsistent."""


@dataclass(frozen=True)
class EvidenceIntegrityRecord:
    schema_version: str
    integrity_record_id: str
    assessment_id: str
    question_id: str
    evidence_id: str
    locator: str | None
    declared_sha256: str | None
    observed_sha256: str | None
    evidence_status: str
    status_history: tuple[Mapping[str, Any], ...]
    deterministic_checks: tuple[Mapping[str, Any], ...]
    content_review: Mapping[str, Any] | None
    provenance: Mapping[str, Any]

    def to_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "integrity_record_id": self.integrity_record_id,
            "assessment_id": self.assessment_id,
            "question_id": self.question_id,
            "evidence_id": self.evidence_id,
            "locator": self.locator,
            "declared_sha256": self.declared_sha256,
            "observed_sha256": self.observed_sha256,
            "evidence_status": self.evidence_status,
            "status_history": [dict(item) for item in self.status_history],
            "deterministic_checks": [dict(item) for item in self.deterministic_checks],
            "content_review": (
                dict(self.content_review) if self.content_review is not None else None
            ),
            "provenance": dict(self.provenance),
        }


class EvidenceIntegrityVerifier:
    """Verify identity, safe file presence and SHA-256 without reading meaning."""

    def __init__(
        self,
        *,
        contract_validator: AssessmentContractValidator | None = None,
    ) -> None:
        self.contract_validator = contract_validator or AssessmentContractValidator()

    def verify(
        self,
        *,
        sequence: int,
        assessment_id: str,
        question_id: str,
        evidence_id: str,
        evidence_root: Path | str | None,
        manifest_entry: Mapping[str, Any] | None,
        review: Mapping[str, Any] | None,
        timestamp: str,
    ) -> EvidenceIntegrityRecord:
        history: list[dict[str, Any]] = [
            {"status": "REFERENCED", "recorded_at": timestamp,
             "actor": INTEGRITY_COMPONENT_ID}
        ]
        checks: list[dict[str, Any]] = []
        locator: str | None = None
        declared: str | None = None
        observed: str | None = None
        status = "REFERENCED"
        content_review: dict[str, Any] | None = None

        if manifest_entry is None:
            status = "UNABLE_TO_ESTABLISH"
            checks.append(self._check("MANIFEST_ENTRY_PRESENT", "FAILED",
                                      "No manifest entry exists for the evidence identifier."))
            history.append(self._history(status, timestamp))
        else:
            if not isinstance(manifest_entry, Mapping):
                raise EvidenceIntegrityError("Evidence manifest entry is invalid.")
            locator = self._optional_string(manifest_entry.get("locator"))
            declared = self._optional_string(manifest_entry.get("declared_sha256"))
            if locator is None:
                status = "UNABLE_TO_ESTABLISH"
                checks.append(self._check("SAFE_PATH", "FAILED",
                                          "Evidence locator is missing."))
                history.append(self._history(status, timestamp))
            else:
                target, path_error = self._resolve_target(evidence_root, locator)
                if path_error is not None:
                    status = "UNABLE_TO_ESTABLISH"
                    checks.append(self._check("SAFE_PATH", "FAILED", path_error))
                    history.append(self._history(status, timestamp))
                elif target is None or not target.is_file():
                    status = "UNABLE_TO_ESTABLISH"
                    checks.append(self._check("FILE_PRESENT", "FAILED",
                                              "A readable regular file was not established."))
                    history.append(self._history(status, timestamp))
                else:
                    try:
                        observed = self._sha256(target)
                    except OSError:
                        status = "UNABLE_TO_ESTABLISH"
                        checks.append(self._check("FILE_PRESENT", "FAILED",
                                                  "The evidence file could not be read."))
                        history.append(self._history(status, timestamp))
                    else:
                        status = "FILE_PRESENT"
                        checks.extend([
                            self._check("SAFE_PATH", "PASSED",
                                        "Evidence resolved within the permitted root."),
                            self._check("FILE_PRESENT", "PASSED",
                                        "A readable regular file is present."),
                        ])
                        history.append(self._history(status, timestamp))
                        if declared is not None:
                            if not self._valid_sha256(declared):
                                status = "UNABLE_TO_ESTABLISH"
                                checks.append(self._check("HASH_VERIFIED", "FAILED",
                                                          "Declared SHA-256 is invalid."))
                                history.append(self._history(status, timestamp))
                            elif observed.lower() != declared.lower():
                                status = "UNABLE_TO_ESTABLISH"
                                checks.append(self._check("HASH_VERIFIED", "FAILED",
                                                          "Observed SHA-256 does not match the declaration."))
                                history.append(self._history(status, timestamp))
                            else:
                                status = "INTEGRITY_VERIFIED"
                                checks.append(self._check("HASH_VERIFIED", "PASSED",
                                                          "Observed SHA-256 matches the declaration."))
                                history.append(self._history(status, timestamp))

        if review is not None:
            if status != "INTEGRITY_VERIFIED":
                raise EvidenceIntegrityError(
                    "Content review requires prior integrity verification."
                )
            content_review, disposition = self._validate_review(review, timestamp)
            status = "CONTENT_REVIEWED"
            history.append(self._history(status, timestamp, content_review["reviewer_id"]))
            if disposition is not None:
                status = disposition
                history.append(self._history(status, timestamp, content_review["reviewer_id"]))

        record = EvidenceIntegrityRecord(
            schema_version="1.0.0",
            integrity_record_id=f"EIR-{assessment_id}-{sequence:03d}",
            assessment_id=assessment_id,
            question_id=question_id,
            evidence_id=evidence_id,
            locator=locator,
            declared_sha256=declared,
            observed_sha256=observed,
            evidence_status=status,
            status_history=tuple(history),
            deterministic_checks=tuple(checks),
            content_review=content_review,
            provenance={
                "created_at": timestamp,
                "created_by": INTEGRITY_COMPONENT_ID,
                "generator": "DETERMINISTIC_RULES",
                "generator_version": INTEGRITY_COMPONENT_VERSION,
                "source_refs": [f"assessment:{assessment_id}",
                                f"question:{question_id}", f"evidence:{evidence_id}"],
            },
        )
        try:
            self.contract_validator.require_valid(
                contract_name="evidence_integrity_record", instance=record.to_contract()
            )
        except AssessmentContractError as exc:
            raise EvidenceIntegrityError(
                "Evidence integrity record failed contract validation."
            ) from exc
        return record

    @staticmethod
    def _resolve_target(root: Path | str | None, locator: str) -> tuple[Path | None, str | None]:
        if root is None:
            return None, "An explicit evidence root was not supplied."
        relative = Path(locator)
        if relative.is_absolute() or ".." in relative.parts:
            return None, "Absolute paths and path traversal are prohibited."
        root_path = Path(root).resolve()
        target = (root_path / relative).resolve()
        try:
            target.relative_to(root_path)
        except ValueError:
            return None, "Evidence locator escapes the permitted root."
        return target, None

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _valid_sha256(value: str) -> bool:
        return len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)

    @staticmethod
    def _validate_review(review: Mapping[str, Any], timestamp: str) -> tuple[dict[str, Any], str | None]:
        if not isinstance(review, Mapping):
            raise EvidenceIntegrityError("Evidence review record is invalid.")
        reviewer = EvidenceIntegrityVerifier._optional_string(review.get("reviewer_id"))
        comments = EvidenceIntegrityVerifier._optional_string(review.get("comments"))
        reviewed = review.get("content_reviewed")
        disposition = review.get("disposition")
        if reviewer is None or reviewed is not True:
            raise EvidenceIntegrityError(
                "Evidence review requires reviewer_id and content_reviewed=true."
            )
        if disposition not in (None, "ACCEPTED", "REJECTED"):
            raise EvidenceIntegrityError("Evidence review disposition is invalid.")
        if disposition is not None and comments is None:
            raise EvidenceIntegrityError("Evidence acceptance or rejection requires comments.")
        return ({"reviewer_id": reviewer, "reviewed_at": timestamp,
                 "content_reviewed": True, "disposition": disposition,
                 "comments": comments}, disposition)

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _check(check_type: str, status: str, observation: str) -> dict[str, Any]:
        return {"check_type": check_type, "status": status, "observation": observation}

    @staticmethod
    def _history(status: str, timestamp: str, actor: str = INTEGRITY_COMPONENT_ID) -> dict[str, Any]:
        return {"status": status, "recorded_at": timestamp, "actor": actor}
