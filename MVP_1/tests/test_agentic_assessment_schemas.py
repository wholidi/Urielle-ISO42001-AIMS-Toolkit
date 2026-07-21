"""Contract tests for Phase 1 agentic-assessment JSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker


PILOT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PILOT_ROOT / "agentic_assessment" / "schemas"
FIXTURE_ROOT = PILOT_ROOT / "tests" / "fixtures" / "agentic_assessment"

SCHEMA_FILES = {
    "assessment_plan": "assessment_plan.schema.json",
    "evidence_decision": "evidence_decision.schema.json",
    "finding": "finding.schema.json",
    "execution_event": "execution_event.schema.json",
}

VALID_FIXTURES = [
    ("assessment_plan", "valid/assessment_plan/assessment_plan.valid.json"),
    ("evidence_decision", "valid/evidence_decision/evidence_decision.valid.json"),
    ("finding", "valid/finding/finding.valid.json"),
    ("execution_event", "valid/execution_event/execution_event.valid.json"),
]

INVALID_FIXTURES = [
    (
        "assessment_plan",
        "invalid/assessment_plan/assessment_plan.invalid_enum.json",
        ("questions", 0, "applicability_status"),
    ),
    (
        "evidence_decision",
        "invalid/evidence_decision/evidence_decision.invalid_evidence_refs.json",
        ("evidence_ids",),
    ),
    (
        "finding",
        "invalid/finding/finding.invalid_missing_review_record.json",
        ("review_record",),
    ),
    (
        "execution_event",
        "invalid/execution_event/execution_event.invalid_human_review_flag.json",
        ("human_review_required",),
    ),
]


def load_json(path: Path) -> dict[str, Any]:
    """Load a UTF-8 JSON object and fail clearly when the file is missing."""
    if not path.is_file():
        raise AssertionError(f"Required JSON file does not exist: {path}")

    with path.open("r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    if not isinstance(data, dict):
        raise AssertionError(f"Expected a JSON object in {path}")

    return data


def build_validator(contract_name: str) -> Draft202012Validator:
    """Load and construct a Draft 2020-12 validator for one contract."""
    schema_path = SCHEMA_ROOT / SCHEMA_FILES[contract_name]
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.mark.parametrize("contract_name", sorted(SCHEMA_FILES))
def test_schema_is_valid_draft_2020_12(contract_name: str) -> None:
    """Every Phase 1 contract must itself be a valid Draft 2020-12 schema."""
    schema_path = SCHEMA_ROOT / SCHEMA_FILES[contract_name]
    schema = load_json(schema_path)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == "1.0.0"
    assert "provenance" in schema["required"]

    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(("contract_name", "fixture_relative_path"), VALID_FIXTURES)
def test_valid_fixture_is_accepted(
    contract_name: str,
    fixture_relative_path: str,
) -> None:
    """Each valid fixture must be accepted by its corresponding schema."""
    validator = build_validator(contract_name)
    instance = load_json(FIXTURE_ROOT / fixture_relative_path)

    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))

    assert not errors, "\n".join(error.message for error in errors)


@pytest.mark.parametrize(
    ("contract_name", "fixture_relative_path", "expected_instance_path"),
    INVALID_FIXTURES,
)
def test_invalid_fixture_is_rejected(
    contract_name: str,
    fixture_relative_path: str,
    expected_instance_path: tuple[str | int, ...],
) -> None:
    """Each negative fixture must fail at its intended contract location."""
    validator = build_validator(contract_name)
    instance = load_json(FIXTURE_ROOT / fixture_relative_path)

    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))

    assert errors, f"Expected fixture to be rejected: {fixture_relative_path}"
    assert any(
        tuple(error.path) == expected_instance_path
        for error in errors
    ), (
        f"Expected validation error at {expected_instance_path}, "
        f"received {[tuple(error.path) for error in errors]}"
    )
