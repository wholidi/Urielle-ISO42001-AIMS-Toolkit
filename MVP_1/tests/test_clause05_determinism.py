from agentic_assessment.clause05.adapter import build_evidence_mappings

def test_mapping_identity_reproducible_for_identical_governed_inputs():
    kwargs = dict(assessment_id="ASM-C05-DET", created_at="2026-09-29T00:00:00Z")
    assert build_evidence_mappings(**kwargs) == build_evidence_mappings(**kwargs)
