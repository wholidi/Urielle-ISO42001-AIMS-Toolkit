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
    assert "requires separately submitted engagement evidence" in schedule["claim_supported"]
    assert "actual reporting occurrence record" in occurrence["claim_supported"]
    assert all(m["combination_rule"] == "ALL_OF" for m in reporting)
