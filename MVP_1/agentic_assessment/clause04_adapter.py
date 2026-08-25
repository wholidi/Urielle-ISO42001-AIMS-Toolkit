"""Adapter boundary for the frozen deterministic Clause 04 assessment engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from clause_04_context.run_clause04_demo import (
    run_clause04_assessment,
)

class Clause04AdapterError(RuntimeError):
    """Raised when Clause 04 execution cannot complete safely."""

@dataclass(frozen=True)
class Clause04AssessmentResult:
    """Normalized deterministic Clause 04 result."""

    assessment_id: str
    session_id: str
    status: str
    score: float
    evidence_records: tuple[
        Mapping[str, Any],
        ...
    ]
    gaps: tuple[
        Mapping[str, Any],
        ...
    ]
    source_result: Mapping[str, Any]

Clause04Executor = Callable[
    [Mapping[str, Any]],
    Mapping[str, Any],
]


class Clause04Adapter:
    """Thin deterministic adapter around the frozen Clause 04 engine.

    The adapter does not:
    - calculate readiness itself;
    - reinterpret evidence;
    - generate findings;
    - modify source evidence;
    - call an LLM;
    - perform human approval.

    Its sole responsibility is to invoke the existing Clause 04
    implementation and normalize its result for the agentic workflow.
    """

    def __init__(
        self,
        *,
        executor: Clause04Executor,
    ) -> None:
        if not callable(executor):
            raise Clause04AdapterError(
                "Clause 04 executor must be callable."
            )

        self.executor = executor

    def execute(
        self,
        *,
        assessment_id: str,
        assessment_context: Mapping[str, Any],
    ) -> Clause04AssessmentResult:
        """Execute one deterministic Clause 04 assessment."""

        self._require_identifier(
            assessment_id,
            "assessment_id",
        )

        if not isinstance(assessment_context, Mapping):
            raise Clause04AdapterError(
                "assessment_context must be a mapping."
            )

        try:
            raw_result = self.executor(
                dict(assessment_context)
            )

        except Clause04AdapterError:
            raise

        except Exception as exc:
            raise Clause04AdapterError(
                "Clause 04 deterministic execution failed."
            ) from exc

        if not isinstance(raw_result, Mapping):
            raise Clause04AdapterError(
                "Clause 04 executor returned an invalid result."
            )

        return self._normalize(
            assessment_id=assessment_id,
            raw_result=raw_result,
        )

    def _normalize(
        self,
        *,
        assessment_id: str,
        raw_result: Mapping[str, Any],
    ) -> Clause04AssessmentResult:
        """Normalize without recalculating Clause 04 results."""

        session_id = raw_result.get("session_id")
        status = raw_result.get("status")
        score = raw_result.get("score")
        evidence_records = raw_result.get("evidence_records")
        gaps = raw_result.get("gaps")

        if not isinstance(session_id, str) or not session_id.strip():
            raise Clause04AdapterError(
                "Clause 04 result is missing session_id."
            )

        if not isinstance(status, str) or not status.strip():
            raise Clause04AdapterError(
                "Clause 04 result is missing status."
            )

        if not isinstance(score, (int, float)):
            raise Clause04AdapterError(
                "Clause 04 result contains invalid score."
            )

        if not isinstance(evidence_records, (list, tuple)):
            raise Clause04AdapterError(
                "Clause 04 result contains invalid evidence_records."
            )

        if not all(
            isinstance(record, Mapping)
            for record in evidence_records
        ):
            raise Clause04AdapterError(
                "Clause 04 evidence_records contain invalid entries."
            )

        if not isinstance(gaps, (list, tuple)):
            raise Clause04AdapterError(
                "Clause 04 result contains invalid gaps."
            )

        if not all(
            isinstance(gap, Mapping)
            for gap in gaps
        ):
            raise Clause04AdapterError(
                "Clause 04 gaps contain invalid entries."
            )

        return Clause04AssessmentResult(
            assessment_id=assessment_id,
            session_id=session_id,
            status=status,
            score=float(score),
            evidence_records=tuple(
                dict(record)
                for record in evidence_records
            ),
            gaps=tuple(
                dict(gap)
                for gap in gaps
            ),
            source_result=dict(raw_result),
        )

    @staticmethod
    def _string_tuple(
        value: Any,
        *,
        field_name: str,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, (list, tuple)):
            raise Clause04AdapterError(
                f"{field_name} must be a list or tuple."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in value
        ):
            raise Clause04AdapterError(
                f"{field_name} contains invalid entries."
            )

        return tuple(value)

    @staticmethod
    def _require_identifier(
        value: Any,
        field_name: str,
    ) -> None:
        if not isinstance(value, str) or not value.strip():
            raise Clause04AdapterError(
                f"{field_name} is missing or invalid."
            )


    def deterministic_clause04_executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Invoke the frozen deterministic Clause 04 assessment engine."""

        session_id = context.get("session_id")
        questions = context.get("questions")
        responses = context.get("responses")

        if (
            not isinstance(session_id, str)
            or not session_id.strip()
        ):
            raise Clause04AdapterError(
                "Clause 04 context is missing session_id."
            )

        if not isinstance(questions, list):
            raise Clause04AdapterError(
                "Clause 04 context is missing questions."
            )

        if not isinstance(responses, list):
            raise Clause04AdapterError(
                "Clause 04 context is missing responses."
            )

        return run_clause04_assessment(
            session_id=session_id,
            questions=questions,
            responses=responses,
        )