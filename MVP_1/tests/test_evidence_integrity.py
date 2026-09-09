"""Phase 4 evidence-integrity lifecycle tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from agentic_assessment.evidence_integrity import (
    EvidenceIntegrityError,
    EvidenceIntegrityVerifier,
)


STAMP = "2026-09-04T08:00:00+00:00"


def verify(tmp_path: Path, *, locator: str = "evidence.txt", declared: str | None = None,
           review=None):
    entry = {"locator": locator}
    if declared is not None:
        entry["declared_sha256"] = declared
    return EvidenceIntegrityVerifier().verify(
        sequence=1, assessment_id="SCN-TEST-001", question_id="C4-Q01",
        evidence_id="EV-001", evidence_root=tmp_path, manifest_entry=entry,
        review=review, timestamp=STAMP,
    )


def test_file_presence_without_hash_stops_at_file_present(tmp_path: Path) -> None:
    (tmp_path / "evidence.txt").write_text("evidence\n", encoding="utf-8")
    assert verify(tmp_path).evidence_status == "FILE_PRESENT"


def test_matching_hash_establishes_integrity(tmp_path: Path) -> None:
    payload = b"evidence\n"
    (tmp_path / "evidence.txt").write_bytes(payload)
    record = verify(tmp_path, declared=hashlib.sha256(payload).hexdigest())
    assert record.evidence_status == "INTEGRITY_VERIFIED"
    assert [item["status"] for item in record.status_history] == [
        "REFERENCED", "FILE_PRESENT", "INTEGRITY_VERIFIED"
    ]
    assert (tmp_path / "evidence.txt").read_bytes() == payload


def test_manifest_absence_is_unable_to_establish(tmp_path: Path) -> None:
    record = EvidenceIntegrityVerifier().verify(
        sequence=1, assessment_id="SCN-TEST-001", question_id="C4-Q01",
        evidence_id="EV-001", evidence_root=tmp_path, manifest_entry=None,
        review=None, timestamp=STAMP,
    )
    assert record.evidence_status == "UNABLE_TO_ESTABLISH"


def test_hash_mismatch_is_unable_to_establish(tmp_path: Path) -> None:
    (tmp_path / "evidence.txt").write_text("evidence\n", encoding="utf-8")
    assert verify(tmp_path, declared="0" * 64).evidence_status == "UNABLE_TO_ESTABLISH"


@pytest.mark.parametrize("locator", ("../escape.txt", "/absolute.txt"))
def test_unsafe_paths_are_rejected(tmp_path: Path, locator: str) -> None:
    assert verify(tmp_path, locator=locator).evidence_status == "UNABLE_TO_ESTABLISH"


def test_directory_is_not_evidence_file(tmp_path: Path) -> None:
    (tmp_path / "evidence.txt").mkdir()
    assert verify(tmp_path).evidence_status == "UNABLE_TO_ESTABLISH"


def test_human_acceptance_requires_verified_integrity(tmp_path: Path) -> None:
    (tmp_path / "evidence.txt").write_text("evidence\n", encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="prior integrity"):
        verify(tmp_path, review={"reviewer_id": "reviewer", "content_reviewed": True,
                                 "disposition": "ACCEPTED", "comments": "Accepted."})


def test_verified_content_can_be_human_accepted(tmp_path: Path) -> None:
    payload = b"evidence\n"
    (tmp_path / "evidence.txt").write_bytes(payload)
    record = verify(
        tmp_path, declared=hashlib.sha256(payload).hexdigest(),
        review={"reviewer_id": "reviewer", "content_reviewed": True,
                "disposition": "ACCEPTED", "comments": "Accepted."},
    )
    assert record.evidence_status == "ACCEPTED"
    assert record.status_history[-2]["status"] == "CONTENT_REVIEWED"


def test_rejection_requires_reason(tmp_path: Path) -> None:
    payload = b"evidence\n"
    (tmp_path / "evidence.txt").write_bytes(payload)
    with pytest.raises(EvidenceIntegrityError, match="requires comments"):
        verify(tmp_path, declared=hashlib.sha256(payload).hexdigest(),
               review={"reviewer_id": "reviewer", "content_reviewed": True,
                       "disposition": "REJECTED"})
