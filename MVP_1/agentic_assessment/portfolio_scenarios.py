"""Fail-closed execution and persistence for Clause 04 portfolio scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from agentic_assessment.clause04_adapter import Clause04Adapter
from agentic_assessment.clause04_workflow import Clause04Workflow
from agentic_assessment.finding_generator import FindingGenerator
from agentic_assessment.human_review import HumanReviewService
from agentic_assessment.report_generator import ReportGenerator
from agentic_assessment.supervisor import (
    SequentialSupervisor,
    SupervisorState,
    WORKFLOW_SEQUENCE,
)
from governance.startup_validator import initialize_governance


class PortfolioScenarioError(RuntimeError):
    """Raised when a portfolio scenario cannot be trusted or completed."""


@dataclass(frozen=True)
class PortfolioScenarioResult:
    """Persisted result for one governed portfolio scenario."""

    scenario_id: str
    output_dir: Path
    report_status: str
    workflow_state: str
    artifact_paths: tuple[Path, ...]


class PortfolioScenarioRunner:
    """Load, execute, verify, and persist deterministic scenarios."""

    REQUIRED_FIELDS = {
        "schema_version",
        "scenario_id",
        "title",
        "description",
        "run_id",
        "fixed_timestamp",
        "expected",
        "clause04_result",
        "human_reviews",
    }

    def __init__(self, *, output_root: Path | str) -> None:
        self.output_root = Path(output_root)

    def run_file(self, scenario_path: Path | str) -> PortfolioScenarioResult:
        path = Path(scenario_path)
        scenario = self._load_json(path)
        self._validate_scenario(scenario)

        scenario_id = str(scenario["scenario_id"])
        run_id = str(scenario["run_id"])
        fixed_time = datetime.fromisoformat(str(scenario["fixed_timestamp"]))
        clock = lambda: fixed_time
        raw_result = scenario["clause04_result"]

        def executor(_: Mapping[str, Any]) -> Mapping[str, Any]:
            return json.loads(json.dumps(raw_result))

        workflow = Clause04Workflow(
            clause04_adapter=Clause04Adapter(executor=executor),
            finding_generator=FindingGenerator(clock=clock),
            human_review_service=HumanReviewService(clock=clock),
            report_generator=ReportGenerator(clock=clock),
        )
        runtime = initialize_governance()
        supervisor = SequentialSupervisor(
            policy_enforcer=runtime.policy_enforcer,
            handlers=workflow.handlers(),
            clock=clock,
        )

        result = supervisor.run(
            run_id=run_id,
            assessment_id=scenario_id,
            assessment_context={
                "assessment_id": scenario_id,
                "human_reviews": scenario["human_reviews"],
            },
            steps=WORKFLOW_SEQUENCE,
        )

        if result.state is not SupervisorState.COMPLETED:
            final_event = result.events[-1] if result.events else None
            detail = final_event.error if final_event is not None else None
            raise PortfolioScenarioError(
                f"Scenario {scenario_id} stopped before completion: {detail}."
            )
        if workflow.last_report is None:
            raise PortfolioScenarioError(
                f"Scenario {scenario_id} produced no report."
            )

        report = workflow.last_report
        summary = {
            "schema_version": "1.0.0",
            "scenario_id": scenario_id,
            "assessment_id": report.assessment_id,
            "run_id": result.run_id,
            "workflow_state": result.state.value,
            "report_status": report.report_status,
            "readiness_score": report.readiness_score,
            "evidence_decision_count": report.evidence_decision_count,
            "finding_count": report.finding_count,
            "pending_finding_count": report.pending_finding_count,
            "accepted_finding_count": report.accepted_finding_count,
            "modified_finding_count": report.modified_finding_count,
            "rejected_finding_count": report.rejected_finding_count,
            "human_review_required": report.pending_finding_count > 0,
            "completed_steps": [step.value for step in result.completed_steps],
        }
        self._verify_expected(scenario["expected"], summary)

        output_dir = self.output_root / scenario_id
        output_dir.mkdir(parents=True, exist_ok=True)

        reviewed_findings = [
            finding.to_contract() for finding in workflow.last_findings
        ]
        review_records = [
            {
                "finding_id": finding["finding_id"],
                "review_record": finding["review_record"],
            }
            for finding in reviewed_findings
            if finding["review_record"] is not None
        ]

        artifacts = {
            "scenario_input.json": scenario,
            "evidence_decisions.json": [
                decision.to_contract()
                for decision in workflow.last_evidence_decisions
            ],
            "findings.json": reviewed_findings,
            "human_review_record.json": review_records,
            "execution_events.json": [
                event.to_contract() for event in result.events
            ],
            "acceptance_summary.json": summary,
        }

        paths: list[Path] = []
        for name, payload in artifacts.items():
            artifact_path = output_dir / name
            artifact_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            paths.append(artifact_path)

        report_path = output_dir / f"report_{report.report_status}.md"
        report_path.write_text(report.markdown + "\n", encoding="utf-8")
        paths.append(report_path)

        return PortfolioScenarioResult(
            scenario_id=scenario_id,
            output_dir=output_dir,
            report_status=report.report_status,
            workflow_state=result.state.value,
            artifact_paths=tuple(paths),
        )

    def run_directory(
        self,
        scenario_root: Path | str,
    ) -> tuple[PortfolioScenarioResult, ...]:
        root = Path(scenario_root)
        paths = sorted(root.glob("SCN-*.json"))
        if not paths:
            raise PortfolioScenarioError("No Clause 04 scenarios were found.")
        return tuple(self.run_file(path) for path in paths)

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PortfolioScenarioError(
                f"Scenario file is unreadable: {path.name}"
            ) from exc
        if not isinstance(payload, dict):
            raise PortfolioScenarioError("Scenario root must be an object.")
        return payload

    @classmethod
    def _validate_scenario(cls, scenario: Mapping[str, Any]) -> None:
        missing = cls.REQUIRED_FIELDS - set(scenario)
        if missing:
            raise PortfolioScenarioError(
                f"Scenario is missing required fields: {', '.join(sorted(missing))}."
            )
        scenario_id = scenario.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id.startswith("SCN-"):
            raise PortfolioScenarioError("scenario_id is invalid.")
        for field in ("title", "description", "run_id", "fixed_timestamp"):
            if not isinstance(scenario.get(field), str) or not scenario[field].strip():
                raise PortfolioScenarioError(f"{field} is invalid.")
        try:
            fixed_time = datetime.fromisoformat(str(scenario["fixed_timestamp"]))
        except ValueError as exc:
            raise PortfolioScenarioError("fixed_timestamp is invalid.") from exc
        if fixed_time.tzinfo is None:
            raise PortfolioScenarioError("fixed_timestamp must include a timezone.")
        if not isinstance(scenario.get("expected"), Mapping):
            raise PortfolioScenarioError("expected is invalid.")
        if not isinstance(scenario.get("clause04_result"), Mapping):
            raise PortfolioScenarioError("clause04_result is invalid.")
        if not isinstance(scenario.get("human_reviews"), Mapping):
            raise PortfolioScenarioError("human_reviews is invalid.")

    @staticmethod
    def _verify_expected(
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
    ) -> None:
        mismatches = {
            key: {"expected": value, "actual": actual.get(key)}
            for key, value in expected.items()
            if actual.get(key) != value
        }
        if mismatches:
            raise PortfolioScenarioError(
                "Scenario acceptance expectations failed: "
                + json.dumps(mismatches, sort_keys=True)
            )
