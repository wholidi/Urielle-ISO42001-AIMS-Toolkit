"""Acceptance tests for persistent Clause 04 portfolio scenarios."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_assessment.portfolio_scenarios import (
    PortfolioScenarioError,
    PortfolioScenarioRunner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = PROJECT_ROOT / "scenarios" / "clause04"
EXPECTED_ARTIFACTS = {
    "scenario_input.json",
    "evidence_decisions.json",
    "findings.json",
    "human_review_record.json",
    "execution_events.json",
    "acceptance_summary.json",
}


@pytest.mark.parametrize(
    ("scenario_id", "report_status", "finding_count", "pending_count"),
    (
        ("SCN-01-COMPLETE", "FINAL", 0, 0),
        ("SCN-02-INCOMPLETE", "DRAFT", 2, 2),
        ("SCN-03-REVIEWED", "FINAL", 3, 0),
    ),
)
def test_persistent_scenario_outcomes(
    tmp_path: Path,
    scenario_id: str,
    report_status: str,
    finding_count: int,
    pending_count: int,
) -> None:
    result = PortfolioScenarioRunner(output_root=tmp_path).run_file(
        SCENARIO_ROOT / f"{scenario_id}.json"
    )
    summary = json.loads(
        (result.output_dir / "acceptance_summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert result.workflow_state == "COMPLETED"
    assert result.report_status == report_status
    assert summary["scenario_id"] == scenario_id
    assert summary["assessment_id"] == scenario_id
    assert summary["finding_count"] == finding_count
    assert summary["pending_finding_count"] == pending_count
    assert (result.output_dir / f"report_{report_status}.md").is_file()
    assert EXPECTED_ARTIFACTS <= {
        path.name for path in result.artifact_paths
    }


def test_scenario_artifact_identifiers_match_scenario(tmp_path: Path) -> None:
    result = PortfolioScenarioRunner(output_root=tmp_path).run_file(
        SCENARIO_ROOT / "SCN-02-INCOMPLETE.json"
    )
    for name in ("evidence_decisions.json", "findings.json"):
        payload = json.loads((result.output_dir / name).read_text(encoding="utf-8"))
        assert payload
        assert all(item["assessment_id"] == result.scenario_id for item in payload)

    report = (result.output_dir / "report_DRAFT.md").read_text(encoding="utf-8")
    assert result.scenario_id in report


def test_pending_review_cannot_produce_final_report(tmp_path: Path) -> None:
    result = PortfolioScenarioRunner(output_root=tmp_path).run_file(
        SCENARIO_ROOT / "SCN-02-INCOMPLETE.json"
    )
    assert result.report_status == "DRAFT"
    assert not (result.output_dir / "report_FINAL.md").exists()


def test_reviewed_dispositions_are_preserved(tmp_path: Path) -> None:
    result = PortfolioScenarioRunner(output_root=tmp_path).run_file(
        SCENARIO_ROOT / "SCN-03-REVIEWED.json"
    )
    reviews = json.loads(
        (result.output_dir / "human_review_record.json").read_text(
            encoding="utf-8"
        )
    )
    dispositions = {
        item["review_record"]["disposition"] for item in reviews
    }
    assert dispositions == {"ACCEPTED", "MODIFIED", "REJECTED"}


def test_repeated_runs_are_byte_for_byte_deterministic(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    scenario_path = SCENARIO_ROOT / "SCN-03-REVIEWED.json"

    first = PortfolioScenarioRunner(output_root=first_root).run_file(scenario_path)
    second = PortfolioScenarioRunner(output_root=second_root).run_file(scenario_path)

    first_files = {
        path.name: path.read_bytes() for path in first.artifact_paths
    }
    second_files = {
        path.name: path.read_bytes() for path in second.artifact_paths
    }
    assert first_files == second_files


def test_invalid_scenario_configuration_fails_closed(tmp_path: Path) -> None:
    invalid_path = tmp_path / "SCN-INVALID.json"
    invalid_path.write_text(
        json.dumps({"schema_version": "1.0.0", "scenario_id": "SCN-INVALID"}),
        encoding="utf-8",
    )

    with pytest.raises(PortfolioScenarioError, match="missing required fields"):
        PortfolioScenarioRunner(output_root=tmp_path / "output").run_file(
            invalid_path
        )


def test_unknown_review_reference_fails_closed(tmp_path: Path) -> None:
    payload = json.loads(
        (SCENARIO_ROOT / "SCN-02-INCOMPLETE.json").read_text(encoding="utf-8")
    )
    payload["human_reviews"] = {
        "FND-UNKNOWN": {
            "reviewer_id": "portfolio-reviewer-001",
            "disposition": "ACCEPTED",
        }
    }
    invalid_path = tmp_path / "SCN-UNKNOWN-REVIEW.json"
    invalid_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PortfolioScenarioError, match="stopped before completion"):
        PortfolioScenarioRunner(output_root=tmp_path / "output").run_file(
            invalid_path
        )
