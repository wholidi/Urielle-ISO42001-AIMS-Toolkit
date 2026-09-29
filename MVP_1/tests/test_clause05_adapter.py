from agentic_assessment.clause05.adapter import build_evidence_mappings

def test_adapter_builds_v2_mapping_shape_and_stable_order():
    rows = build_evidence_mappings(
        assessment_id="ASM-C05-TEST",
        created_at="2026-09-29T00:00:00Z",
    )
    assert rows
    assert all(row["schema_version"] == "2.0.0" for row in rows)
    assert all(row["question_id"].startswith("Q-C05-") for row in rows)
    assert all(row["evidence_id"].startswith("EVD-S5-") for row in rows)
    assert rows == sorted(rows, key=lambda r: (r["question_id"], r["evidence_id"], r["mapping_id"]))
