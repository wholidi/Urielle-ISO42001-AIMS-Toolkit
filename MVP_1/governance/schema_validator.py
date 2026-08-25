"""Deterministic, fail-closed JSON Schema validation for governance contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


class SchemaValidationError(RuntimeError):
    """Raised when schema validation cannot be performed safely."""


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic JSON Schema validation failure."""

    path: tuple[str | int, ...]
    message: str
    validator: str | None


@dataclass(frozen=True)
class SchemaValidationResult:
    """Immutable result of deterministic schema validation."""

    contract_name: str
    valid: bool
    issues: tuple[ValidationIssue, ...]


class SchemaValidator:
    """Validate governance objects against registered JSON Schemas.

    This component performs deterministic validation only.

    It does not:
    - modify governance configuration;
    - repair invalid documents;
    - make policy decisions;
    - approve human decisions;
    - generate assessment findings;
    - call external or generative models.
    """

    SCHEMA_FILES = {
        "agent_registry": "agent_registry.schema.json",
        "permission_matrix": "permission_matrix.schema.json",
        "human_approval_rules": "human_approval_rules.schema.json",
        "model_use_record": "model_use_record.schema.json",
    }

    def __init__(self, schema_root: Path | str | None = None) -> None:
        if schema_root is None:
            schema_root = Path(__file__).resolve().parent / "schemas"

        self.schema_root = Path(schema_root)

    def validate(
        self,
        *,
        contract_name: str,
        instance: Any,
    ) -> SchemaValidationResult:
        """Validate an instance and return an immutable result.

        Operational failures such as an unknown contract, missing schema,
        malformed JSON, or invalid schema raise SchemaValidationError.

        A well-formed schema with an invalid instance returns valid=False.
        """

        schema_path = self._resolve_schema_path(contract_name)
        schema = self._load_schema(schema_path)
        validator = self._build_validator(schema, schema_path)

        errors = sorted(
            validator.iter_errors(instance),
            key=self._error_sort_key,
        )

        issues = tuple(
            ValidationIssue(
                path=tuple(error.path),
                message=error.message,
                validator=error.validator,
            )
            for error in errors
        )

        return SchemaValidationResult(
            contract_name=contract_name,
            valid=not issues,
            issues=issues,
        )

    def require_valid(
        self,
        *,
        contract_name: str,
        instance: Any,
    ) -> None:
        """Validate an instance and fail closed when it is invalid."""

        result = self.validate(
            contract_name=contract_name,
            instance=instance,
        )

        if result.valid:
            return

        details = "; ".join(
            f"{list(issue.path)}: {issue.message}"
            for issue in result.issues
        )

        raise SchemaValidationError(
            f"Schema validation failed for {contract_name}: {details}"
        )

    def _resolve_schema_path(self, contract_name: str) -> Path:
        """Resolve only explicitly registered governance contracts."""

        if not isinstance(contract_name, str) or not contract_name.strip():
            raise SchemaValidationError(
                "Contract name is missing or invalid."
            )

        schema_name = self.SCHEMA_FILES.get(contract_name)

        if schema_name is None:
            raise SchemaValidationError(
                f"Unknown governance schema contract: {contract_name}"
            )

        return self.schema_root / schema_name

    @staticmethod
    def _load_schema(schema_path: Path) -> Mapping[str, Any]:
        """Load one JSON Schema and fail closed on malformed input."""

        if not schema_path.is_file():
            raise SchemaValidationError(
                f"Governance schema file is missing: {schema_path}"
            )

        try:
            with schema_path.open("r", encoding="utf-8-sig") as handle:
                schema = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise SchemaValidationError(
                f"Unable to parse governance schema: {schema_path}"
            ) from exc

        if not isinstance(schema, dict):
            raise SchemaValidationError(
                f"Governance schema must be an object: {schema_path}"
            )

        return schema

    @staticmethod
    def _build_validator(
        schema: Mapping[str, Any],
        schema_path: Path,
    ) -> Draft202012Validator:
        """Construct a validated Draft 2020-12 validator."""

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise SchemaValidationError(
                f"Invalid governance schema: {schema_path}"
            ) from exc

        return Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

    @staticmethod
    def _error_sort_key(error: Any) -> tuple[str, ...]:
        """Provide stable ordering across mixed string/integer paths."""

        return tuple(str(element) for element in error.path)