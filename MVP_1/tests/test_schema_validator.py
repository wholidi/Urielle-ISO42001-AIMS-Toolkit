"""Tests for deterministic governance schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from governance.schema_validator import (
    SchemaValidationError,
    SchemaValidator,
)


PILOT_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = PILOT_ROOT / "governance"


CONFIGURATION_FILES = {
    "agent_registry": "agent_registry.yaml",
    "permission_matrix": "permission_matrix.yaml",
    "human_approval_rules": "human_approval_rules.yaml",
    "model_use_record": "model_use_record.yaml",
}


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML object used by governance tests."""

    with path.open("r", encoding="utf-8-sig") as handle:
        data = yaml.safe_load(handle)

    assert isinstance(data, dict)
    return data


@pytest.mark.parametrize(
    "contract_name",
    sorted(CONFIGURATION_FILES),
)
def test_valid_governance_configuration_is_accepted(
    contract_name: str,
) -> None:
    """Current governance configuration must satisfy its schema."""

    validator = SchemaValidator()

    instance = load_yaml(
        GOVERNANCE_ROOT / CONFIGURATION_FILES[contract_name]
    )

    result = validator.validate(
        contract_name=contract_name,
        instance=instance,
    )

    assert result.valid is True
    assert result.contract_name == contract_name
    assert result.issues == ()


def test_invalid_instance_is_rejected() -> None:
    """Structurally invalid governance data must fail validation."""

    validator = SchemaValidator()

    result = validator.validate(
        contract_name="agent_registry",
        instance={"unexpected": True},
    )

    assert result.valid is False
    assert result.issues


def test_validation_issues_include_instance_paths() -> None:
    """Validation failures must expose deterministic evidence paths."""

    validator = SchemaValidator()

    instance = load_yaml(
        GOVERNANCE_ROOT / "agent_registry.yaml"
    )

    instance["components"][0]["enabled"] = "yes"

    result = validator.validate(
        contract_name="agent_registry",
        instance=instance,
    )

    assert result.valid is False

    assert any(
        issue.path == ("components", 0, "enabled")
        for issue in result.issues
    )


def test_require_valid_accepts_valid_instance() -> None:
    """Hard validation boundary must allow compliant input."""

    validator = SchemaValidator()

    instance = load_yaml(
        GOVERNANCE_ROOT / "model_use_record.yaml"
    )

    validator.require_valid(
        contract_name="model_use_record",
        instance=instance,
    )


def test_require_valid_raises_for_invalid_instance() -> None:
    """Hard validation boundary must fail closed."""

    validator = SchemaValidator()

    with pytest.raises(
        SchemaValidationError,
        match="Schema validation failed",
    ):
        validator.require_valid(
            contract_name="agent_registry",
            instance={"unexpected": True},
        )


def test_unknown_contract_fails_closed() -> None:
    """Unregistered schema contracts must never be accepted."""

    validator = SchemaValidator()

    with pytest.raises(
        SchemaValidationError,
        match="Unknown governance schema contract",
    ):
        validator.validate(
            contract_name="unknown_contract",
            instance={},
        )


@pytest.mark.parametrize(
    "contract_name",
    ["", "   "],
)
def test_missing_contract_name_fails_closed(
    contract_name: str,
) -> None:
    """Blank contract identifiers must be rejected."""

    validator = SchemaValidator()

    with pytest.raises(
        SchemaValidationError,
        match="Contract name is missing or invalid",
    ):
        validator.validate(
            contract_name=contract_name,
            instance={},
        )


def test_missing_schema_file_fails_closed(
    tmp_path: Path,
) -> None:
    """Missing schema files must prevent validation."""

    validator = SchemaValidator(schema_root=tmp_path)

    with pytest.raises(
        SchemaValidationError,
        match="Governance schema file is missing",
    ):
        validator.validate(
            contract_name="agent_registry",
            instance={},
        )


def test_malformed_schema_json_fails_closed(
    tmp_path: Path,
) -> None:
    """Malformed schema documents must prevent validation."""

    schema_path = tmp_path / "agent_registry.schema.json"
    schema_path.write_text(
        "{this-is-not-json",
        encoding="utf-8",
    )

    validator = SchemaValidator(schema_root=tmp_path)

    with pytest.raises(
        SchemaValidationError,
        match="Unable to parse governance schema",
    ):
        validator.validate(
            contract_name="agent_registry",
            instance={},
        )


def test_invalid_json_schema_fails_closed(
    tmp_path: Path,
) -> None:
    """A syntactically valid but invalid JSON Schema must be rejected."""

    schema_path = tmp_path / "agent_registry.schema.json"

    schema_path.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": 123,
            }
        ),
        encoding="utf-8",
    )

    validator = SchemaValidator(schema_root=tmp_path)

    with pytest.raises(
        SchemaValidationError,
        match="Invalid governance schema",
    ):
        validator.validate(
            contract_name="agent_registry",
            instance={},
        )


def test_repeated_validation_is_deterministic() -> None:
    """Identical inputs must produce identical validation results."""

    validator = SchemaValidator()

    instance = load_yaml(
        GOVERNANCE_ROOT / "permission_matrix.yaml"
    )

    first = validator.validate(
        contract_name="permission_matrix",
        instance=instance,
    )

    second = validator.validate(
        contract_name="permission_matrix",
        instance=instance,
    )

    assert first == second