"""Tests for deterministic governance configuration loading."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from governance.config_loader import (
    ConfigurationLoader,
    GovernanceConfigurationError,
)


MVP_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = MVP_ROOT / "governance"


def copy_governance_tree(destination: Path) -> Path:
    copied_root = destination / "governance"
    shutil.copytree(GOVERNANCE_ROOT, copied_root)
    return copied_root


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = yaml.safe_load(handle)

    assert isinstance(data, dict)
    return data


def write_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            sort_keys=False,
        )


def test_loader_accepts_production_governance_configuration() -> None:
    config = ConfigurationLoader(GOVERNANCE_ROOT).load()

    assert config.agent_registry["default_execution_mode"] == (
        "DETERMINISTIC_ONLY"
    )
    assert config.permission_matrix["default_decision"] == "DENY"
    assert config.human_approval_rules["self_approval_prohibited"] is True
    assert config.model_use_record["model_use_status"] == "NOT_IN_USE"


def test_loader_rejects_missing_configuration_file(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    (governance_root / "permission_matrix.yaml").unlink()

    with pytest.raises(
        GovernanceConfigurationError,
        match="configuration file is missing",
    ):
        ConfigurationLoader(governance_root).load()


def test_loader_rejects_schema_invalid_configuration(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    matrix_path = governance_root / "permission_matrix.yaml"

    matrix = load_yaml(matrix_path)
    matrix["default_decision"] = "ALLOW"
    write_yaml(matrix_path, matrix)

    with pytest.raises(
        GovernanceConfigurationError,
        match="failed schema validation",
    ):
        ConfigurationLoader(governance_root).load()


def test_loader_rejects_unregistered_permission_component(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    matrix_path = governance_root / "permission_matrix.yaml"

    matrix = load_yaml(matrix_path)
    matrix["permissions"][0]["component_id"] = "governance.unknown_component"
    write_yaml(matrix_path, matrix)

    with pytest.raises(
        GovernanceConfigurationError,
        match="components and permission entries do not match",
    ):
        ConfigurationLoader(governance_root).load()


def test_loader_rejects_allowed_and_denied_action_overlap(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    matrix_path = governance_root / "permission_matrix.yaml"

    matrix = load_yaml(matrix_path)
    permission = matrix["permissions"][0]

    permission["allowed_actions"].append(
        permission["denied_actions"][0]
    )
    write_yaml(matrix_path, matrix)

    with pytest.raises(
        GovernanceConfigurationError,
        match="both allowed and denied",
    ):
        ConfigurationLoader(governance_root).load()


def test_loader_rejects_model_use_enablement(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    record_path = governance_root / "model_use_record.yaml"

    record = load_yaml(record_path)
    record["external_model_calls_allowed"] = True
    write_yaml(record_path, record)

    with pytest.raises(
        GovernanceConfigurationError,
        match="failed schema validation",
    ):
        ConfigurationLoader(governance_root).load()
