"""Phase 03 deterministic file-integrity boundary tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentic_assessment.shared_kernel.lifecycle import verify_evidence_integrity
from tests._shared_kernel_fixtures import TIMESTAMP, manifest, mapping


def test_matching_file_hash_establishes_integrity(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence" / "control.txt"
    evidence.parent.mkdir()
    evidence.write_text("controlled evidence", encoding="utf-8")
    declared = hashlib.sha256(evidence.read_bytes()).hexdigest()
    record = verify_evidence_integrity(
        mapping=mapping(), manifest=manifest(evidence_items=[{
            "evidence_id": "EVD-CONTROL-001", "path": "evidence/control.txt",
            "media_type": "text/plain", "declared_sha256": declared,
        }]), evidence_root=tmp_path, recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST"
    )
    assert record.state == "INTEGRITY_VERIFIED"
    assert record.sha256 == declared


def test_present_file_without_declared_hash_stops_at_file_present(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence" / "control.txt"
    evidence.parent.mkdir()
    evidence.write_text("controlled evidence", encoding="utf-8")
    record = verify_evidence_integrity(
        mapping=mapping(), manifest=manifest(evidence_items=[{
            "evidence_id": "EVD-CONTROL-001", "path": "evidence/control.txt",
            "media_type": "text/plain",
        }]), evidence_root=tmp_path, recorded_at=TIMESTAMP,
        recorded_by="KERNEL.TEST"
    )
    assert record.state == "FILE_PRESENT"
    assert record.sha256 is None


def test_hash_mismatch_is_unable_to_establish(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence" / "control.txt"
    evidence.parent.mkdir()
    evidence.write_text("controlled evidence", encoding="utf-8")
    record = verify_evidence_integrity(
        mapping=mapping(), manifest=manifest(), evidence_root=tmp_path,
        recorded_at=TIMESTAMP, recorded_by="KERNEL.TEST"
    )
    assert record.state == "UNABLE_TO_ESTABLISH"


def test_missing_file_is_unable_to_establish(tmp_path: Path) -> None:
    record = verify_evidence_integrity(
        mapping=mapping(), manifest=manifest(), evidence_root=tmp_path,
        recorded_at=TIMESTAMP, recorded_by="KERNEL.TEST"
    )
    assert record.state == "UNABLE_TO_ESTABLISH"


def test_resolved_path_cannot_escape_evidence_root(tmp_path: Path) -> None:
    escaped = manifest(evidence_items=[{
        "evidence_id": "EVD-CONTROL-001", "path": "../outside-control.txt",
        "media_type": "text/plain",
    }])
    # The frozen schema rejects traversal before filesystem resolution.
    from agentic_assessment.shared_kernel.validation import SharedKernelError
    import pytest

    with pytest.raises(SharedKernelError, match="contract validation"):
        verify_evidence_integrity(
            mapping=mapping(), manifest=escaped, evidence_root=tmp_path,
            recorded_at=TIMESTAMP, recorded_by="KERNEL.TEST"
        )
