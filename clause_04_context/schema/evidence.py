from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Dict, Any, List
import re


@dataclass
class EvidenceReference:
    reference_type: str
    reference_name: str
    extracted_from: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceRecord:
    session_id: str
    question_id: str
    clause: str
    title: str
    question: str
    expected_evidence: List[str]
    response: str
    response_source_type: str
    actual_evidence_references: List[Dict[str, Any]]
    confidence_score: float
    confidence_type: str
    auditor_note: str
    auditor_flag: bool
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def extract_evidence_references(response_text: str) -> List[Dict[str, Any]]:
    """
    Extract simple evidence references from the human response.

    This does not verify that the file exists.
    It only preserves cited evidence references for audit traceability.
    """

    references = []

    file_patterns = [
        r"\b[\w\-]+\.xlsx\b",
        r"\b[\w\-]+\.xls\b",
        r"\b[\w\-]+\.csv\b",
        r"\b[\w\-]+\.json\b",
        r"\b[\w\-]+\.md\b",
        r"\b[\w\-]+\.pdf\b",
        r"\b[\w\-]+\.docx\b",
    ]

    for pattern in file_patterns:
        matches = re.findall(pattern, response_text, flags=re.IGNORECASE)

        for match in matches:
            references.append(
                EvidenceReference(
                    reference_type="file_reference",
                    reference_name=match,
                    extracted_from="human_response",
                ).to_dict()
            )

    return references


def create_evidence_record(
    session_id: str,
    question: Dict[str, Any],
    response: Dict[str, Any],
    confidence_score: float,
    auditor_flag: bool,
) -> EvidenceRecord:
    response_text = response.get("response", "")

    return EvidenceRecord(
        session_id=session_id,
        question_id=question["question_id"],
        clause=question["clause"],
        title=question["title"],
        question=question["question"],
        expected_evidence=question.get("expected_evidence", []),
        response=response_text,
        response_source_type="human_file",
        actual_evidence_references=extract_evidence_references(response_text),
        confidence_score=confidence_score,
        confidence_type="rule_based_response_quality",
        auditor_note=response.get("auditor_note", ""),
        auditor_flag=auditor_flag,
        timestamp=datetime.now(UTC).isoformat(),
    )