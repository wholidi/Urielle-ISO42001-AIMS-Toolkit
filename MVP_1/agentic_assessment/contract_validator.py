"""Runtime validation for Agentic Clause 04 data contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


class AssessmentContractError(RuntimeError):
    """Raised when an agentic-assessment contract cannot be validated safely."""


class AssessmentContractValidator:
    """Fail-closed validator for Agentic Clause 04 runtime contracts."""

    SCHEMA_FILES = {
        "execution_event": "execution_event.schema.json",
        "evidence_decision": "evidence_decision.schema.json",
    }

    def __init__(self, schema_root: Path | str | None = None) -> None:
        if schema_root is None:
            schema_root = Path(__file__).resolve().parent / "schemas"

        self.schema_root = Path(schema_root)

    def require_valid(
        self,
        *,
        contract_name: str,
        instance: Mapping[str, Any],
    ) -> None:
        """Require an instance to satisfy its registered contract."""

        schema_name = self.SCHEMA_FILES.get(contract_name)

        if schema_name is None:
            raise AssessmentContractError(
                f"Unknown agentic assessment contract: {contract_name}"
            )

        schema_path = self.schema_root / schema_name

        if not schema_path.is_file():
            raise AssessmentContractError(
                f"Assessment schema file is missing: {schema_path}"
            )

        try:
            with schema_path.open("r", encoding="utf-8") as handle:
                schema = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise AssessmentContractError(
                f"Unable to load assessment schema: {schema_path}"
            ) from exc

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise AssessmentContractError(
                f"Invalid assessment schema: {schema_path}"
            ) from exc

        validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

        errors = sorted(
            validator.iter_errors(instance),
            key=lambda error: tuple(str(item) for item in error.path),
        )

        if not errors:
            return

        details = "; ".join(
            f"{list(error.path)}: {error.message}"
            for error in errors
        )

        raise AssessmentContractError(
            f"{contract_name} failed schema validation: {details}"
        )