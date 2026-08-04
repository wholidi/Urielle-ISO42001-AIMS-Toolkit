"""Deterministic loading and schema validation for governance configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator, FormatChecker


class GovernanceConfigurationError(RuntimeError):
    """Raised when governance configuration cannot be loaded safely."""


@dataclass(frozen=True)
class GovernanceConfiguration:
    """Validated Phase 2 governance configuration."""

    agent_registry: Mapping[str, Any]
    permission_matrix: Mapping[str, Any]
    human_approval_rules: Mapping[str, Any]
    model_use_record: Mapping[str, Any]


class ConfigurationLoader:
    """Load and validate deterministic governance configuration."""

    CONFIGURATION_FILES = {
        "agent_registry": (
            "agent_registry.yaml",
            "agent_registry.schema.json",
        ),
        "permission_matrix": (
            "permission_matrix.yaml",
            "permission_matrix.schema.json",
        ),
        "human_approval_rules": (
            "human_approval_rules.yaml",
            "human_approval_rules.schema.json",
        ),
        "model_use_record": (
            "model_use_record.yaml",
            "model_use_record.schema.json",
        ),
    }

    def __init__(self, governance_root: Path | str | None = None) -> None:
        if governance_root is None:
            governance_root = Path(__file__).resolve().parent

        self.governance_root = Path(governance_root)
        self.schema_root = self.governance_root / "schemas"

    def load(self) -> GovernanceConfiguration:
        """Load all governance files and reject invalid configuration."""

        loaded: dict[str, Mapping[str, Any]] = {}

        for key, (config_name, schema_name) in self.CONFIGURATION_FILES.items():
            config_path = self.governance_root / config_name
            schema_path = self.schema_root / schema_name

            loaded[key] = self._load_and_validate(
                config_path=config_path,
                schema_path=schema_path,
            )

        self._validate_cross_configuration_consistency(loaded)

        return GovernanceConfiguration(
            agent_registry=loaded["agent_registry"],
            permission_matrix=loaded["permission_matrix"],
            human_approval_rules=loaded["human_approval_rules"],
            model_use_record=loaded["model_use_record"],
        )

    @staticmethod
    def _load_yaml(path: Path) -> Mapping[str, Any]:
        if not path.is_file():
            raise GovernanceConfigurationError(
                f"Governance configuration file is missing: {path}"
            )

        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                data = yaml.safe_load(handle)
        except (OSError, yaml.YAMLError) as exc:
            raise GovernanceConfigurationError(
                f"Unable to parse governance configuration: {path}"
            ) from exc

        if not isinstance(data, dict):
            raise GovernanceConfigurationError(
                f"Governance configuration must be an object: {path}"
            )

        return data

    @staticmethod
    def _load_schema(path: Path) -> Mapping[str, Any]:
        if not path.is_file():
            raise GovernanceConfigurationError(
                f"Governance schema file is missing: {path}"
            )

        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                schema = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise GovernanceConfigurationError(
                f"Unable to parse governance schema: {path}"
            ) from exc

        if not isinstance(schema, dict):
            raise GovernanceConfigurationError(
                f"Governance schema must be an object: {path}"
            )

        return schema

    def _load_and_validate(
        self,
        *,
        config_path: Path,
        schema_path: Path,
    ) -> Mapping[str, Any]:
        config = self._load_yaml(config_path)
        schema = self._load_schema(schema_path)

        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            raise GovernanceConfigurationError(
                f"Invalid governance schema: {schema_path}"
            ) from exc

        validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

        errors = sorted(
            validator.iter_errors(config),
            key=lambda error: list(error.path),
        )

        if errors:
            details = "; ".join(
                f"{list(error.path)}: {error.message}"
                for error in errors
            )

            raise GovernanceConfigurationError(
                f"Governance configuration failed schema validation "
                f"for {config_path}: {details}"
            )

        return config

    @staticmethod
    def _validate_cross_configuration_consistency(
        loaded: Mapping[str, Mapping[str, Any]],
    ) -> None:
        registry = loaded["agent_registry"]
        matrix = loaded["permission_matrix"]
        approvals = loaded["human_approval_rules"]
        model_record = loaded["model_use_record"]

        registered_ids = {
            component["component_id"]
            for component in registry["components"]
            if component["enabled"]
        }

        permission_ids = {
            permission["component_id"]
            for permission in matrix["permissions"]
        }

        if registered_ids != permission_ids:
            raise GovernanceConfigurationError(
                "Enabled registry components and permission entries do not match."
            )

        if len(permission_ids) != len(matrix["permissions"]):
            raise GovernanceConfigurationError(
                "Duplicate permission entries are prohibited."
            )

        registry_by_id = {
            component["component_id"]: component
            for component in registry["components"]
        }

        for permission in matrix["permissions"]:
            component = registry_by_id[permission["component_id"]]

            allowed = set(permission["allowed_actions"])
            denied = set(permission["denied_actions"])
            prohibited = set(component["prohibited_actions"])

            if not allowed.isdisjoint(denied):
                raise GovernanceConfigurationError(
                    f"Action is both allowed and denied for "
                    f"{permission['component_id']}."
                )

            if not prohibited.issubset(denied):
                raise GovernanceConfigurationError(
                    f"Registry-prohibited actions are not fully denied for "
                    f"{permission['component_id']}."
                )

        if registry["default_execution_mode"] != "DETERMINISTIC_ONLY":
            raise GovernanceConfigurationError(
                "Registry must use deterministic-only execution."
            )

        if matrix["default_decision"] != "DENY":
            raise GovernanceConfigurationError(
                "Permission matrix must default to DENY."
            )

        if matrix["deny_precedence"] is not True:
            raise GovernanceConfigurationError(
                "Permission matrix must enforce deny precedence."
            )

        if matrix["unregistered_component_decision"] != "DENY":
            raise GovernanceConfigurationError(
                "Unregistered components must be denied."
            )

        if approvals["self_approval_prohibited"] is not True:
            raise GovernanceConfigurationError(
                "Self-approval must remain prohibited."
            )

        if approvals["approval_bypass_prohibited"] is not True:
            raise GovernanceConfigurationError(
                "Approval bypass must remain prohibited."
            )

        if model_record["execution_mode"] != "DETERMINISTIC_ONLY":
            raise GovernanceConfigurationError(
                "Model-use record must remain deterministic-only."
            )

        if model_record["model_use_status"] != "NOT_IN_USE":
            raise GovernanceConfigurationError(
                "Model use must remain disabled."
            )

        if model_record["external_model_calls_allowed"] is not False:
            raise GovernanceConfigurationError(
                "External model calls must remain disabled."
            )

        if model_record["generative_model_calls_allowed"] is not False:
            raise GovernanceConfigurationError(
                "Generative model calls must remain disabled."
            )
