import json
from pathlib import Path
from datetime import datetime, UTC

from clause_04_context.validator.validator import score_response, requires_auditor_review
from clause_04_context.schema.evidence import create_evidence_record
from clause_04_context.fabric.gap_detector import detect_gaps, calculate_readiness
from clause_04_context.validator.input_validator import raise_if_invalid_inputs

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

QUESTIONS_FILE = BASE_DIR / "questions" / "C4.json"
RESPONSES_FILE = BASE_DIR / "responses" / "human" / "C4_responses.json"
REPORT_FILE = PROJECT_ROOT / "reports" / "clause4_readiness_report.md"
EVIDENCE_FILE = BASE_DIR / "evidence" / "clause4_evidence_records.json"

def save_evidence_records(evidence_records):
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = EVIDENCE_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(evidence_records, file, indent=2, ensure_ascii=False)

    temp_file.replace(EVIDENCE_FILE)
    
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in file: {path}\n"
            f"Line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"Required input file not found: {path}"
        ) from error


def match_response(question_id, responses):
    matching_responses = [
        response for response in responses
        if response.get("question_id") == question_id
    ]

    if len(matching_responses) > 1:
        raise ValueError(f"Duplicate responses found for question_id: {question_id}")

    if not matching_responses:
        return {
            "question_id": question_id,
            "response": "",
            "auditor_note": "No response found."
        }

    return matching_responses[0]

def generate_markdown_report(session_id, evidence_records, gaps, readiness):
    lines = []

    lines.append("# ISO/IEC 42001 Clause 4 Rule-based Readiness Report")
    lines.append("")
    lines.append(f"Session ID: `{session_id}`")
    lines.append(f"Generated: {datetime.now(UTC).isoformat()}")
    lines.append("")
    lines.append("## Clause 4 Rule-based Readiness Score")
    lines.append("")
    lines.append(f"**{readiness}%**")
    lines.append("")
    lines.append(
        "_This score is based on the loaded Clause 4 question set, "
        "rule-based response quality checks, and structural coverage checks. "
        "It is not a certification result or full audit assurance._"
    )
    lines.append("")
    lines.append("## Evidence Summary")
    lines.append("")

    for record in evidence_records:
        lines.append(f"### {record['question_id']} — {record['title']}")
        lines.append("")
        lines.append(f"- Clause: {record['clause']}")
        lines.append(f"- Rule-based Response Quality Score: {record['confidence_score']}")
        lines.append(f"- Auditor Review Required: {record['auditor_flag']}")
        lines.append(f"- Auditor Note: {record['auditor_note']}")
        lines.append("")

        lines.append("Expected Evidence:")
        for item in record.get("expected_evidence", []):
            lines.append(f"- {item}")

        lines.append("")
        lines.append("Actual Evidence References (extracted, not independently verified):")
        actual_refs = record.get("actual_evidence_references", [])

        if actual_refs:
            for ref in actual_refs:
                lines.append(
                    f"- {ref.get('reference_name')} ({ref.get('reference_type')})"
                )
        else:
            lines.append("- No structured evidence reference extracted.")

        lines.append("")
        lines.append("Response:")
        lines.append("")
        response_text = record.get("response", "")
        lines.append(f"> {response_text if response_text else 'No response provided.'}")
        lines.append("")

    lines.append("## Gaps")
    lines.append("")
    lines.append(
    "_Actual Evidence References are extracted from human responses. "
    "This pilot does not verify that referenced files exist or validate their contents._"
)
    lines.append("")

    if not gaps:
        lines.append(
            "No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope."
        )
    else:
        for gap in gaps:
            lines.append(
                f"- **{gap['question_id']} / Clause {gap['clause']}**: {gap['description']}"
            )

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = REPORT_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    temp_file.replace(REPORT_FILE)

def main():
    session_id = "CLAUSE4-DEMO-001"

    questions = load_json(QUESTIONS_FILE)
    responses = load_json(RESPONSES_FILE)

    raise_if_invalid_inputs(questions, responses)

    evidence_records = []

    for question in questions:
        response = match_response(question["question_id"], responses)
        score = score_response(response.get("response", ""), question["clause"])
        auditor_flag = requires_auditor_review(score)

        evidence_record = create_evidence_record(
            session_id=session_id,
            question=question,
            response=response,
            confidence_score=score,
            auditor_flag=auditor_flag
        )

        evidence_records.append(evidence_record.to_dict())

    gaps = detect_gaps(questions, responses, evidence_records)
    readiness = calculate_readiness(evidence_records, gaps)

    generate_markdown_report(session_id, evidence_records, gaps, readiness)
    save_evidence_records(evidence_records)

    print("Clause 4 demo completed.")
    print(f"Rule-based readiness score: {readiness}%")
    print(f"Report generated: {REPORT_FILE}")
    print(f"Evidence records generated: {EVIDENCE_FILE}")

    if gaps:
        print("")
        print("Gaps detected:")
        for gap in gaps:
            print(f"- {gap['gap_type']} | {gap['question_id']} | Clause {gap['clause']}: {gap['description']}")
    else:
        print("")
        print("No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope.")

if __name__ == "__main__":
    main()