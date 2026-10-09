from copy import deepcopy

import pytest

from agentic_assessment.clause05.config import load_evidence_map, load_question_bank
from agentic_assessment.clause05.validation import Clause05ConfigError, validate_clause05_configuration

def test_configuration_validates():
    validate_clause05_configuration(load_question_bank(), load_evidence_map())

def test_broken_question_reference_fails_closed():
    em = load_evidence_map()
    em["mappings"][0]["question_id"] = "Q-C05-5.1-999"
    with pytest.raises(Clause05ConfigError):
        validate_clause05_configuration(load_question_bank(), em)

def test_unknown_evidence_reference_fails_closed():
    em = load_evidence_map()
    em["mappings"][0]["evidence_id"] = "S5-99"
    with pytest.raises(Clause05ConfigError):
        validate_clause05_configuration(load_question_bank(), em)

def test_human_acceptance_cannot_be_disabled():
    em = load_evidence_map()
    em["mappings"][0]["human_acceptance_required"] = False
    with pytest.raises(Clause05ConfigError):
        validate_clause05_configuration(load_question_bank(), em)

def test_mixed_combination_rules_for_one_question_fail_closed():
    em = load_evidence_map()
    target = [m for m in em["mappings"] if m["question_id"] == "Q-C05-5.2-003"]
    target[0]["combination_rule"] = "ANY_OF"
    with pytest.raises(Clause05ConfigError):
        validate_clause05_configuration(load_question_bank(), em)

def test_conditional_question_must_use_conditional_rule():
    em = load_evidence_map()
    target = next(m for m in em["mappings"] if m["question_id"] == "Q-C05-5.2-006")
    target["combination_rule"] = "ANY_OF"
    with pytest.raises(Clause05ConfigError):
        validate_clause05_configuration(load_question_bank(), em)


def test_mapping_identity_must_match_question_identity():
    em = load_evidence_map()
    em["mappings"][0]["mapping_id"] = "C05MAP-5.2-001-A"
    with pytest.raises(Clause05ConfigError, match="Mapping identity"):
        validate_clause05_configuration(load_question_bank(), em)


def test_resource_decision_mapping_must_remain_corroborating():
    em = load_evidence_map()
    target = next(
        m for m in em["mappings"] if m["mapping_id"] == "C05MAP-5.1-004-A"
    )
    target["evidence_role"] = "PRIMARY"
    with pytest.raises(Clause05ConfigError, match="S5-05 corroboration"):
        validate_clause05_configuration(load_question_bank(), em)


def test_resource_decision_mapping_must_use_primary_s5_15():
    em = load_evidence_map()
    target = next(
        m for m in em["mappings"] if m["mapping_id"] == "C05MAP-5.1-004-B"
    )
    target["evidence_role"] = "CORROBORATING"
    with pytest.raises(Clause05ConfigError, match="primary S5-15"):
        validate_clause05_configuration(load_question_bank(), em)


@pytest.mark.parametrize(
    "mapping_id",
    ["C05MAP-5.1-004-A", "C05MAP-5.1-004-B"],
)
def test_every_resource_decision_mapping_is_required(mapping_id):
    em = load_evidence_map()
    em["mappings"] = [
        mapping for mapping in em["mappings"] if mapping["mapping_id"] != mapping_id
    ]
    with pytest.raises(Clause05ConfigError, match="Resource decisions require"):
        validate_clause05_configuration(load_question_bank(), em)


def test_artifact_catalog_cannot_omit_an_approved_source():
    em = load_evidence_map()
    em["artifact_catalog"].remove("S5-15")
    with pytest.raises(Clause05ConfigError, match="exactly match"):
        validate_clause05_configuration(load_question_bank(), em)


def test_artifact_catalog_cannot_add_an_invented_source():
    em = load_evidence_map()
    em["artifact_catalog"].append("S5-99")
    with pytest.raises(Clause05ConfigError, match="exactly match"):
        validate_clause05_configuration(load_question_bank(), em)


def test_approved_source_cannot_be_substituted_by_invented_source():
    em = deepcopy(load_evidence_map())
    em["artifact_catalog"] = [
        "S5-99" if source == "S5-15" else source
        for source in em["artifact_catalog"]
    ]
    for mapping in em["mappings"]:
        if mapping["evidence_id"] == "S5-15":
            mapping["evidence_id"] = "S5-99"
    with pytest.raises(Clause05ConfigError, match="exactly match"):
        validate_clause05_configuration(load_question_bank(), em)


@pytest.mark.parametrize(
    "mapping_id",
    ["C05MAP-5.3-006-A", "C05MAP-5.3-006-B", "C05MAP-5.3-006-C"],
)
def test_every_reporting_occurrence_mapping_is_required(mapping_id):
    em = load_evidence_map()
    em["mappings"] = [
        mapping
        for mapping in em["mappings"]
        if mapping["mapping_id"] != mapping_id
    ]
    with pytest.raises(Clause05ConfigError, match="reporting occurrence"):
        validate_clause05_configuration(load_question_bank(), em)


def test_reporting_occurrence_question_cannot_revert_to_schedule_wording():
    qb = load_question_bank()
    question = next(
        item for item in qb["questions"] if item["question_id"] == "Q-C05-5.3-006"
    )
    question["question_text"] = "Is the reporting route and cadence established?"
    with pytest.raises(Clause05ConfigError, match="occurrence-specific"):
        validate_clause05_configuration(qb, load_evidence_map())
