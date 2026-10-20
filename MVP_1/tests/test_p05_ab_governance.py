"""P05-A/B: ensure staged Clause 05 governance grants NO runtime authority."""

from __future__ import annotations

from governance.startup_validator import initialize_governance
from governance.policy_enforcer import PolicyDecisionType
from agentic_assessment.supervisor import WORKFLOW_SEQUENCE, WorkflowStep


def test_p05b_actor_is_registered_but_disabled():
    runtime = initialize_governance()
    matches = [c for c in runtime.configuration.agent_registry["components"]
               if c["component_id"] == "agentic.clause05_workflow"]
    assert len(matches) == 1
    assert matches[0]["enabled"] is False
    assert matches[0]["execution_mode"] == "DETERMINISTIC_ONLY"
    assert not any(p["component_id"] == "agentic.clause05_workflow"
                   for p in runtime.configuration.permission_matrix["permissions"])


def test_p05b_workflow_execution_is_denied():
    runtime = initialize_governance()
    for action in ("EXECUTE_CLAUSE_05_ASSESSMENT", "CALL_EXTERNAL_MODEL",
                   "APPROVE_HUMAN_DECISION", "ISSUE_CERTIFICATION_CONCLUSION"):
        result = runtime.policy_enforcer.evaluate(
            component_id="agentic.clause05_workflow",
            resource="CLAUSE_05_ASSESSMENT_WORKFLOW", action=action)
        assert result.decision is PolicyDecisionType.DENY


def test_p05a_clause04_sequence_not_modified():
    assert WORKFLOW_SEQUENCE == (
        WorkflowStep.ASSESSMENT_PLANNING, WorkflowStep.QUESTION_SELECTION,
        WorkflowStep.CLAUSE_04_EXECUTION, WorkflowStep.EVIDENCE_ASSESSMENT,
        WorkflowStep.FINDING_GENERATION, WorkflowStep.HUMAN_REVIEW_DECISION,
        WorkflowStep.REPORT_GENERATION,
    )
