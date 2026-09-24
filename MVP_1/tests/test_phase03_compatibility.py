"""Phase 03 additive-boundary compatibility checks."""

from __future__ import annotations

import inspect
from pathlib import Path

import agentic_assessment.clause04_adapter as clause04_adapter
import agentic_assessment.clause04_workflow as clause04_workflow
import agentic_assessment.evidence_assessor as evidence_assessor
import agentic_assessment.evidence_integrity as evidence_integrity
import agentic_assessment.finding_generator as finding_generator
import agentic_assessment.human_review as human_review
import agentic_assessment.report_generator as report_generator
import agentic_assessment.supervisor as supervisor
from governance.policy_enforcer import PolicyDecisionType
from governance.startup_validator import initialize_governance


def test_clause04_execution_path_does_not_import_shared_kernel() -> None:
    modules = (
        clause04_adapter,
        clause04_workflow,
        evidence_assessor,
        evidence_integrity,
        finding_generator,
        human_review,
        report_generator,
        supervisor,
    )
    assert all("shared_kernel" not in inspect.getsource(module) for module in modules)


def test_shared_kernel_has_no_phase5_runtime_permission() -> None:
    governance_root = Path(__file__).resolve().parents[1] / "governance"
    runtime = initialize_governance(governance_root)
    decision = runtime.policy_enforcer.evaluate(
        component_id="agentic.shared_kernel",
        resource="AGENTIC_ASSESSMENT_WORKFLOW",
        action="EXECUTE_WORKFLOW_STEP",
    )
    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False
