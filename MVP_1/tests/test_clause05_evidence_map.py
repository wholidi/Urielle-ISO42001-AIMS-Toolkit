from agentic_assessment.clause05.config import load_evidence_map

def test_approval_mapping_is_explicit_and_question_specific():
    mappings = load_evidence_map()["mappings"]
    approval = {m["evidence_id"] for m in mappings if m["question_id"] == "Q-C05-5.2-003"}
    assert approval == {"S5-01", "S5-06"}

def test_reporting_schedule_does_not_claim_actual_reporting():
    mappings = load_evidence_map()["mappings"]
    reporting = [m for m in mappings if m["question_id"] == "Q-C05-5.3-006"]
    schedule = next(m for m in reporting if m["evidence_id"] == "S5-14")
    occurrence = next(m for m in reporting if m["evidence_id"] == "S5-05")
    role = next(m for m in reporting if m["evidence_id"] == "S5-11")
    assert {m["evidence_id"] for m in reporting} == {"S5-05", "S5-11", "S5-14"}
    assert "does not prove that reporting occurred" in schedule["claim_supported"]
    assert "explicitly accepted for this question" in occurrence["claim_supported"]
    assert "template presence alone does not prove" in occurrence["claim_supported"]
    assert "role title or register entry alone does not prove" in role["claim_supported"]
    assert all(m["combination_rule"] == "ALL_OF" for m in reporting)
