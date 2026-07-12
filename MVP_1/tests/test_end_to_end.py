import json
from pathlib import Path

from clause_04_context import run_clause04_demo as demo

def test_main_generates_report_and_evidence_json(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    assert report_path.exists()
    assert evidence_path.exists()

    records = json.loads(evidence_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")

    assert [record["question_id"] for record in records] == [
        "C4-Q01",
        "C4-Q02",
        "C4-Q03",
        "C4-Q04",
    ]

    assert "# ISO/IEC 42001 Clause 4 Rule-based Readiness Report" in report
    assert "## Clause 4 Rule-based Readiness Score" in report
    assert "Expected Evidence:" in report
    assert "Actual Evidence References (extracted, not independently verified):" in report
    assert "This pilot does not verify that referenced files exist or validate their contents" in report
    assert "No structural, response-quality, or evidence-reference gaps detected" in report
 
def test_generated_json_records_have_required_traceability_fields(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    records = json.loads(evidence_path.read_text(encoding="utf-8"))

    required_fields = {
        "session_id",
        "question_id",
        "clause",
        "title",
        "question",
        "expected_evidence",
        "response",
        "response_source_type",
        "actual_evidence_references",
        "confidence_score",
        "confidence_type",
        "auditor_note",
        "auditor_flag",
        "timestamp",
    }

    for record in records:
        assert required_fields.issubset(record.keys())
        assert record["response_source_type"] == "human_file"
        assert record["confidence_type"] == "rule_based_response_quality"
        assert isinstance(record["expected_evidence"], list)
        assert isinstance(record["actual_evidence_references"], list)
        assert 0.0 <= record["confidence_score"] <= 1.0


def test_generated_json_can_be_parsed_after_repeated_runs(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()
    demo.main()

    records = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert len(records) == 4


def test_report_contains_each_clause_04_question(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    report = report_path.read_text(encoding="utf-8")

    assert "C4-Q01" in report
    assert "C4-Q02" in report
    assert "C4-Q03" in report
    assert "C4-Q04" in report

    assert "Clause: 4.1" in report
    assert "Clause: 4.2" in report
    assert "Clause: 4.3" in report
    assert "Clause: 4.4" in report


def test_output_paths_can_be_changed_to_temp_directory(tmp_path, monkeypatch):
    nested_output_dir = tmp_path / "custom" / "outputs"
    report_path = nested_output_dir / "report.md"
    evidence_path = nested_output_dir / "evidence.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    assert report_path.exists()
    assert evidence_path.exists()


def test_main_works_when_current_working_directory_differs(tmp_path, monkeypatch):
    report_path = tmp_path / "report.md"
    evidence_path = tmp_path / "evidence.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    original_cwd = Path.cwd()

    try:
        monkeypatch.chdir(tmp_path)
        demo.main()
    finally:
        monkeypatch.chdir(original_cwd)

    assert report_path.exists()
    assert evidence_path.exists()


def test_generate_markdown_report_handles_markdown_response_content(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    monkeypatch.setattr(demo, "REPORT_FILE", report_path)

    evidence_records = [
        {
            "question_id": "C4-Q01",
            "clause": "4.1",
            "title": "Context",
            "question": "Has context been identified?",
            "expected_evidence": ["context register"],
            "response": "## Evidence\n\n- Context register exists\n- Owner: AI Governance Lead",
            "response_source_type": "human_file",
            "actual_evidence_references": [],
            "confidence_score": 0.75,
            "confidence_type": "rule_based_response_quality",
            "auditor_note": "Markdown test.",
            "auditor_flag": False,
            "timestamp": "2026-07-08T00:00:00+00:00",
        }
    ]

    demo.generate_markdown_report(
        session_id="TEST-SESSION",
        evidence_records=evidence_records,
        gaps=[],
        readiness=75.0,
    )

    report = report_path.read_text(encoding="utf-8")

    assert "## Evidence" in report
    assert "Context register exists" in report
    assert "Rule-based Response Quality Score" in report

def test_report_contains_response_and_evidence_reference_for_each_record(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    report = report_path.read_text(encoding="utf-8")

    expected_references = [
        "Clause4_Context_Register.xlsx",
        "Clause4_Stakeholder_Register.xlsx",
        "Clause4_AIMS_Scope_Statement.xlsx",
        "Clause4_AIMS_Process_Map.xlsx",
    ]

    for reference in expected_references:
        assert reference in report

    assert report.count("Actual Evidence References (extracted, not independently verified):") == 4
    assert report.count("Response:") == 4
    assert "## Gaps" in report

def test_report_places_each_reference_under_correct_question_section(tmp_path, monkeypatch):
    report_path = tmp_path / "clause4_readiness_report.md"
    evidence_path = tmp_path / "clause4_evidence_records.json"

    monkeypatch.setattr(demo, "REPORT_FILE", report_path)
    monkeypatch.setattr(demo, "EVIDENCE_FILE", evidence_path)

    demo.main()

    report = report_path.read_text(encoding="utf-8")

    expected_pairs = [
        ("C4-Q01", "Clause4_Context_Register.xlsx"),
        ("C4-Q02", "Clause4_Stakeholder_Register.xlsx"),
        ("C4-Q03", "Clause4_AIMS_Scope_Statement.xlsx"),
        ("C4-Q04", "Clause4_AIMS_Process_Map.xlsx"),
    ]

    for question_id, reference in expected_pairs:
        section_start = report.index(f"### {question_id}")
        next_section_start = report.find("### C4-Q", section_start + 1)

        if next_section_start == -1:
            section = report[section_start:]
        else:
            section = report[section_start:next_section_start]

        assert reference in section