from agentic_assessment.clause05.config import load_evidence_map

def test_approval_mapping_is_explicit_and_question_specific():
    mappings = load_evidence_map()["mappings"]
    approval = {m["evidence_id"] for m in mappings if m["question_id"] == "Q-C05-5.2-003"}
    assert approval == {"S5-01", "S5-06"}

def test_reporting_schedule_does_not_claim_actual_reporting():
    mappings = load_evidence_map()["mappings"]
    reporting = [m for m in mappings if m["question_id"] == "Q-C05-5.3-006"]
    assert reporting
    assert all("requires separately submitted engagement evidence" in m["claim_supported"] for m in reporting)
