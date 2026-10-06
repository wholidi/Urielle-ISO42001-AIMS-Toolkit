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
    with pytest.raises(Clause05ConfigError, match="resource-decision"):
        validate_clause05_configuration(load_question_bank(), em)
