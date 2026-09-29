"""Clause 05 deterministic aggregation over P03 question assessments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

try:
    from agentic_assessment.shared_kernel.validation import canonical_identifier
except Exception:  # pragma: no cover - local checkpoint fallback
    import hashlib, json
    def canonical_identifier(prefix: str, *parts: Any) -> str:
        payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        return f"{prefix}-{hashlib.sha256(payload).hexdigest().upper()}"

class Clause05AggregationError(RuntimeError):
    pass

@dataclass(frozen=True)
class Clause05RequirementResult:
    result_id: str
    assessment_id: str
    requirement_ref: str
    outcome: str
    question_assessment_ids: tuple[str, ...]
    question_ids: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "assessment_id": self.assessment_id,
            "requirement_ref": self.requirement_ref,
            "outcome": self.outcome,
            "question_assessment_ids": list(self.question_assessment_ids),
            "question_ids": list(self.question_ids),
            "rationale": self.rationale,
        }

def _record(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    serializer = getattr(value, "to_contract", None)
    if callable(serializer):
        return dict(serializer())
    raise Clause05AggregationError("Invalid requirement assessment record.")

def aggregate_requirement(
    *,
    assessment_id: str,
    requirement_ref: str,
    question_ids: Sequence[str],
    assessments: Sequence[Any],
) -> Clause05RequirementResult:
    expected = tuple(sorted(set(question_ids)))
    if not expected:
        raise Clause05AggregationError("At least one expected question is required.")
    records = [_record(item) for item in assessments]
    by_question: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("assessment_id") != assessment_id:
            raise Clause05AggregationError("Assessment identity mismatch.")
        if record.get("requirement_ref") != requirement_ref:
            raise Clause05AggregationError("Requirement identity mismatch.")
        qid = record.get("question_id")
        if qid in by_question:
            raise Clause05AggregationError("Duplicate question assessment is prohibited.")
        by_question[qid] = record

    unknown = set(by_question) - set(expected)
    if unknown:
        raise Clause05AggregationError("Unexpected question assessment is prohibited.")

    ordered_records = [by_question.get(qid) for qid in expected]
    if any(record is None for record in ordered_records):
        outcome = "UNRESOLVED"
        rationale = "One or more mandatory atomic questions have no assessment."
    else:
        outcomes = [record["outcome"] for record in ordered_records]
        if any(value == "UNSUPPORTED" for value in outcomes):
            outcome = "UNSUPPORTED"
            rationale = "At least one mandatory atomic question is unsupported."
        elif all(value == "SUPPORTED" for value in outcomes):
            outcome = "SUPPORTED"
            rationale = "All mandatory atomic questions are supported by question-specific human-accepted evidence."
        else:
            outcome = "UNRESOLVED"
            rationale = "One or more mandatory atomic questions remain unresolved."

    assessment_ids = tuple(
        sorted(
            record["requirement_assessment_id"]
            for record in ordered_records
            if record is not None
        )
    )
    result_id = canonical_identifier(
        "C05REQ",
        assessment_id,
        requirement_ref,
        expected,
        assessment_ids,
        outcome,
    )
    return Clause05RequirementResult(
        result_id=result_id,
        assessment_id=assessment_id,
        requirement_ref=requirement_ref,
        outcome=outcome,
        question_assessment_ids=assessment_ids,
        question_ids=expected,
        rationale=rationale,
    )
