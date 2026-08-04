"""Tests for fail-closed deterministic governance startup."""

from __future__ import annotations

import shutil
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from governance.policy_enforcer import PolicyDecisionType
from governance.startup_validator import (
    GovernanceStartupError,
    initialize_governance,
)


MVP_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = MVP_ROOT / "governance"


def copy_governance_tree(destination: Path) -> Path:
    copied_root = destination / "governance"
    shutil.copytree(
        GOVERNANCE_ROOT,
        copied_root,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
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


def test_production_governance_starts_ready() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    assert runtime.ready is True
    assert runtime.execution_mode == "DETERMINISTIC_ONLY"
    assert runtime.model_use_status == "NOT_IN_USE"

    assert (
        runtime.configuration.model_use_record["model_use_status"]
        == "NOT_IN_USE"
    )


def test_runtime_context_is_frozen() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    with pytest.raises(FrozenInstanceError):
        runtime.ready = False  # type: ignore[misc]


def test_startup_rejects_missing_configuration(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    (governance_root / "agent_registry.yaml").unlink()

    with pytest.raises(
        GovernanceStartupError,
        match="startup validation failed",
    ):
        initialize_governance(governance_root)


def test_startup_rejects_missing_schema(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    (
        governance_root
        / "schemas"
        / "permission_matrix.schema.json"
    ).unlink()

    with pytest.raises(
        GovernanceStartupError,
        match="startup validation failed",
    ):
        initialize_governance(governance_root)


def test_startup_rejects_model_enablement(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    record_path = governance_root / "model_use_record.yaml"

    record = load_yaml(record_path)
    record["external_model_calls_allowed"] = True
    write_yaml(record_path, record)

    with pytest.raises(
        GovernanceStartupError,
        match="startup validation failed",
    ):
        initialize_governance(governance_root)


def test_startup_rejects_registry_permission_mismatch(
    tmp_path: Path,
) -> None:
    governance_root = copy_governance_tree(tmp_path)
    matrix_path = governance_root / "permission_matrix.yaml"

    matrix = load_yaml(matrix_path)
    matrix["permissions"][0]["component_id"] = (
        "governance.unregistered_component"
    )
    write_yaml(matrix_path, matrix)

    with pytest.raises(
        GovernanceStartupError,
        match="startup validation failed",
    ):
        initialize_governance(governance_root)


def test_started_runtime_denies_unregistered_component() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    decision = runtime.policy_enforcer.evaluate(
        component_id="governance.unregistered_component",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False
