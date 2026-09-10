"""Phase 2 tests for clause-neutral v2 assessment contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from agentic_assessment.contract_validator import AssessmentContractValidator

MVP_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = MVP_ROOT / "agentic_assessment" / "schemas"
V2_ROOT = SCHEMA_ROOT / "v2"
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "agentic_assessment" / "v2"
CONTRACTS = ("assessment_plan", "evidence_manifest", "evidence_mapping", "evidence_lifecycle_record", "evidence_acceptance_record", "requirement_assessment", "finding", "execution_event", "report_state")
V1_SHA256 = {
    "assessment_plan.schema.json": "47c68b2b7dc73bfe52379d36152b51db351bdce214c198012df3f9cf46b17762",
    "evidence_decision.schema.json": "5d7a5f3187b3392dd6c7dbc45238db542015b7a0a275b5cc4518e2660583bd6a",
    "evidence_integrity_record.schema.json": "3c631478b8bb9d433dfb49b08d39f4b1aa331aa05339ee5ffdbee39938bbe6ae",
    "execution_event.schema.json": "d4811430a9d45b70e50840e4262b42634231d5cfb63fd5b2e59b01dabd668e53",
    "finding.schema.json": "6983dc325a70d8483716274b3c7522a04f7d09c6ae3da23d2ebc1d3051f0bc30",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator(contract: str) -> Draft202012Validator:
    return Draft202012Validator(load(V2_ROOT / f"{contract}.schema.json"), format_checker=FormatChecker())


@pytest.mark.parametrize("contract", CONTRACTS)
def test_v2_schema_is_closed_draft_2020_12(contract: str) -> None:
    schema = load(V2_ROOT / f"{contract}.schema.json")
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == "2.0.0"
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize("contract", CONTRACTS)
def test_valid_fixture_is_accepted(contract: str) -> None:
    instance = load(FIXTURE_ROOT / "valid" / f"{contract}.valid.json")
    assert list(validator(contract).iter_errors(instance)) == []
    AssessmentContractValidator().require_valid(contract_name=f"v2.{contract}", instance=instance)


@pytest.mark.parametrize("fixture", sorted((FIXTURE_ROOT / "invalid").glob("*.json")))
def test_invalid_fixture_fails_closed(fixture: Path) -> None:
    contract = fixture.name.split(".", 1)[0]
    assert list(validator(contract).iter_errors(load(fixture))), fixture.name


def test_authoritative_v1_schema_bytes_are_unchanged() -> None:
    actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in SCHEMA_ROOT.glob("*.schema.json")}
    assert actual == V1_SHA256


def test_acceptance_identity_is_question_and_mapping_specific() -> None:
    required = set(load(V2_ROOT / "evidence_acceptance_record.schema.json")["required"])
    assert {"assessment_id", "question_id", "mapping_id", "evidence_id", "lifecycle_id"} <= required


def test_finding_disposition_is_separate_from_evidence_acceptance() -> None:
    acceptance = load(V2_ROOT / "evidence_acceptance_record.schema.json")["properties"]
    finding = load(V2_ROOT / "finding.schema.json")["properties"]
    assert "disposition" not in acceptance
    assert "disposition" in finding
