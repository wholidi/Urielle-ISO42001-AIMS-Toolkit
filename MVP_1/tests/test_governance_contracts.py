"""Contract tests for deterministic Phase 2 governance configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker


MVP_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = MVP_ROOT / "governance"
SCHEMA_ROOT = GOVERNANCE_ROOT / "schemas"
FIXTURE_ROOT = MVP_ROOT / "tests" / "fixtures" / "governance"


CONFIG_SCHEMA_PAIRS = (
    (
        GOVERNANCE_ROOT / "agent_registry.yaml",
        SCHEMA_ROOT / "agent_registry.schema.json",
    ),
    (
        GOVERNANCE_ROOT / "permission_matrix.yaml",
        SCHEMA_ROOT / "permission_matrix.schema.json",
    ),
    (
        GOVERNANCE_ROOT / "human_approval_rules.yaml",
        SCHEMA_ROOT / "human_approval_rules.schema.json",
    ),
    (
        GOVERNANCE_ROOT / "model_use_record.yaml",
        SCHEMA_ROOT / "model_use_record.schema.json",
    ),
)


VALID_FIXTURE_SCHEMA_PAIRS = (
    (
        FIXTURE_ROOT / "valid" / "agent_registry.valid.yaml",
        SCHEMA_ROOT / "agent_registry.schema.json",
    ),
    (
        FIXTURE_ROOT / "valid" / "permission_matrix.valid.yaml",
        SCHEMA_ROOT / "permission_matrix.schema.json",
    ),
    (
        FIXTURE_ROOT / "valid" / "human_approval_rules.valid.yaml",
        SCHEMA_ROOT / "human_approval_rules.schema.json",
    ),
    (
        FIXTURE_ROOT / "valid" / "model_use_record.valid.yaml",
        SCHEMA_ROOT / "model_use_record.schema.json",
    ),
)


INVALID_FIXTURE_SCHEMA_PAIRS = (
    (
        FIXTURE_ROOT / "invalid" / "agent_registry.invalid.yaml",
        SCHEMA_ROOT / "agent_registry.schema.json",
    ),
    (
        FIXTURE_ROOT / "invalid" / "permission_matrix.invalid.yaml",
        SCHEMA_ROOT / "permission_matrix.schema.json",
    ),
    (
        FIXTURE_ROOT / "invalid" / "human_approval_rules.invalid.yaml",
        SCHEMA_ROOT / "human_approval_rules.schema.json",
    ),
    (
        FIXTURE_ROOT / "invalid" / "model_use_record.invalid.yaml",
        SCHEMA_ROOT / "model_use_record.schema.json",
    ),
)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = yaml.safe_load(handle)

    assert isinstance(data, dict)
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    assert isinstance(data, dict)
    return data


def validation_errors(
    instance_path: Path,
    schema_path: Path,
) -> list[Any]:
    instance = load_yaml(instance_path)
    schema = load_json(schema_path)

    Draft202012Validator.check_schema(schema)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    return sorted(
        validator.iter_errors(instance),
        key=lambda error: list(error.path),
    )


@pytest.mark.parametrize(
    ("config_path", "schema_path"),
    CONFIG_SCHEMA_PAIRS,
)
def test_governance_configuration_conforms_to_schema(
    config_path: Path,
    schema_path: Path,
) -> None:
    assert validation_errors(config_path, schema_path) == []


@pytest.mark.parametrize(
    ("fixture_path", "schema_path"),
    VALID_FIXTURE_SCHEMA_PAIRS,
)
def test_valid_governance_fixture_is_accepted(
    fixture_path: Path,
    schema_path: Path,
) -> None:
    assert validation_errors(fixture_path, schema_path) == []


@pytest.mark.parametrize(
    ("fixture_path", "schema_path"),
    INVALID_FIXTURE_SCHEMA_PAIRS,
)
def test_invalid_governance_fixture_is_rejected(
    fixture_path: Path,
    schema_path: Path,
) -> None:
    assert validation_errors(fixture_path, schema_path)


def test_registry_and_permission_matrix_component_ids_match() -> None:
    registry = load_yaml(GOVERNANCE_ROOT / "agent_registry.yaml")
    matrix = load_yaml(GOVERNANCE_ROOT / "permission_matrix.yaml")

    registered_ids = {
        component["component_id"]
        for component in registry["components"]
        if component["enabled"]
    }

    permission_ids = {
        permission["component_id"]
        for permission in matrix["permissions"]
    }

    assert permission_ids == registered_ids
    assert len(permission_ids) == len(matrix["permissions"])


def test_registered_prohibited_actions_are_denied() -> None:
    registry = load_yaml(GOVERNANCE_ROOT / "agent_registry.yaml")
    matrix = load_yaml(GOVERNANCE_ROOT / "permission_matrix.yaml")

    registry_by_id = {
        component["component_id"]: component
        for component in registry["components"]
    }

    for permission in matrix["permissions"]:
        component_id = permission["component_id"]
        component = registry_by_id[component_id]

        allowed = set(permission["allowed_actions"])
        denied = set(permission["denied_actions"])
        prohibited = set(component["prohibited_actions"])

        assert allowed.isdisjoint(denied)
        assert prohibited.issubset(denied)


def test_phase_2_governance_is_fail_closed() -> None:
    registry = load_yaml(GOVERNANCE_ROOT / "agent_registry.yaml")
    matrix = load_yaml(GOVERNANCE_ROOT / "permission_matrix.yaml")
    approvals = load_yaml(
        GOVERNANCE_ROOT / "human_approval_rules.yaml"
    )
    model_record = load_yaml(
        GOVERNANCE_ROOT / "model_use_record.yaml"
    )

    assert registry["default_execution_mode"] == "DETERMINISTIC_ONLY"

    assert matrix["default_decision"] == "DENY"
    assert matrix["deny_precedence"] is True
    assert matrix["unregistered_component_decision"] == "DENY"

    assert (
        approvals["default_decision"]
        == "REQUIRE_HUMAN_APPROVAL"
    )
    assert approvals["self_approval_prohibited"] is True
    assert approvals["approval_bypass_prohibited"] is True

    assert model_record["execution_mode"] == "DETERMINISTIC_ONLY"
    assert model_record["model_use_status"] == "NOT_IN_USE"
    assert model_record["external_model_calls_allowed"] is False
    assert model_record["generative_model_calls_allowed"] is False


def test_automated_approval_is_prohibited_for_every_rule() -> None:
    approvals = load_yaml(
        GOVERNANCE_ROOT / "human_approval_rules.yaml"
    )

    for rule in approvals["rules"]:
        assert rule["approval_required"] is True
        assert rule["minimum_approvals"] >= 1
        assert rule["reason_required"] is True
        assert rule["automated_approval_allowed"] is False


def test_forbidden_runtime_capabilities_are_recorded() -> None:
    model_record = load_yaml(
        GOVERNANCE_ROOT / "model_use_record.yaml"
    )

    prohibited = set(model_record["prohibited_capabilities"])

    assert {
        "EXTERNAL_MODEL_INVOCATION",
        "GENERATIVE_TEXT_CREATION",
        "AUTONOMOUS_FINDING_GENERATION",
        "AUTONOMOUS_HUMAN_APPROVAL",
        "SUPERVISOR_ORCHESTRATION",
        "REPORT_GENERATION",
    }.issubset(prohibited)
