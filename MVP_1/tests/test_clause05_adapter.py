import pytest

from agentic_assessment.clause05.adapter import build_evidence_mappings
from agentic_assessment.clause05.validation import Clause05ConfigError

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


def test_conditional_mapping_is_proposed_until_applicability_is_explicit():
    rows = build_evidence_mappings(
        assessment_id="ASM-C05-TEST",
        created_at="2026-09-29T00:00:00Z",
    )
    conditional = [row for row in rows if row["question_id"] == "Q-C05-5.2-006"]
    assert conditional
    assert all(row["mapping_status"] == "PROPOSED" for row in conditional)


def test_explicit_empty_configuration_does_not_fall_back_to_package_data():
    with pytest.raises(Clause05ConfigError):
        build_evidence_mappings(
            assessment_id="ASM-C05-TEST",
            created_at="2026-09-29T00:00:00Z",
            question_bank={},
        )
