from pathlib import Path
from zipfile import ZipFile

from agentic_assessment.clause05.config import load_evidence_map


def test_resource_decision_mapping_is_explicit_and_question_specific():
    mappings = load_evidence_map()["mappings"]
    resource = [m for m in mappings if m["question_id"] == "Q-C05-5.1-004"]
    by_source = {mapping["evidence_id"]: mapping for mapping in resource}
    assert set(by_source) == {"S5-05", "S5-15"}
    assert by_source["S5-05"]["evidence_role"] == "CORROBORATING"
    assert by_source["S5-15"]["evidence_role"] == "PRIMARY"
    assert all(mapping["combination_rule"] == "ALL_OF" for mapping in resource)
    assert all(mapping["human_acceptance_required"] is True for mapping in resource)


def test_s5_15_is_an_explicitly_uncompleted_blank_template():
    template = (
        Path(__file__).parents[2]
        / "Evidence_Repository"
        / "Section_5"
        / "S5-15_AIMS_Resource_Allocation_Decision_Record_Template.docx"
    )
    with ZipFile(template) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    for marker in (
        "UNCOMPLETED BLANK TEMPLATE",
        "Record ID",
        "AIMS Scope",
        "Approving Leader",
        "Authority Basis",
        "Decision Date",
        "People",
        "Budget",
        "Tools / Infrastructure",
        "Allocation Scope",
        "Approval Reference",
        "Related Evidence",
    ):
        assert marker in document

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
