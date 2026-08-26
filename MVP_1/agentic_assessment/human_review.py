"""Governed human-review integration for Agentic Clause 04 findings."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from agentic_assessment.contract_validator import (
    AssessmentContractError,
    AssessmentContractValidator,
)
from agentic_assessment.finding_generator import Finding


HUMAN_REVIEW_COMPONENT_ID = "agentic.human_review"
HUMAN_REVIEW_VERSION = "0.1.0"

ALLOWED_DISPOSITIONS = {
    "ACCEPTED",
    "MODIFIED",
    "REJECTED",
}


class HumanReviewError(RuntimeError):
    """Raised when a finding cannot be reviewed safely."""


class HumanReviewService:
    """Apply an externally supplied human disposition to a draft finding.

    This component does not:
    - determine the review outcome;
    - invent reviewer identity;
    - modify source evidence;
    - generate findings;
    - perform automated approval;
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

    def review(
        self,
        *,
        finding: Finding,
        reviewer_id: str,
        disposition: str,
        comments: str | None = None,
    ) -> Finding:
        """Apply one explicit human review decision."""

        self._require_valid_finding(finding)

        if finding.human_disposition != "PENDING":
            raise HumanReviewError(
                "Finding has already been reviewed."
            )

        reviewer_id = self._require_string(
            reviewer_id,
            "reviewer_id",
        )

        if disposition not in ALLOWED_DISPOSITIONS:
            raise HumanReviewError(
                "Human review disposition is invalid."
            )

        normalized_comments = self._normalize_comments(
            disposition=disposition,
            comments=comments,
        )

        reviewed_at = datetime.now(
            timezone.utc
        ).isoformat()

        review_record: dict[str, Any] = {
            "reviewer_id": reviewer_id,
            "reviewed_at": reviewed_at,
            "disposition": disposition,
        }

        if normalized_comments is not None:
            review_record["comments"] = normalized_comments

        reviewed_finding = replace(
            finding,
            human_disposition=disposition,
            review_record=review_record,
        )

        try:
            self.contract_validator.require_valid(
                contract_name="finding",
                instance=reviewed_finding.to_contract(),
            )

        except AssessmentContractError as exc:
            raise HumanReviewError(
                "Reviewed finding failed contract validation."
            ) from exc

        return reviewed_finding

    def _require_valid_finding(
        self,
        finding: Finding,
    ) -> None:
        """Require a valid schema-bound finding before review."""

        if not isinstance(finding, Finding):
            raise HumanReviewError(
                "Finding is missing or invalid."
            )

        try:
            self.contract_validator.require_valid(
                contract_name="finding",
                instance=finding.to_contract(),
            )

        except AssessmentContractError as exc:
            raise HumanReviewError(
                "Finding failed contract validation."
            ) from exc

    @staticmethod
    def _normalize_comments(
        *,
        disposition: str,
        comments: str | None,
    ) -> str | None:
        """Apply the review-comment rules from the finding contract."""

        if comments is not None:
            if not isinstance(comments, str):
                raise HumanReviewError(
                    "Review comments are invalid."
                )

            comments = comments.strip()

            if not comments:
                comments = None

        if (
            disposition in {
                "MODIFIED",
                "REJECTED",
            }
            and comments is None
        ):
            raise HumanReviewError(
                f"{disposition} review requires comments."
            )

        return comments

    @staticmethod
    def _require_string(
        value: Any,
        field_name: str,
    ) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise HumanReviewError(
                f"{field_name} is missing or invalid."
            )

        return value.strip()