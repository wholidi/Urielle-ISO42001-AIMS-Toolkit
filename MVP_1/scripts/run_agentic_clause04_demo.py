from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from agentic_assessment.clause04_adapter import Clause04Adapter
from agentic_assessment.clause04_workflow import Clause04Workflow
from agentic_assessment.supervisor import (
    SequentialSupervisor,
    WORKFLOW_SEQUENCE,
)
from clause_04_context.run_clause04_demo import (
    run_clause04_assessment,
)
from governance.startup_validator import initialize_governance


PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUESTIONS_PATH = (
    PROJECT_ROOT
    / "clause_04_context"
    / "questions"
    / "C4.json"
)

RESPONSES_PATH = (
    PROJECT_ROOT
    / "clause_04_context"
    / "responses"
    / "human"
    / "C4_responses.json"
)


def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def production_clause04_executor(
    assessment_context: Mapping[str, Any],
) -> Mapping[str, Any]:
    questions = load_json(QUESTIONS_PATH)
    responses = load_json(RESPONSES_PATH)

    session_id = str(
        assessment_context.get(
            "session_id",
            "CLAUSE4-DEMO-001",
        )
    )

    return run_clause04_assessment(
        session_id=session_id,
        questions=questions,
        responses=responses,
    )


def main() -> None:
    assessment_id = "CLAUSE04-DEMO-001"
    run_id = "RUN-CLAUSE04-DEMO-001"

    adapter = Clause04Adapter(
        executor=production_clause04_executor,
    )

    workflow = Clause04Workflow(
        clause04_adapter=adapter,
    )

    governance = initialize_governance()

    supervisor = SequentialSupervisor(
        policy_enforcer=governance.policy_enforcer,
        handlers=workflow.handlers(),
    )

    assessment_context = {
        "assessment_id": assessment_id,
        "session_id": "CLAUSE4-DEMO-001",
    }

    result = supervisor.run(
        run_id=run_id,
        assessment_id=assessment_id,
        assessment_context=assessment_context,
        steps=WORKFLOW_SEQUENCE,
    )

    print()
    print("====================================")
    print("AGENTIC CLAUSE 04 DEMO")
    print("====================================")

    print(f"Run ID: {result.run_id}")
    print(f"State: {result.state.value}")

    print()
    print("Completed workflow steps:")

    for step in result.completed_steps:
        print(f"  - {step.value}")

    print()
    print("Execution events:")

    for event in result.events:
        print(
            f"  {event.event_id}"
            f" | {event.step}"
            f" | {event.action}"
            f" | {event.event_status}"
            f" | {event.workflow_state}"
        )

    print()

    if workflow.last_report is None:
        print("No report generated.")
        return

    report = workflow.last_report

    evidence_dir = (
        PROJECT_ROOT
        / "reports"
        / "evidence"
        / "agentic_clause04"
    )

    evidence_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        evidence_dir
        / f"{assessment_id}_{report.report_status}.md"
    )

    report_path.write_text(
        report.markdown,
        encoding="utf-8",
    )

    print(
        f"Report saved to: {report_path}"
    )

    events_path = (
        evidence_dir
        / f"{assessment_id}_execution_events.json"
    )

    events_payload = [
        event.to_contract()
        for event in result.events
    ]

    events_path.write_text(
        json.dumps(
            events_payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    acceptance_summary_path = (
        evidence_dir
        / f"{assessment_id}_acceptance_summary.json"
    )

    acceptance_summary_payload = {
        "assessment_id": assessment_id,
        "run_id": result.run_id,
        "workflow_state": result.state.value,
        "report_status": report.report_status,
        "readiness_score": report.readiness_score,
        "finding_count": report.finding_count,
        "pending_finding_count": report.pending_finding_count,
        "human_review_required": (
            report.pending_finding_count > 0
        ),
        "completed_steps": [
            step.value
            for step in result.completed_steps
        ],
    }

    acceptance_summary_path.write_text(
        json.dumps(
            acceptance_summary_payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Execution events saved to: {events_path}"
    )

    print(
        f"Acceptance summary saved to: "
        f"{acceptance_summary_path}"
    )

    print("Report summary:")
    print(
        f"  Status: {report.report_status}"
    )
    print(
        f"  Readiness score: "
        f"{report.readiness_score}"
    )

    print(
        f"  Findings: "
        f"{report.finding_count}"
    )
    print(
        f"  Pending findings: "
        f"{report.pending_finding_count}"
    )

    print()
    print("====================================")
    print("REPORT")
    print("====================================")
    print(report.markdown)


if __name__ == "__main__":
    main()
