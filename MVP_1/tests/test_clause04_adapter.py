"""Tests for the deterministic Clause 04 adapter boundary."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from agentic_assessment.clause04_adapter import (
    Clause04Adapter,
    Clause04AdapterError,
)

def valid_executor(
    context: Mapping[str, Any],
) -> Mapping[str, Any]:
    return {
        "session_id": "CLAUSE4-TEST-001",
        "status": "COMPLETED",
        "score": 92.5,
        "evidence_records": [
            {
                "question_id": "C4.1-01",
                "clause": "4.1",
                "confidence_score": 0.9,
            },
            {
                "question_id": "C4.2-01",
                "clause": "4.2",
                "confidence_score": 0.8,
            },
        ],
        "gaps": [
            {
                "gap_type": "REVIEW_REQUIRED",
                "question_id": "C4.2-01",
                "clause": "4.2",
                "description": (
                    "Interested-party review requires update."
                ),
            },
        ],
        "input_context": dict(context),
    }

def test_adapter_normalizes_clause04_result() -> None:
    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    result = adapter.execute(
        assessment_id="CLAUSE04-001",
        assessment_context={
            "organization": "Example",
        },
    )

    assert result.assessment_id == "CLAUSE04-001"
    assert result.session_id == "CLAUSE4-TEST-001"
    assert result.status == "COMPLETED"
    assert result.score == 92.5

    assert len(result.evidence_records) == 2

    assert (
        result.evidence_records[0]["question_id"]
        == "C4.1-01"
    )
    assert (
        result.evidence_records[0]["clause"]
        == "4.1"
    )

    assert (
        result.evidence_records[1]["question_id"]
        == "C4.2-01"
    )
    assert (
        result.evidence_records[1]["clause"]
        == "4.2"
    )

    assert len(result.gaps) == 1

    assert (
        result.gaps[0]["gap_type"]
        == "REVIEW_REQUIRED"
    )
    assert (
        result.gaps[0]["question_id"]
        == "C4.2-01"
    )
    assert (
        result.gaps[0]["description"]
        == "Interested-party review requires update."
    )

def test_adapter_preserves_source_result() -> None:
    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    result = adapter.execute(
        assessment_id="CLAUSE04-002",
        assessment_context={
            "organization": "Example",
        },
    )

    assert result.source_result["score"] == 92.5
    assert result.source_result["status"] == "COMPLETED"
    assert (
        result.source_result["session_id"]
        == "CLAUSE4-TEST-001"
    )



def test_adapter_passes_context_to_executor() -> None:
    observed: dict[str, Any] = {}

    def executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        observed.update(context)

        return {
            "session_id": "CLAUSE4-TEST-003",
            "status": "COMPLETED",
            "score": 100,
            "evidence_records": [],
            "gaps": [],
        }

    adapter = Clause04Adapter(
        executor=executor,
    )

    adapter.execute(
        assessment_id="CLAUSE04-003",
        assessment_context={
            "scope": "Clause 04",
        },
    )

    assert observed == {
        "scope": "Clause 04",
    }


def test_adapter_does_not_modify_input_context() -> None:
    context = {
        "scope": "Clause 04",
    }

    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    adapter.execute(
        assessment_id="CLAUSE04-004",
        assessment_context=context,
    )

    assert context == {
        "scope": "Clause 04",
    }


def test_missing_assessment_id_fails_closed() -> None:
    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="assessment_id is missing or invalid",
    ):
        adapter.execute(
            assessment_id="",
            assessment_context={},
        )


def test_non_mapping_context_fails_closed() -> None:
    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="assessment_context must be a mapping",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-005",
            assessment_context=[],  # type: ignore[arg-type]
        )


def test_executor_failure_is_wrapped() -> None:
    def failing_executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        raise RuntimeError("internal failure")

    adapter = Clause04Adapter(
        executor=failing_executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="deterministic execution failed",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-006",
            assessment_context={},
        )


def test_invalid_executor_result_fails_closed() -> None:
    def invalid_executor(
        context: Mapping[str, Any],
    ) -> Any:
        return "invalid"

    adapter = Clause04Adapter(
        executor=invalid_executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="returned an invalid result",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-007",
            assessment_context={},
        )


def test_missing_status_fails_closed() -> None:
    def executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "session_id": "CLAUSE4-TEST-008",
            "score": 90,
            "evidence_refs": [],
            "gaps": [],
        }

    adapter = Clause04Adapter(
        executor=executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="missing status",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-008",
            assessment_context={},
        )


def test_invalid_score_fails_closed() -> None:
    def executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "session_id": "CLAUSE4-TEST-009",
            "status": "COMPLETED",
            "score": "ninety",
            "evidence_refs": [],
            "gaps": [],
        }

    adapter = Clause04Adapter(
        executor=executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="invalid score",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-009",
            assessment_context={},
        )

def test_invalid_evidence_records_fail_closed() -> None:
    def executor(
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        return {
            "session_id": "CLAUSE4-TEST-010",
            "status": "COMPLETED",
            "score": 90,
            "evidence_records": "invalid",
            "gaps": [],
        }

    adapter = Clause04Adapter(
        executor=executor,
    )

    with pytest.raises(
        Clause04AdapterError,
        match="invalid evidence_records",
    ):
        adapter.execute(
            assessment_id="CLAUSE04-010",
            assessment_context={},
        )

def test_adapter_is_deterministic_for_same_executor_result() -> None:
    adapter = Clause04Adapter(
        executor=valid_executor,
    )

    first = adapter.execute(
        assessment_id="CLAUSE04-011",
        assessment_context={},
    )

    second = adapter.execute(
        assessment_id="CLAUSE04-011",
        assessment_context={},
    )

    assert first == second